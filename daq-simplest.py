import sys
import pprint
import nidaqmx

pp = pprint.PrettyPrinter(indent=4)

# Get name of DAQ target device
if len(sys.argv) > 1:
    device = sys.argv[1]
else:
    device = "cDAQ3Mod1/ai0"
    print(f'Pass device/channel as string argument... using {device}')

with nidaqmx.Task() as task: # Creates task object
    task.ai_channels.add_ai_voltage_chan(device)

    print('1 Channel 1 Sample Read: ')
    data = task.read()
    pp.pprint(data)

    data = task.read(number_of_samples_per_channel=1)
    pp.pprint(data)

    print('1 Channel N Samples Read: ')
    data = task.read(number_of_samples_per_channel=8)
    pp.pprint(data)

   
