import sys
import pprint
import nidaqmx
from nidaqmx.constants import AcquisitionType
import numpy as np

pp = pprint.PrettyPrinter(indent=4)

# Get name of DAQ target device
if len(sys.argv) > 1:
    device = sys.argv[1]
else:
    device = "cDAQ1Mod1/ai2"
    print(f'Pass device/channel as string argument... using {device}')


with nidaqmx.Task() as task:
    task.ai_channels.add_ai_voltage_chan(device)

    task.timing.cfg_samp_clk_timing(1000, sample_mode=AcquisitionType.CONTINUOUS)

    samples = []

    def callback(task_handle, every_n_samples_event_type,
                 number_of_samples, callback_data):
        print('Every N Samples callback invoked.')

        samples.extend(task.read(number_of_samples_per_channel=1000))

        return 0

    task.register_every_n_samples_acquired_into_buffer_event(
        1000, callback)

    task.start()

    input('Running task. Press Enter to stop and see number of '
          'accumulated samples.\n')

    print(f'Acquired {len(samples)} points: DC {np.mean(samples):.3f} V, std {np.std(samples):.3f} V')
    
