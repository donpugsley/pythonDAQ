# This works for a NI9234 card
import nidaqmx
from nidaqmx.constants import AcquisitionType
from nidaqmx import stream_readers
import numpy as np
import csv
import time
from datetime import datetime
import pandas as pd
import plotly.graph_objects as go
import plotters as p

sample_rate = 51200                              # Usually sample rate goes 2048 Hz, 2560 Hz, 3200 Hz, 5120 Hz, 6400 Hz (at least for a NI9234 card) 
samples_to_acq = 5120                           # At least for vibration matters, Samples to acq go from 2048, 4096, 8192
wait_time = samples_to_acq/sample_rate          # Data Acquisition Time in s, very important for the NI task function, and since we have 2048 on both sides, time is 1 s
cont_mode = AcquisitionType.CONTINUOUS              # There is also FINITE for sporadic measurements
iterations = 10
    
with nidaqmx.Task() as task:
    # Create accelerometer channel and configure sample clock. current_excit_val=0.002 enables IEPE, velocity measured in ips and accel in m/s2, 
    # both prox and tachometer can be used with a simple voltage channel.
    # For more info about channels: https://nidaqmx-python.readthedocs.io/en/latest/ai_channel_collection.html

    # accelerometer channels
    task.ai_channels.add_ai_accel_chan(physical_channel = "cDAQ3Mod1/ai0", sensitivity = 100, current_excit_val = 0.002)
    task.ai_channels.add_ai_accel_chan(physical_channel = "cDAQ3Mod1/ai1", sensitivity = 100, current_excit_val = 0.002)
    task.ai_channels.add_ai_accel_chan(physical_channel = "cDAQ3Mod1/ai2", sensitivity = 100, current_excit_val = 0.002)
    task.ai_channels.add_ai_accel_chan(physical_channel = "cDAQ3Mod1/ai3", sensitivity = 100, current_excit_val = 0.002)

    # voltage channels
    task.ai_channels.add_ai_voltage_chan(physical_channel = "cDAQ3Mod2/ai0")
    task.ai_channels.add_ai_voltage_chan(physical_channel = "cDAQ3Mod2/ai1")
    task.ai_channels.add_ai_voltage_chan(physical_channel = "cDAQ3Mod2/ai2")
    task.ai_channels.add_ai_voltage_chan(physical_channel = "cDAQ3Mod2/ai3")

    total_wait_time = wait_time * iterations                         # We will only take 10 measurements, 10 s for this example
    samples_to_acq_new = samples_to_acq * iterations                 # Also multiply by 10 to keep the same ratio, it should be 

    # Sets source of sample clock, its rate, and number of samples to aquire = buffer size
    task.timing.cfg_samp_clk_timing(sample_rate, sample_mode = cont_mode, samps_per_chan = samples_to_acq_new)               
    
    start = time.time()
    print ('Starting task...')         # Just to keep a control in your console

    # Saving the 4 channels to a csv file. This file is overwritten everytime the program is executed.
    # It should appear in the same folder that your program is located. 
    with open('data.csv', 'w', newline = '') as f:
        writer = csv.writer(f)
        writer.writerow(['Time','Ax','Ay','Az','Mic','Mx','My','Mz','NC'])
        t = np.linspace(0, total_wait_time, samples_to_acq_new)       # Your x axis (ms), starts from 0, final time is total_wait_time, equally divided by the number of samples you'll capture
        
        data = np.ndarray((8, samples_to_acq_new), dtype = np.float64)  #Creates an array, 4 columns each one of 20480 rows
        stream_readers.AnalogMultiChannelReader(task.in_stream).read_many_sample(data, samples_to_acq_new, timeout = 14) # it should't take that long for this example, check out time for other exercises               
        
        for value in range(len(t)):
            writer.writerow([t[value], data[0][value], data[1][value], data[2][value], data[3][value],data[4][value], data[5][value], data[6][value], data[7][value]])

    elapsed_time = (time.time() - start)
    print (f'done in {elapsed_time}')

df = pd.read_csv('data.csv')

# Plotly version - displays in browser
# fig = go.Figure()
# fig.add_trace(go.Scatter(x = df['Time'], y = df['Ax'], mode='lines', name='Ax'))
# fig.add_trace(go.Scatter(x = df['Time'], y = df['Ay'], mode='lines', name='Ay'))
# fig.add_trace(go.Scatter(x = df['Time'], y = df['Az'], mode='lines', name='Az'))
# fig.add_trace(go.Scatter(x = df['Time'], y = df['Mic'], mode='lines', name='Mic'))

p.threelsd(df['Ax'],df['Ay'],df['Az'],51200,'g','9234 Accel','Ax','Ay','Az',6)


