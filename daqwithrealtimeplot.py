# 20250806: Appears to be working at 20 kHz SR
# Todo - switch plots to Bokeh

import matplotlib.pyplot as plt
import numpy as np
import nidaqmx
from nidaqmx.stream_readers import AnalogMultiChannelReader
from nidaqmx import constants
import csv
import threading
import pickle
from datetime import datetime
import scipy.io

import plotters as p

# Parameters
SR = 20000  # in Hz
buffer_in_size = 2000
bufsize_callback = buffer_in_size
buffer_in_size_cfg = round(buffer_in_size * 1)  # clock configuration
chans_in = 4
refresh_rate_plot = 2  # in Hz
crop = 0  # number of seconds to drop at acquisition start before saving
DATAWINDOW = 0.5 # seconds

# Initialize data placeholders
buffer_in = np.zeros((chans_in, buffer_in_size))
data = np.zeros((chans_in, 1))  # will contain a first column with zeros but that's fine


# Definitions of basic functions
def ask_user():
    global running
    input("Press ENTER/RETURN to stop the task loop.")
    running = False


def cfg_read_task(acquisition):  # uses above parameters
    acquisition.ai_channels.add_ai_voltage_chan("cDAQ4Mod2/ai0:3")  # has to match with chans_in
    acquisition.timing.cfg_samp_clk_timing(rate=SR, sample_mode=constants.AcquisitionType.CONTINUOUS,
                                           samps_per_chan=buffer_in_size_cfg)


def reading_task_callback(task_idx, event_type, num_samples, callback_data):  # bufsize_callback is passed to num_samples
    global data
    global buffer_in

    if running:
        # It may be wiser to read slightly more than num_samples here, to make sure one does not miss any sample,
        # see: https://documentation.help/NI-DAQmx-Key-Concepts/contCAcqGen.html
        buffer_in = np.zeros((chans_in, num_samples))  # double definition ???
        stream_in.read_many_sample(buffer_in, num_samples, timeout=constants.WAIT_INFINITELY)

        data = np.append(data, buffer_in, axis=1)  # appends buffered data to total variable data

    return 0  # Absolutely needed for this callback to be well defined (see nidaqmx doc).


# Configure and setup the tasks
task_in = nidaqmx.Task()
cfg_read_task(task_in)
stream_in = AnalogMultiChannelReader(task_in.in_stream)
task_in.register_every_n_samples_acquired_into_buffer_event(bufsize_callback, reading_task_callback)


# Start threading to prompt user to stop
thread_user = threading.Thread(target=ask_user)
thread_user.start()


# Main loop
print ("Starting task...")
running = True
time_start = datetime.now()
task_in.start()


# Plot a visual feedback for the user's mental health
# f, (ax1, ax2, ax3) = plt.subplots(3, 1, sharex='all', sharey='none')
f, ax1 = plt.subplots()

while running:  # make this adapt to number of channels automatically
    ax1.clear()
    # ax2.clear()
    # ax3.clear()
    ax1.plot(data[0, -SR * 1:].T)  # 5 seconds rolling window
    # ax2.plot(data[1, -SR * 1:].T)
    # ax3.plot(data[2, -SR * 1:].T)
    # Label and axis formatting
    # ax3.set_xlabel('time [s]')
    # ax1.set_ylabel('voltage [V]')
    # ax2.set_ylabel('voltage [V]')
    # ax3.set_ylabel('voltage [V]')
    xticks = np.arange(0, data[0, -SR * 1:].size, SR)
    xticklabels = np.arange(0, xticks.size, 1)
    # ax3.set_xticks(xticks)
    # ax3.set_xticklabels(xticklabels)

    plt.pause(1/refresh_rate_plot)  # required for dynamic plot to work (if too low, nulling performance bad)


# Close task to clear connection once done
task_in.close()
duration = datetime.now() - time_start
print ("Task closed")

# Final save data and metadata ... first in python reloadable format:
# filename = my_filename
# with open(filename, 'wb') as f:
#     pickle.dump(data, f)
'''
Load this variable back with:
with open(name, 'rb') as f:
    data_reloaded = pickle.load(f)
'''
# Human-readable text file:
extension = '.txt'
#np.set_printoptions(threshold=np.inf, linewidth=np.inf)  # turn off summarization, line-wrapping
t = np.array([n for n in range(0,max(data.shape))])*(1.0/SR)

with open('data.csv', 'w', newline = '') as f:
    writer = csv.writer(f)
    writer.writerow(['Time','Ax','Ay','Az'])
    
    for i in range(len(t)):
        writer.writerow([t[i], data[0,i], data[1,i], data[2,i]])
# # MATLAB file:
# extension = '.mat'
# scipy.io.savemat(filename + extension, {'data':data})


# Some messages at the end
num_samples_acquired = data[0,:].size
print("\n")
print("OPM acquisition ended.\n")
print("Acquisition duration: {}.".format(duration))
print("Acquired samples: {}.".format(num_samples_acquired - 1))


# Final plot of whole time course the acquisition
plt.close('all')
f_tot, (ax1, ax2, ax3) = plt.subplots(3, 1, sharex='all', sharey='none')
ax1.plot(data[0, 10:].T)  # note the exclusion of the first 10 iterations (automatically zoomed in plot)
ax2.plot(data[1, 10:].T)
ax3.plot(data[2, 10:].T)
# Label formatting ...
ax3.set_xlabel('time [s]')
ax1.set_ylabel('voltage [V]')
ax2.set_ylabel('voltage [V]')
ax3.set_ylabel('voltage [V]')
xticks = np.arange(0, data[0, :].size, SR)
xticklabels = np.arange(0, xticks.size, 1)
ax3.set_xticks(xticks)
ax3.set_xticklabels(xticklabels)
plt.show()

