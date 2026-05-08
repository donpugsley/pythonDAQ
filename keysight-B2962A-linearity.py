# Generate hysteresis/linearity patterns using a Keysight B2962A
import pyvisa 
from pyvisa import constants
import nidaqmx
from nidaqmx.constants import AcquisitionType
from nidaqmx import stream_readers
import numpy as np
import csv
import time
import pandas as pd
import plotters as p
import logging
from datetime import datetime
import argparse

# Set the logging level for the 'pyvisa' logger to WARNING or higher
# This will suppress INFO and DEBUG messages.
# logging.getLogger('pyvisa').setLevel(logging.WARNING)

def config_keysight(SN, CH, CONFIG):
    """
    Setup Keysight instrument.
    
    Inputs:
        SN (int): Serial number of Keysight (119 || 120)
        CH (int): Channel (1 || 2)
        CONFIG (dict): Dictionary containing settings for the 11 configuration parameters.
            Keys must match:
                'OFFMODE'       <ZERO | HIZ | NORM>
                'PROTECTION'    <ON | OFF>
                'REM'           <ON | OFF>              (ON = 4-wire/Kelvin, OFF = 2-wire)
                'HCAP'          <ON | OFF>              (High capacitance mode)
                'DFILT'         <ON | OFF>              (Digital output filter)
                'DFILT_FREQ'    (float)                 (3dB frequency of digital output filter)
                'EXT_FILT'      <ON | OFF>              (External filter module)
                'EXT_FILT_TYPE' <LNF | ULNF | HCULNF>   (External filter type)
                'OCOM'          <ON | OFF>              (Resistance compensation)
                'LIMIT'         (float)                 (Voltage or current safety limit)
                'OUTPUTMODE'    <VOLT | CURR>           (Channel output type)
    """
    
    # Breakout config array (Dictionary access)
    OFF_MODE = CONFIG['OFFMODE']
    PROTECTION = CONFIG['PROTECTION']
    REM = CONFIG['REM']
    HCAP = CONFIG['HCAP']
    D_FILT = CONFIG['DFILT']
    D_FILT_FREQ = CONFIG['DFILT_FREQ']
    EXT_FILT = CONFIG['EXT_FILT']
    EXT_FILT_TYPE = CONFIG['EXT_FILT_TYPE']
    OCOM = CONFIG['OCOM']
    LIMIT = CONFIG['LIMIT']
    OUTPUTMODE = CONFIG['OUTPUTMODE']
    
    # Determine protection mode based on output mode
    if OUTPUTMODE == "CURR":
        PROTECTMODE = "VOLT"
    elif OUTPUTMODE == "VOLT":
        PROTECTMODE = "CURR"
    else:
        raise ValueError("OUTPUTMODE must be 'VOLT' or 'CURR'")

    # Initialize instrument
    inst = initialize_COMMS(SN)
    
    # Configure channel
    init_channel(CH, OFF_MODE, PROTECTION, REM, HCAP, D_FILT, D_FILT_FREQ, 
                  EXT_FILT_TYPE, EXT_FILT, OCOM, inst)
    
    # Configure output
    initialize_output(CH, OUTPUTMODE, PROTECTION, PROTECTMODE, LIMIT, inst)
    
    return inst

def initialize_COMMS(SN):
    """
    Initialize communication with the Keysight instrument.
    """
    
    if SN not in visa_addr_map:
        raise ValueError(f"Serial Number {SN} not supported. Supported: {list(visa_addr_map.keys())}")
        
    VISAADDR = visa_addr_map[SN]
    
    rm = pyvisa.ResourceManager()
    
    # Check for existing resources (equivalent to instrfind)
    # Note: pyvisa handles closing/deleting in context managers, but we follow the logic
    existing_resources = rm.list_resources()
    # Filter for our specific device if multiple exist, or just close all found
    # The original script closes all found resources.
    # In a real scenario, you might want to be more specific, but this follows the original logic.
    # However, listing all and closing them might delete the device you want.
    # We will assume the device is not already open or we are re-initializing.
    
    # Attempt to open directly
    try:
        inst = rm.open_resource(VISAADDR)
        inst.open()
        return inst
    except pyvisa.VisaIOError as e:
        print(f"Failed to open resource {VISAADDR}: {e}")
        raise

