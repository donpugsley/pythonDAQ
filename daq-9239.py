import sys
import pprint
import nidaqmx
from nidaqmx.constants import Edge, AcquisitionType, UnitsPreScaled, VoltageUnits

import matplotlib.pyplot as plt
plt.ion

sys.path.append('~/Code/Python/library')
import plotters as p

pp = pprint.PrettyPrinter(indent=4)

# Get name of DAQ target device
# if len(sys.argv) > 1:
#     device = sys.argv[1]
# else:
#     device = "cDAQ2Mod1/ai0:3"

samplingrate = 50000.0

with nidaqmx.Task() as task: # Creates task object

    # Create the gain/offset scales we will need
    nidaqmx.Scale.create_lin_scale("BS-1000HF", 14705.88, 0, UnitsPreScaled.VOLTS, "pT")
    nidaqmx.Scale.create_lin_scale("Grad03-12-100K", 10000, 0, UnitsPreScaled.VOLTS, "nT")

    # Configure the channels we have connected
    task.ai_channels.add_ai_voltage_chan("cDAQ2Mod1/ai0","FuncGen")
    task.ai_channels.add_ai_voltage_chan("cDAQ2Mod1/ai1","Quasar",custom_scale_name="BS-1000HF",units=VoltageUnits.FROM_CUSTOM_SCALE)
    task.ai_channels.add_ai_voltage_chan("cDAQ2Mod1/ai2","Grad03",custom_scale_name="Grad03-12-100K",units=VoltageUnits.FROM_CUSTOM_SCALE)

    # 9239 has to have a sampling rate specified
    task.timing.cfg_samp_clk_timing(samplingrate, source='', active_edge=Edge.RISING, sample_mode=AcquisitionType.FINITE, samps_per_chan=50000)
    # print('1 Channel 1 Sample Read: ')
    # data = task.read()
    # pp.pprint(data)

    # Read one second from all four channels
    data = task.read(number_of_samples_per_channel=50000)
    task.close
    
N = len(data[0])
M = len(data)
print(f'Read {N} points for {M} channels')
t = []
t = [i/samplingrate for i in range(N)]

for c, channel in enumerate(data):
    p.oneplot(t,channel,'V',str(c))
    p.lsd(t,channel,samplingrate,'V',str(c))

input("Press Enter to continue...")
   
