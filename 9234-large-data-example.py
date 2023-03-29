import matplotlib.pyplot as plt
import numpy as np
import nidaqmx
from nidaqmx.stream_readers import AnalogMultiChannelReader
from nidaqmx import constants
import threading
from datetime import datetime
import os

# Parameters
sampling_freq_in = 200000  # in Hz
buffer_in_size = 800000
bufsize_callback = 200000
buffer_in_size_cfg = round(buffer_in_size) * 10  # clock configuration * 10 ?
chans_in = 32  # number of chan
refresh_rate_plot = 100000  # in Hz
crop = 0  # number of seconds to drop at acquisition start before saving

# Initialize data placeholders
buffer_in = np.zeros((chans_in, buffer_in_size))
data = np.zeros(
    (chans_in, 1))  # will contain a first column with zeros but that's fine
print(data.size)


# Definitions of basic functions
def ask_user():
    global running
    input("Press ENTER/RETURN to stop acquisition and coil drivers.")
    running = False


def cfg_read_task(acquisition):
    acquisition.ai_channels.ai_gain = 100
    acquisition.ai_channels.ai_max = 100
    acquisition.ai_channels.add_ai_accel_chan("Dev3/ai0:15",
                                              sensitivity=1000.0,
                                              max_val=1,
                                              min_val=-1)  # Cards1
    acquisition.ai_channels.add_ai_accel_chan("Dev4/ai0:15",
                                              sensitivity=1000.0,
                                              max_val=1,
                                              min_val=-1)  # Cards2
    acquisition.timing.cfg_samp_clk_timing(rate=sampling_freq_in,
                                           sample_mode=constants.AcquisitionType.CONTINUOUS,
                                           samps_per_chan=buffer_in_size_cfg)


def reading_task_callback(task_idx, event_type, num_samples, callback_data):
    global data
    global buffer_in
    if running:
        path = r'D:\Experience\caca\Acc/'
        isExist = os.path.exists(path)
        if not isExist:
            os.makedirs(path)
        buffer_in = np.zeros((chans_in, num_samples))  # double definition ???
        stream_in.read_many_sample(buffer_in, num_samples,
                                   timeout=constants.WAIT_INFINITELY)
        data = np.append(data, buffer_in,
                         axis=1)  # appends buffered data to total variable data
        filename = path + 'Acc_' + str(
            datetime.now().strftime("%m%d%h%H%M%S%f"))
        extension = '.npy'
        np.save(filename + extension, data)
        # f=np.fft.rfftfreq(data[4][1::].size,d=1/100000)
        # P=abs(np.fft.rfft(data[4][1::]))
        # plt.plot(f[f>200] ,P[f>200],'k')
        # plt.xlim(100,10000)
        # plt.plot(data[0][1::],'k--')
        data = np.zeros((chans_in, 1))
    return 0


# Configure and setup the tasks
task_in = nidaqmx.Task()
cfg_read_task(task_in)
stream_in = AnalogMultiChannelReader(task_in.in_stream)
task_in.register_every_n_samples_acquired_into_buffer_event(bufsize_callback,
                                                            reading_task_callback)

# Start threading to prompt user to stop
thread_user = threading.Thread(target=ask_user)
thread_user.start()

# Main loop
running = True
time_start = datetime.now()
task_in.start()

# Plot a visual feedback for the user's mental health

# f, (ax1, ax2, ax3) = plt.subplots(3, 1, sharex='all', sharey='none')
while running:  # make this adapt to number of channels automatically
    a = 0
    # ax1.clear()
    # ax2.clear()
    # ax3.clear()
    # ax1.plot(data[0, -sampling_freq_in * 5:].T,'r')  # 5 seconds rolling window
    # ax2.plot(data[1, -sampling_freq_in * 5:].T,'k')
    # ax3.plot(data[2, -sampling_freq_in * 5:].T,'b')
# Label and axis formatting
# ax3.set_xlabel('time [s]')
# ax1.set_ylabel('m/s**2')
# ax2.set_ylabel('m/s**2')
# ax3.set_ylabel('m/s**2')
# xticks = np.arange(0, data[0, -sampling_freq_in * 5:].size, sampling_freq_in)
# xticklabels = np.arange(0, xticks.size, 1)
# ax3.set_xticks(xticks)
# ax3.set_xticklabels(xticklabels)
# plt.pause(1/refresh_rate_plot)  # required for dynamic plot to work (if too low, nulling performance bad)
# Close task to clear connection once done
task_in.close()
duration = datetime.now() - time_start
print(duration, 'Pan t es mort')
experience_file = [duration, sampling_freq_in]
np.save('info.npy', experience_file)

# savefile:


# Some messages at the end
# print("\n")
# print("OPM acquisition ended.\n")
# print("Acquisition duration: {}.".format(duration))