def init_channel(CH, OFF_MODE, PROTECTION, REM, HCAP, D_FILT, D_FILT_FREQ, 
                  EXT_FILT_TYPE, EXT_FILT, OCOM, inst):
    """
    Configure hardware settings for the channel.
    """
    # Initialize instrument to 60Hz line frequency
    inst.write(':SYST:LFR 60')
    
    # Set output off mode
    outp_off_str = f':OUTP{CH}:OFF:MODE {OFF_MODE}'
    inst.write(outp_off_str)
    
    # Set protection enabled/disabled
    prot_str = f':OUTP{CH}:PROT {PROTECTION}'
    inst.write(prot_str)
    
    # Set REM (2-wire or 4-wire)
    # Original: OFF = 2-wire, ON = 4-wire
    rem_str = f':SENS{CH}:REM {REM}'
    inst.write(rem_str)
    
    # High capacitance mode
    hcap_str = f':OUTP{CH}:HCAP {HCAP}'
    inst.write(hcap_str)
    
    # Digital output filter
    dfilt_str = f':OUTP{CH}:FILT {D_FILT}'
    inst.write(dfilt_str)
    
    # Set filter frequency if enabled
    if D_FILT == "ON":
        dfilt_freq_str = f':OUTP{CH}:FILT:FREQ {D_FILT_FREQ}'
        inst.write(dfilt_freq_str)
    
    # Enable external output filter
    ext_filt_str = f':OUTP{CH}:FILT:EXT:STAT {EXT_FILT}'
    inst.write(ext_filt_str)
    
    # Select external output filter type if enabled
    if EXT_FILT == "ON":
        ext_filt_type_str = f':OUTP{CH}:FILT:EXT:TYPE {EXT_FILT_TYPE}'
        inst.write(ext_filt_type_str)
    
    # Enable resistance compensation
    ocom_str = f':SENS{CH}:RES:OCOM {OCOM}'
    inst.write(ocom_str)

def initialize_output(CH, OUTPUTMODE, PROTECTION, PROTECTMODE, LIMIT, inst):
    """
    Configure output settings for the channel.
    """
    # Note: Keysight usually sets :SOUR{ch}:VOLT:DC or :SOUR{ch}:CURR:DC via specific commands.
    # The original code used generic ':SOUR{ch}:{mode} 0'. 
    # Keysight SCPI often requires :SOUR{ch}:VOLT:DC or :SOUR{ch}:CURR:DC.
    # Assuming the SCPI command ':SOUR{ch}:{mode} 0' works or needs adjustment:
    
    # Set DC bias to zero (Adjusting for typical Keysight SCPI)
    # If the original command ':SOUR1:VOLT 0' worked, keep it. 
    # If it requires :SOUR1:VOLT:DC 0, uncomment below.
    # dc_bias_str = f':SOUR{CH}:{OUTPUTMODE} 0' 
    # inst.write(dc_bias_str)
    
    # Typical Keysight syntax for DC bias:
    if OUTPUTMODE == "VOLT":
        inst.write(f':SOUR{CH}:VOLT:DC 0')
    elif OUTPUTMODE == "CURR":
        inst.write(f':SOUR{CH}:CURR:DC 0')
        
    # Set protection mode if enabled
    if PROTECTION == "ON":
        CH_PROT_STR = f':SENS{CH}:{PROTECTMODE}:PROT {LIMIT}'
        inst.write(CH_PROT_STR)

def KeysightInit(KS):
    
    rm = pyvisa.ResourceManager('@py')
    # print(f'Back end is {rm}')
    # devices = rm.list_resources()
    # print(devices)

    # kd = rm.resource_info(KS,True)

    ki = rm.open_resource(KS)

    # ki.write_termination = '\n'
    # ki.read_termination = '\n'

    ki.write('*CLS')

    # print('IDN (firmware): ', end="")
    # print(ki.query('*IDN?'))

    # # Query arbitrary waveform capability (0 = no, 002 = yes)
    # opts = ki.query('*OPT?')
    # print(f'Options: {opts}')

    # #print('SCPI: ', end="")

    # print(ki.query('SYST:VERS?'))
    
    # # Get entire device state
    # print(instr.query('*LRN?'))
    return (ki)

def KeysightClear(ki):
    ki.write('*CLS')
    
def KeysightReset(ki):
    # Reset
    ki.query('*RST')
    time.sleep(10)

def KeysightSaveCfg(ki,n): # Save present settings to slot n
    print(ki.query(f'*SAV{n}'))  # slots 1..4, 0 is cleared on power cycle

def KeysightRecallCfg(ki,n): # # Recall saved settings from slot 0..4
    print(ki.query(f'*RCL{n}'))  # slots 1..4, 0 is cleared on power cycle
    
def KeysightOutputOff(ki): # Output On/off
    ki.write('OUTPUT OFF')

def KeysightOutputOn(ki): # Output On/off
    ki.write('OUTPUT ON')

def KeysightDC(ki,v): # Output DC voltage v
    ki.write('FUNC DC')
    ki.write(f'VOLT:OFFSET {v}')

