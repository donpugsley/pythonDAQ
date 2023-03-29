import pyvisa
import time

KS = 'USB0::0x0957::0x1507::MY57002342::0::INSTR'

rm = pyvisa.ResourceManager()
instr = rm.open_resource(KS)

print(f'Back end is {rm}')

#print('Resources:') always empty??
#rm.list_resources()

instr.write('*CLS')

print('IDN (firmware): ', end="")
print(instr.query('*IDN?'))

# Query arbitrary waveform capability (0 = no, 002 = yes)
opts = instr.query('*OPT?')
print(f'Options: {opts}')

print('SCPI: ', end="")
print(instr.query('SYST:VERS?'))

# Basic tasks

# Reset
#instr.query('*RST')
#time.sleep(10)


# Get entire device state
#print(instr.query('*LRN?'))

# Save present settings
#print(instr.query('*SAV1'))  # slots 1..4, 0 is cleared on power cycle

# Recall saved settings...
#print(instr.query('*RCL1'))

# Output On/off
instr.write('OUTPUT OFF')

# Output a DC voltage
#instr.write('FUNC DC')
#instr.write('VOLT:OFFSET 1.0')

# Output a sine(freq,ampl,offset)
instr.write('APPL:SIN 5 KHZ, 3.0 VPP, -2.5 V')
#    or
#instr.write('FUNC SIN')
#instr.write('FREQ 1.0 Hz')
#instr.write('VOLT 1.0')
#instr.write('VOLT:OFFS 0.0')

instr.write('OUTPUT ON')
