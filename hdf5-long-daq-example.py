import nidaqmx
import datetime
import time
import numpy as np
import h5py

def hdf5_write_parameter(h5_file, parameter, group_name='parameter'):
    # add parameter group
    param_grp = h5_file.create_group(group_name)
    # write single item
    for key, item in parameter.items():
        try:
            if item is None:
                item = 'None'
            if isinstance(item, dict):
                # recursive write each dictionary
                hdf5_write_parameter(h5_file, item, group_name+'/'+key)
            else:
                h5_file.create_dataset("/"+group_name+"/{}".format(key), data=item)
        except:
            print("[hdf5_write_parameter]: failed to write:", key, "=", item)
    return


run_bool = True # should be controlled by GUI or caller thread
measurement_duration = 1 # in seconds
filename = 'test_acquisition'
hdf5_write = True # a hdf5 file with ending '.h5' is created, False = numpy array

# check if device is available
system = nidaqmx.system.System.local()
system.driver_version
for device in system.devices:
        print(device) # plot devices
        
ADC_DEVICE_NAME = device.name # 'PCI6024e'
print('ADC: init measure for', measurement_duration, 'seconds')



# Setup ADC
parameter = { 
    "channels": 8,  # number of AI channels
    "channel_name": ADC_DEVICE_NAME + '/ai0:7',
    "log_rate": int(20000),  # Samples per second
    "adc_min_value": -5.0,  # minimum ADC value in Volts
    "adc_max_value": 5.0,  # maximum ADC value in Volts
    "timeout": measurement_duration + 2.0,  # timeout to detect external clock on read
    "debug_output": 1,
    "measurement_duration": measurement_duration,
    }

parameter["buffer_size"] = int(parameter["log_rate"])  # buffer size in samples
                           # must be bigger than loop duration!
parameter["requested_samples"] = parameter["log_rate"] * measurement_duration

parameter["hdf5_write"] = hdf5_write  # write in array
if parameter['hdf5_write']:
    filename += '.h5'
    f = h5py.File(filename, 'w') # create a h5-file object if True
    data = f.create_dataset('data', (0, parameter["channels"]), 
                                 maxshape=(None, parameter["channels"]), chunks=True)
else:
    filename += '.csv'
    # pre-allocate array, we might get up to 1 buffer more than requested...
    data = np.empty((parameter["requested_samples"]+parameter["buffer_size"], parameter["channels"]), dtype=np.float64)
    data[:] = np.nan


with nidaqmx.Task() as task:
    task.ai_channels.add_ai_voltage_chan(parameter["channel_name"],
                                         terminal_config=nidaqmx.constants.TerminalConfiguration.RSE,
                                         min_val=parameter["adc_min_value"],
                                         max_val=parameter["adc_max_value"],
                                         units=nidaqmx.constants.VoltageUnits.VOLTS
                                         )

    task.timing.cfg_samp_clk_timing(rate=parameter["log_rate"],
                                    sample_mode=nidaqmx.constants.AcquisitionType.CONTINUOUS)

    # helper variables
    total_samples = 0
    i = 0
    last_display = -1

    parameter["acquisition_start"] = str(datetime.datetime.now())
    if 1:
        print("ADC:   ---   acquisition started:", parameter["acquisition_start"])
        print("ADC: Requested samples:", parameter["requested_samples"], "Acquisition duration:",
                      measurement_duration)


    task.control(nidaqmx.constants.TaskMode.TASK_COMMIT)
    time_adc_start = time.perf_counter()
    # ############################# READING LOOP ##########################
    while run_bool and total_samples < parameter["requested_samples"] and time.perf_counter() - time_adc_start < parameter[
        "timeout"]:
        i = i + 1

        if parameter["debug_output"] >= 1:
            elapsed_time = np.floor(time.perf_counter() - time_adc_start)  # in sec
            if elapsed_time != last_display:
                print("ADC: ...", round(elapsed_time), "of", measurement_duration, "sec:",
                              total_samples, "acquired ...")
                last_display = elapsed_time

    
        # high-lvl read function: always create a new array
        data_buff = np.asarray(
            task.read(number_of_samples_per_channel=nidaqmx.constants.READ_ALL_AVAILABLE)).T
        time_adc_end = time.perf_counter()

        samples_from_buffer = data_buff.shape[0]

        # get nr of samples and acumulate to total_samples
        total_samples = int(total_samples + samples_from_buffer)
        if parameter["debug_output"] >= 2:
            print("ADC: iter", i, "total:", total_samples, "smp from buffer", samples_from_buffer,
                          "time elapsed", time.perf_counter() - time_adc_start)
        if samples_from_buffer > 0:
            
            # prepair buffer and hdf5 dataset
            if parameter["hdf5_write"]:  # sequential write to hdf5 file
                chunk_start = data.shape[0]
                # resize dataset in file
                data.resize(data.shape[0] + samples_from_buffer, axis=0)
            else:
                # prepair buffer to fit in pre-allocated array 'data'
                chunk_start = int(np.count_nonzero(~np.isnan(data)) / parameter["channels"])
                if parameter['channels'] == 1:
                    data_buff = data_buff[:, np.newaxis]
            
            if parameter["debug_output"] >= 3:
                    print("Non-empty data shape: (", data.shape,
                                  "), buffer shape:", data_buff.shape,
                                  "chunk start:", chunk_start)
                    
            # write buffer to HDF5 file or into numpy array
            data[chunk_start:chunk_start + samples_from_buffer, :] = data_buff
    # ############################# READING LOOP #########################
    parameter["acquisition_stop"] = str(datetime.datetime.now())


if parameter["debug_output"] >= 1:
    print("ADC: requested points:   ", parameter["requested_samples"])
    print("ADC: total aqcuired points", total_samples, "in", time_adc_end - time_adc_start)
    print("ADC: data array shape:", data.shape)
    print("ADC:  ---   aqcuisition finished:", parameter["acquisition_stop"])
    print("ADC: sample rate:", round(1/((time_adc_end-time_adc_start)/parameter["requested_samples"])))

# prepare data nparray for return
if not parameter["hdf5_write"]:
    # shrink numpy array by all nan's (from oversize with buffer size)
    total_written = int(np.count_nonzero(~np.isnan(data)) / parameter["channels"])
    if parameter["debug_output"] >= 2:
        print("resize data array by cutting", data.shape[0] - total_written, "tailing NaN's")
    data = np.resize(data, (total_written, parameter["channels"]))

# add more parameter to wrtie into the hdf5 file
parameter["total_samples"] = total_samples
parameter["total_acquisition_time"] = time_adc_end - time_adc_start
parameter["data_shape"] = data.shape
if parameter['hdf5_write']:
    hdf5_write_parameter(f, parameter) # write parameter
    f.close()