def KeysightSine(ki,freq,vpp=2.0,offset=0.0): # # Recall saved settings from slot 0..4
    # Output a sine(freq,ampl,offset)
    ki.write(f'APPL:SIN {freq} HZ, {vpp} VPP, {offset} V')

    #ki.write('FUNC SIN')
    #ki.write('FREQ 1.0 Hz')
    #ki.write('VOLT 1.0')
    #ki.write('VOLT:OFFS 0.0')

def set_config(inst, channel, config_dict):
    for param, val in config_dict.items():
        command = f':SOUR{channel}:{param} {val}'
        print(command, end="")
        status=inst.write(command)
        print(" ... ", inst.query(':SYSTem:ERRor?'))

parser = argparse.ArgumentParser()
parser.add_argument("startval", nargs='?', default=-20, help="Starting output value")
parser.add_argument("stopval", nargs='?', default=20, help="Starting output value")
parser.add_argument("nsteps", nargs='?', default=11, help="Number of steps")
parser.add_argument("stepsecs", nargs='?', default=0.2, help="Seconds to wait at each step")
parser.add_argument("nreps", nargs='?', default=10, help="Number of up-and-back-down pattern repetitions")
args = parser.parse_args()

# --- Configuration ---
coil_const = 5000  # 5000 nT/mA for old solenoid
AMPS_LIMIT = 3.0  # Chooses range... 3 A/2V, 3A/20V
VOLTS_LIMIT = 20.0  # 
VC = 'CURR' # Constant Voltage or Constant Current mode

dt = float(args.stepsecs)  # duration of DC step (seconds)

# Generate output sequence - maybe should start at 0?  not yet
nT = np.linspace(int(args.startval), int(args.stopval), int(args.nsteps)) 
nT = np.concatenate([nT, np.flip(nT)])
if int(args.nreps) > 1:
    nT = np.tile(nT,int(args.nreps)-1)

amps = nT / coil_const

# --- 2. Build Waveform List ---
# Format: ':SOUR1:ARB:CURR:UDEF:LEV %s' (String list)
# MATLAB used %.12f, we replicate that precision
list_str = [f"{amp:.12f}" for amp in amps]

print(f"Opening and configuring Keysight B2962A...")

# We only have two possibilities... SN 119 and 120
try:
    inst = KeysightInit(f'USB0::0x0957::0x9018::SG52350119::0::INSTR')
except:
    inst = KeysightInit(f'USB0::0x0957::0x9018::SG52350120::0::INSTR')

KeysightClear(inst)
KeysightOutputOff(inst)

# Configure using config structure... needs code changes, not working now
# set_config(inst, 1, ch1_config) commands are wrong for this device???? ask George
# set_config(inst, 2, ch2_config) # Uncomment if you need CH2 configured

if VC.__contains__('VOLT'):
    print ('Using constant voltage mode.')
else:
    print ('Using constant current mode.')

inst.write(f':SOUR1:FUNC:MODE {VC}')
inst.write (':SOUR1:RANGE:AUTO ON')
inst.write(f':SOUR1:{VC} 0.0')
inst.write(f':SENS1:CURR:PROT:LEV:BOTH {AMPS_LIMIT}')
inst.write(f':SENS1:VOLT:PROT:LEV:BOTH {VOLTS_LIMIT}')
inst.write (':OUTP1 ON')

# input("Press Enter to start output...")

for val in list_str:
    command = f':SOUR1:{VC}:LEV:IMM:AMPL {val}'
    print(command)
    inst.write(command)
    time.sleep(dt)

print("Sequence complete.")
inst.write(':OUTP1 OFF')







# # Send Waveform
# inst.write(':SOUR1:FUNC:MODE {VC}')
# inst.write(':SOUR1:{VC}:MODE ARB')
# inst.write(':SOUR1:ARB:FUNC UDEF')

# print("Uploading output list to Keysight...")
# for val in list_str:
#     inst.write(f':SOUR1:ARB:{VC}:UDEF:LEV {val}')

# Set timing
# inst.write(f':SOUR1:ARB:{VC}:UDEF:TIME {dt}')
# inst.write(':SOUR1:ARB:COUN INF') # Run until interrupted

# input("Press Enter to start output...")
# inst.write(':OUTP1 ON')
# inst.write(':INIT:TRAN (@1)') # Note: Keysight syntax might vary, usually just ':INIT:TRAN'

# # Placeholder for DAQ
# # req_dur = (len_list * dt.*2)+(10*dt);
# # [Data,trigger_time]=FG_daqmx_recorder(2E3,req_dur);

# input("Waveform output is on now, press Enter to stop...")

# Implement your DAQ logic here (e.g., using pyvisa to read or calling an external function)
# Example placeholder:
# import time
# time.sleep(req_dur) 
# Data = np.zeros(req_dur)


inst.write(':OUTP1 OFF')
inst.close()

print(f"Completed at {datetime.now()}")