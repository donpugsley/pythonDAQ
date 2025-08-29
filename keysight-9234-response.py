# Keysight 33210A -> Crown DSI1000 -> Crowsonshaker - 356A01 accelerometer -> NI9234 card
import pyvisa 
import nidaqmx
from nidaqmx.constants import AcquisitionType
from nidaqmx import stream_readers
import numpy as np
import csv
import time
import pandas as pd
import plotters as p
import logging

# Set the logging level for the 'pyvisa' logger to WARNING or higher
# This will suppress INFO and DEBUG messages.
logging.getLogger('pyvisa').setLevel(logging.WARNING)

Keysight33210A = 'USB::0x0957::0x1507::MY57002342::0::INSTR' # works

GPERV = 200.0 # 5 mV/g... 
DAQ9234 = "cDAQ4Mod2"
DAQ9239 = "cDAQ4Mod1"
SR = 2*5120
SEC = 2

pyvisa.log_to_screen()

def KeysightInit():
    
    rm = pyvisa.ResourceManager('@py')
    print(f'Back end is {rm}')

    kd = rm.resource_info(Keysight33210A,True)

    ki = rm.open_resource(Keysight33210A)

    # ki.query('*CLS')

    # print('IDN (firmware): ', end="")
    # print(ki.query('*IDN?'))

    # Query arbitrary waveform capability (0 = no, 002 = yes)
    # opts = ki.query('*OPT?')
    # print(f'Options: {opts}')

    # print('SCPI: ', end="")
    # print(ki.query('SYST:VERS?'))
    # Get entire device state
    #print(instr.query('*LRN?'))
    return (ki)

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


ki = KeysightInit()
KeysightOutputOff(ki)
KeysightSine(ki,40) # 1V amplitude
KeysightOutputOn(ki)

sample_rate = SR  # Usually sample rate goes 2048 Hz, 2560 Hz, 3200 Hz, 5120 Hz, 6400 Hz (at least for a NI9234 card) 
samples_to_acq = SR   # At least for vibration matters, Samples to acq go from 2048, 4096, 8192
wait_time = samples_to_acq/sample_rate          # Data Acquisition Time in s, very important for the NI task function, and since we have 2048 on both sides, time is 1 s
smode = AcquisitionType.FINITE              # There is also FINITE for sporadic measurements
iterations = SEC

with nidaqmx.Task() as task:
    # Create accelerometer channel and configure sample clock. current_excit_val=0.002 enables IEPE, velocity measured in ips and accel in m/s2, 
    # both prox and tachometer can be used with a simple voltage channel.
    # For more info about channels: https://nidaqmx-python.readthedocs.io/en/latest/ai_channel_collection.html

    task = nidaqmx.Task()
    task.ai_channels.add_ai_accel_chan(physical_channel = DAQ9234 + "/ai0", sensitivity = 100, current_excit_val = 0.002)
    task.ai_channels.add_ai_accel_chan(physical_channel = DAQ9234 + "/ai1", sensitivity = 100, current_excit_val = 0.002)
    task.ai_channels.add_ai_accel_chan(physical_channel = DAQ9234 + "/ai2", sensitivity = 100, current_excit_val = 0.002)
    task.ai_channels.add_ai_accel_chan(physical_channel = DAQ9234 + "/ai3", sensitivity = 100, current_excit_val = 0.002)

    # voltage channels
    # task.ai_channels.add_ai_voltage_chan(physical_channel = DAQ9239 + "/ai0")
    # task.ai_channels.add_ai_voltage_chan(physical_channel = DAQ9239 + "/ai1")
    # task.ai_channels.add_ai_voltage_chan(physical_channel = DAQ9239 + "/ai2")
    # task.ai_channels.add_ai_voltage_chan(physical_channel = DAQ9239 + "/ai3")

    NCHANS = 4
    total_wait_time = wait_time * iterations                         # We will only take 10 measurements, 10 s for this example
    samples_to_acq_new = samples_to_acq * iterations                 # Also multiply by 10 to keep the same ratio, it should be 

    # Sets source of sample clock, its rate, and number of samples to aquire = buffer size
    task.timing.cfg_samp_clk_timing(sample_rate) # , sample_mode = smode, samps_per_chan = samples_to_acq_new)               

    start = time.time()
    data = np.ndarray((NCHANS, samples_to_acq_new), dtype = np.float64)  #Creates an array, 4 columns each one of 20480 rows    
    start = time.time()
    print ('Starting task...')         # Just to keep a control in your console

    # Saving the 4 channels to a csv file. This file is overwritten everytime the program is executed.
    # It should appear in the same folder that your program is located. 
    with open('data.csv', 'w', newline = '') as f:
        writer = csv.writer(f)
        writer.writerow(['Time','Ax','Ay','Az','Mic']) #,'Mx','My','Mz','NC'])
        t = np.linspace(0, total_wait_time, samples_to_acq_new)       # Your x axis (ms), starts from 0, final time is total_wait_time, equally divided by the number of samples you'll capture
        
        # data = np.ndarray((NCHANS, samples_to_acq_new), dtype = np.float64)  #Creates an array, 4 columns each one of 20480 rows
        stream_readers.AnalogMultiChannelReader(task.in_stream).read_many_sample(data, samples_to_acq_new, timeout = 4) 
        
        for value in range(len(t)):
            writer.writerow([t[value], data[0][value], data[1][value], data[2][value], data[3][value]])

    elapsed_time = (time.time() - start)
    print (f'done in {elapsed_time}')

df = pd.read_csv('data.csv')

# Plotly version - displays in browser
# fig = go.Figure()
# fig.add_trace(go.Scatter(x = df['Time'], y = df['Ax'], mode='lines', name='Ax'))
# fig.add_trace(go.Scatter(x = df['Time'], y = df['Ay'], mode='lines', name='Ay'))
# fig.add_trace(go.Scatter(x = df['Time'], y = df['Az'], mode='lines', name='Az'))
# fig.add_trace(go.Scatter(x = df['Time'], y = df['Mic'], mode='lines', name='Mic'))

p.threelsd(df['Ax']*GPERV,df['Ay']*GPERV,df['Az']*GPERV,SR,'g','9234 Accel','Ax','Ay','Az',6)

p.lsd(t,df['Mic'],SR,'g','')


