import nidaqmx
from nidaqmx.constants import AcquisitionType
import numpy as np
from matplotlib import pyplot as plt

# Instantiate variables
sample_rate = 25600
samples_to_acq = 51200
wait_time = samples_to_acq/sample_rate
channel_name = 'cDAQ1Mod2/ai2'
#trig_name = '/cDAQ2Mod1/PFI0'
cont_mode = AcquisitionType.CONTINUOUS
units_g = nidaqmx.constants.AccelUnits.G

with nidaqmx.Task() as task:
    
    # Create accelerometer channel and configure sample clock and trigger specs
    task.ai_channels.add_ai_accel_chan(channel_name, units = units_g)
    task.timing.cfg_samp_clk_timing(sample_rate, sample_mode = cont_mode, samps_per_chan=samples_to_acq)
#    task.triggers.start_trigger.cfg_dig_edge_start_trig(trigger_source = trig_name)
    
    for n in range (0, 7):
        
        # Reading data from sensor and generating time data with numpy
        ydata = task.read(number_of_samples_per_channel=samples_to_acq)
        xdata = np.linspace(0,wait_time,samples_to_acq)
        
        # Plotting data
        plt.clf() 
        plt.xlabel('Time (s)')
        plt.ylabel('Acceleration (g)')
        plt.axis([0, wait_time, -.5, .5])
        plt.plot(xdata, ydata)
        plt.pause(wait_time)




