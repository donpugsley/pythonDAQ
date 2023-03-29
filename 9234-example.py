import nidaqmx
from nidaqmx.constants import AcquisitionType
import matplotlib.pyplot as plt
import numpy as np

sample_time = 600  # units = seconds
s_freq = 200000
num_samples = sample_time*s_freq
dt = 1/s_freq
print('go acquisition !')
with nidaqmx.Task() as task:
    task.ai_channels.add_ai_accel_chan("PXI1Slot2_3/ai1:3",
                                       sensitivity=10000.0,
                                       max_val=1,
                                       min_val=-1)
    task.timing.cfg_samp_clk_timing(s_freq,
                                   sample_mode = AcquisitionType.CONTINUOUS)
    data = task.read(number_of_samples_per_channel=num_samples, timeout = nidaqmx.constants.WAIT_INFINITELY)
print('I do it right !')
