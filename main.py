from machine import Pin, I2C
from ssd1306 import SSD1306_I2C
import rp2
from time import ticks_us, ticks_diff

# initialize local oled display
i2c=I2C(0,sda=Pin(0), scl=Pin(1), freq=400000)
oled = SSD1306_I2C(128, 64, i2c)


# Pin 11 is 60Hz signal to be measured
pin60Hz = Pin(11, Pin.IN, Pin.PULL_DOWN)
# Pin 12 is 32kHz "accurate clock" better than internal
pin32kHz = Pin(12, Pin.IN, Pin.PULL_DOWN)
# Pin 13 is a signal pin for the state machines to communicate
pinCom = Pin(13, Pin.OUT)

@rp2.asm_pio(set_init=rp2.PIO.OUT_LOW)
def count60():          # count cycles of the clock being measured
    wrap_target()
    pull()              # wait here until FIFO has data, move from TX FIFO to OSR
    mov(x,osr)          # move data (120) from OSR to X scratch
    label('loop')
    wait(0,pin,0)       # wait for low value on clock pin
    wait(1,pin,0)       # wait for high value on clock pin
    set(pins,1)         # set pinCom high to signal 32k counter to start
    jmp(x_dec,'loop')   # jump to 'loop' label if X nonzero, always decrement X
    set(pins,0)         # set pinCom low to signal 32k counter to stop
    irq(0)              # set irq 0 (no block), start handler()
    wrap()

@rp2.asm_pio()
def count32k():         # count cycles of the reference clock
    set(x,0)
    wrap_target()
    label('loop')
    wait(1,gpio,13)     # wait here forever until pinCom is high
    wait(0,pin,0)       # wait for low value on clock pin
    wait(1,pin,0)       # wait for high value on clock pin
    jmp(x_dec,'loop')   # jump to 'loop' label if X nonzero, always decrement X
    wrap()

def get32kcount():      # collect clock count while pinCom is low (counting stopped)
    sm32kHz.exec('mov(isr,x)')   # move X into ISR
    sm32kHz.exec('push()')       # push ISR into RX FIFO for pickup
    sm32kHz.exec('set(x,0)')     # reset the counter for next time
    x = sm32kHz.get()
    return (0x100000000 - x) & 0xffffffff   # return the number of clock counts

def handler(sm):
    td = get32kcount()
    freq = 1/(td/(120*32768))  # 120 cycles into freq (Hz)
    print(freq)   # print to console, host can insert value into influxDB or whatever
    oled.fill(0)  # also print to the tiny local display
    oled.text(str(freq), 30, 30)
    oled.show()
    sm32kHz.exec('set(x,0)')
    sm60Hz.put(120)  # measure 120 cycles (2 sec at 60Hz)

sm60Hz = rp2.StateMachine(0, count60, in_base=pin60Hz, set_base=pinCom)
sm60Hz.irq(handler)   # assumes irq0 because micropython only supports just this one?
sm32kHz = rp2.StateMachine(1, count32k, in_base=pin32kHz)

t = ticks_us()
td = 0
sm60Hz.active(1)  # activate state machine
sm32kHz.active(1) # activate state machine
sm60Hz.put(120)  # measure 120 cycles (2 sec at 60Hz)
