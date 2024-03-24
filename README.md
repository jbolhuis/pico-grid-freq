# pico-grid-freq

Use a Raspberry Pi Pico and a precision external clock to measure the frequency of a 60Hz source - like the electrical grid frequency as delivered to your home.

How does it work, what do I need?

You need a way to tame the 120V AC power coming out of your wall into a 3.3V square wave suitable for the digital input of a Raspberry Pi Pico.  This typically involves a wall-wart type power supply with low voltage AC output fed into some sort of circuit featuring an op-amp or a schmitt trigger.  If you search for 'sine wave to square wave' you'll find a thousand circuit examples.

You also need a precision external clock.  This code assumes you have a precision clock module with a 32kHz square wave output.  Pre-built modules with the Maxim DS3232 are available to hobbyists for cheap.

How it works:

The Raspberry Pi Pico uses its PIO state machines to count the number of cycles of the precision clock during 120 cycles of the grid clock.  Math is done on the counters to determine the frequency of the grid clock.  This frequency number pops out on the local i2c display and also on the console.
