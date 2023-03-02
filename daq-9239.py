import sys
import pprint
import nidaqmx
from nidaqmx.constants import Edge
from nidaqmx.constants import AcquisitionType

pp = pprint.PrettyPrinter(indent=4)

# Get name of DAQ target device
# if len(sys.argv) > 1:
#     device = sys.argv[1]
# else:
#     device = "cDAQ1Mod3/ai0"
#     print(f'Pass device/channel as string argument... using {device}')

samplingrate = 2000.0

with nidaqmx.Task() as task: # Creates task object
    task.ai_channels.add_ai_voltage_chan("cDaq1Mod3/ai0")
    # 9239 has to have a sampling rate specified
    task.timing.cfg_samp_clk_timing(samplingrate, source='', active_edge=Edge.RISING, sample_mode=AcquisitionType.FINITE)
    
    print('1 Channel 1 Sample Read: ')
    data = task.read()
    pp.pprint(data)

    print('1 Channel N Samples Read: ')
    data = task.read(number_of_samples_per_channel=8)
    pp.pprint(data)

   
