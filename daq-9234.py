import nidaqmx
import nidaqmx.constants
import numpy as np
from matplotlib import pyplot as plt

# Instantiate variables
sample_rate = 25600
samples_to_acq = int(51200)
wait_time = samples_to_acq/sample_rate
channel_name = 'cDAQ3Mod1/ai2'
#trig_name = '/cDAQ2Mod1/PFI0'
cont_mode = nidaqmx.constants.AcquisitionType.CONTINUOUS
units_g = nidaqmx.constants.AccelUnits.G

with nidaqmx.Task() as task:
    
    # Create accelerometer channel and configure sample clock and trigger specs
    task.ai_channels.add_ai_accel_chan(channel_name, units = units_g)
    task.timing.cfg_samp_clk_timing(sample_rate, sample_mode = cont_mode, samps_per_chan=samples_to_acq)
#    task.triggers.start_trigger.cfg_dig_edge_start_trig(trigger_source = trig_name)
    
    for n in range (0, 7):
        
        # Reading data from sensor and generating time data with numpy
        ydata = task.read()
        xdata = np.linspace(0,wait_time,samples_to_acq)
        
        # Plotting data
        plt.clf() 
        plt.xlabel('Time (s)')
        plt.ylabel('Acceleration (g)')
        plt.plot(xdata, np.array(ydata))
        plt.pause(wait_time)




