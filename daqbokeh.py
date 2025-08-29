# 20250814: Works! Bokeh plotting version, use bokeh serve --show daqbokeh.py to start
#
# Uses two separate callback systems... an NI-DAQ callback reads new data, and a Bokeh callback updates the plots
#
# TODO - needs a clean exit with NI task closure

import numpy as np
import nidaqmx
from nidaqmx.stream_readers import AnalogMultiChannelReader
from nidaqmx import constants
from datetime import datetime
from bokeh.plotting import figure, curdoc
from bokeh.models import ColumnDataSource
from bokeh.layouts import row, column, grid
from scipy.fft import fft
from scipy.signal import periodogram, welch
from waterfall import WaterfallRenderer

# DEBUG flag
DEBUG = False

# Parameters
SR = 50000  # in Hz... 51200 DID NOT WORK AS EXPECTED
WINDOWSEC = 2 # Seconds of data in plot window
BOKEHBUFFERSIZE = int(SR*WINDOWSEC) # 
UPDATEMILLISEC = 500 # plot update timer

buffer_in_size = 2500 # 20 daq callbacks per second
bufsize_callback = buffer_in_size # After this many samples are acquired, trigger callback function
buffer_in_size_cfg = round(buffer_in_size * 1)  # clock configuration samples per channel

chans_in = 3
CHANNELSTOREAD = "cDAQ4Mod2/ai0:2"
crop = 0  # number of seconds to drop at acquisition start before saving
DATAWINDOW = 0.5 # seconds

# Initialize data placeholders
buffer_in = np.zeros((chans_in, buffer_in_size))
# data = np.zeros((chans_in, 1))  # will contain a first column with zeros but that's fine

Dx = np.empty(shape=[0]) # linspace(0,0,1) # Create the data arrays that will be plotted
Dy = np.empty(shape=[0]) # linspace(0,0,1)
Dz = np.empty(shape=[0]) # linspace(0,0,1)
Dt = np.empty(shape=[0]) # linspace(0,0,1)

# Definitions of basic functions
def ask_user():
    global running
    input("Press ENTER/RETURN to stop the task loop.")
    running = False


def cfg_read_task(acquisition):  # uses above parameters
    acquisition.ai_channels.add_ai_voltage_chan(CHANNELSTOREAD)  # has to match with chans_in
    acquisition.timing.cfg_samp_clk_timing(rate=SR, sample_mode=constants.AcquisitionType.CONTINUOUS,
                                           samps_per_chan=buffer_in_size_cfg)


def reading_task_callback(task_idx, event_type, num_samples, callback_data):  # bufsize_callback is passed to num_samples
    global buffer_in, Dt,Dx,Dy,Dz, BOKEHBUFFERSIZE, signal_source,spectrum_source, running
    
    if running:
        # It may be wiser to read slightly more than num_samples here, to make sure one does not miss any sample,
        # see: https://documentation.help/NI-DAQmx-Key-Concepts/contCAcqGen.html
        buffer_in = np.zeros((chans_in, num_samples))  # double definition ???
        stream_in.read_many_sample(buffer_in, num_samples, timeout=constants.WAIT_INFINITELY)

        # data = np.append(data, buffer_in, axis=1)  # appends buffered data to total variable data
        # vmx,vmy,vmz,ax,ay,az,gx,gy,gz,bar,temp = getVMRdata(dev,DATASIZE)
        
        # # attach to VS Code debugger if this script was run with BOKEH_VS_DEBUG=true
        # # (place this just before the code you're interested in)
        # if os.environ['BOKEH_VS_DEBUG'] == 'true':
        #     # 5678 is the default attach port in the VS Code debug configurations
        #     print('Waiting for debugger attach')
        #     ptvsd.enable_attach(address=('localhost', 5678), redirect_output=True)
        #     ptvsd.wait_for_attach()

        Dx = np.append(Dx, np.array(buffer_in[0,:]))              
        Dy = np.append(Dy, np.array(buffer_in[1,:]))              
        Dz = np.append(Dz, np.array(buffer_in[2,:])) 
        Dt = np.arange(len(Dx))/SR # Assumes no dropped points
        
        if len(Dx) > BOKEHBUFFERSIZE: # If we have filled the data buffer, keep only the end
            Dx = Dx[-BOKEHBUFFERSIZE:]
            Dy = Dy[-BOKEHBUFFERSIZE:]
            Dz = Dz[-BOKEHBUFFERSIZE:]
            Dt = Dt[-BOKEHBUFFERSIZE:]

        # DEBUG
        # print(f"mx({len(vmx)}, my({len(vmy)}), mz({len(vmz)}) -> Dx({len(Dx)})")
    return 0  # Absolutely needed for this callback to be well defined (see nidaqmx doc).

