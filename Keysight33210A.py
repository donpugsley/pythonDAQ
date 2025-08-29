import pyvisa
import time

KS = 'USB::0x0957::0x1507::MY57002342::0::INSTR'

def open(device):
    rm = pyvisa.ResourceManager()
    instr = rm.open_resource(KS)
    print(f'Opened {device}, back end is {rm}')
    print('IDN (firmware): ', end="")

    
    print(instr.query('*IDN?'))
    instr.write('*CLS')
    return instr


# Query arbitrary waveform capability (0 = no, 002 = yes)
# opts = instr.query('*OPT?')
# print(f'Options: {opts}')

# print('SCPI: ', end="")
# print(instr.query('SYST:VERS?'))

# Basic tasks

# Reset
def reset(instr):
    instr.query('*RST')
    time.sleep(10)


# Get entire device state
#print(instr.query('*LRN?'))

# Save present settings
def savesettings(instr):
    instr.write('*SAV1')  # slots 1..4, 0 is cleared on power cycle

# Recall saved settings...
def recallsettings(instr):
    instr.write('*RCL1')

# Output On/off
def outputoff(instr):
    instr.write('OUTPUT OFF')

# Output a DC voltage
#instr.write('FUNC DC')
#instr.write('VOLT:OFFSET 1.0')

# Output a sine(freq,ampl,offset)
def sine(instr,hz,pkpk,offset):
    instr.write(f'APPL:SIN {hz} HZ, {pkpk} VPP, {offset} V')

#    or
#instr.write('FUNC SIN')
#instr.write('FREQ 1.0 Hz')
#instr.write('VOLT 1.0')
#instr.write('VOLT:OFFS 0.0')

def outputon(instr):
    instr.write('OUTPUT ON')