def updateplots():
    global Dt,Dx,Dy,Dz, BOKEHBUFFERSIZE, signal_source,spectrum_source, running
    # # BEST PRACTICE --- update .data in one ste
    sig = dict(t=Dt,mx=Dx,my=Dy,mz=Dz) # new data dict

    f, px = welch(Dx,SR,window='hann',nperseg=BOKEHBUFFERSIZE/6,detrend='constant') 
    f, py = welch(Dy,SR,window='hann',nperseg=BOKEHBUFFERSIZE/6,detrend='constant') 
    f, pz = welch(Dz,SR,window='hann',nperseg=BOKEHBUFFERSIZE/6,detrend='constant') 
   
    # (f, px) = periodogram(Dx, SR, scaling='density')
    # (f, py) = periodogram(Dy, SR, scaling='density')
    # (f, pz) = periodogram(Dz, SR, scaling='density')
    
    lsd = dict(f=f,px=px,py=py,pz=pz)

    # seems to be a problem with Array property, using List for now
    # wd = px.tolist()
    # wd[0] = wd[1] # avoid the lowest frequency point
    # waterfall_renderer.latest = wd 
    # waterfall_plot.y_range.end = SR/2

    signal_source.data = sig
    spectrum_source.data = lsd


signal_source = ColumnDataSource(data=dict(t=[], mx=[], my=[], mz=[])) # t,mx,my,mz
signal_plot = figure(title="Signal", min_width=200, min_height=200)
signal_plot.sizing_mode = 'scale_both'
signal_plot.background_fill_color = "white" # "#eaeaea"
signal_plot.line(x="t", y="mx", line_color="red", source=signal_source, legend_label="X")
signal_plot.line(x="t", y="my", line_color="green", source=signal_source, legend_label="Y")
signal_plot.line(x="t", y="mz", line_color="blue", source=signal_source, legend_label="Z")
signal_plot.legend.location = "top_left"
signal_plot.legend.click_policy="hide"
signal_plot.y_range.only_visible = True

spectrum_source = ColumnDataSource(data=dict(f=[], px=[], py=[], pz=[])) # f,px,py,pz
spectrum_plot = figure(title="Power spectrum (WARNING: unscaled FFT)",x_axis_type="log",y_axis_type="log", min_width=200, min_height=200)
spectrum_plot.sizing_mode = 'scale_both'
spectrum_plot.background_fill_color = "white" #  "#eaeaea"
spectrum_plot.line(x="f", y="px", line_color="red", source=spectrum_source, legend_label="X")
spectrum_plot.line(x="f", y="py", line_color="green", source=spectrum_source, legend_label="Y")
spectrum_plot.line(x="f", y="pz", line_color="blue", source=spectrum_source, legend_label="Z")
spectrum_plot.legend.location = "top_left"
spectrum_plot.legend.click_policy="hide"
spectrum_plot.y_range.only_visible = True

# MAX_FREQ_KHZ = SR/2.0
# NUM_GRAMS = 600
# GRAM_LENGTH = 512
# TILE_WIDTH = 200
# EQ_CLAMP = 20

# PALETTE = ['#081d58', '#253494', '#225ea8', '#1d91c0', '#41b6c4', '#7fcdbb', '#c7e9b4', '#edf8b1', '#ffffd9']
# PLOTARGS = dict(tools="", toolbar_location=None, outline_line_color='#595959')

# waterfall_renderer = WaterfallRenderer(palette=PALETTE, num_grams=NUM_GRAMS,gram_length=GRAM_LENGTH, tile_width=TILE_WIDTH)
# waterfall_plot = figure(width=600, height=200,x_range=[0, NUM_GRAMS], y_range=[0, MAX_FREQ_KHZ], **PLOTARGS)
# waterfall_plot.grid.grid_line_color = None
# waterfall_plot.background_fill_color = "#024768"
# waterfall_plot.renderers.append(waterfall_renderer)

# Configure and setup the tasks
task_in = nidaqmx.Task()
cfg_read_task(task_in)
stream_in = AnalogMultiChannelReader(task_in.in_stream)
task_in.register_every_n_samples_acquired_into_buffer_event(bufsize_callback, reading_task_callback)

# Set up the Bokeh plot window
curdoc().add_root(column(children=[signal_plot,spectrum_plot],sizing_mode="stretch_both")) # Time series and FFT
# curdoc().add_root(grid(column(waterfall_plot, row(column(signal_plot, spectrum_plot,sizing_mode="stretch_both")),sizing_mode="stretch_both"),sizing_mode="stretch_both")) # Spectrogram, time series, and FFT
                                
# Set the Bokeh plot update timer
curdoc().add_periodic_callback(updateplots, UPDATEMILLISEC)

running = True
time_start = datetime.now()
task_in.start()

# while running:  # make this adapt to number of channels automatically
#     time.sleep(0.1)  
#     print('.')

# # Close task to clear connection once done
# task_in.close()
# duration = datetime.now() - time_start
# print ("Task closed")



# curdoc().title = "VMR"


