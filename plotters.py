# Library of plotting and analysis functions
import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt
from scipy import signal
from math import sqrt

def threeplot(t,x,y,z,units,title):
    fig, ax = plt.subplots()
    mx = np.mean(x)
    my = np.mean(y)
    mz = np.mean(z)
    ax.plot(t, x-mx,label=f'X {mx:.0f} DC')
    ax.plot(t, y-my,label=f'Y {my:.0f} DC')
    ax.plot(t, z-mz,label=f'Z {mz:.0f} DC')
    ax.legend()
    ax.set_title(title)
    ax.set_ylabel(units)
    ax.set_xlabel('Time (seconds)', fontsize=12)
    plt.tick_params(axis='both', which='major', labelsize=12)
    # plt.axis([0, 1100, 0, 1100000])
    plt.grid(visible=True)
    plt.show()

def ftmg7plot(t,G,units,title):
    fig, ax = plt.subplots()
    # Extract components... zx and zy are redundant
    xx = G[0,0,:]
    xy = G[0,1,:]
    xz = G[0,2,:] 
    yx = G[1,0,:]
    yy = G[1,1,:]
    yz = G[1,2,:]
    zz = G[2,2,:]
    mxx = np.mean(xx)
    mxy = np.mean(xy)
    mxz = np.mean(xz) 
    myx = np.mean(yx)
    myy = np.mean(yy)
    myz = np.mean(yz) 
    mzz = np.mean(zz) 
    ax.plot(t, xx-mxx,label=f'XX {mxx:.0f} DC')
    ax.plot(t, xy-mxy,label=f'XY {mxy:.0f} DC')
    ax.plot(t, xz-mxz,label=f'XZ {mxz:.0f} DC')
    ax.plot(t, yx-myx,label=f'YX {myx:.0f} DC')
    ax.plot(t, yy-myy,label=f'YY {myy:.0f} DC')
    ax.plot(t, yz-myz,label=f'YZ {myz:.0f} DC')
    ax.plot(t, zz-mzz,label=f'ZZ {mzz:.0f} DC')
    ax.legend()
    ax.set_title(title)
    ax.set_ylabel(units)
    ax.set_xlabel('Time (seconds)', fontsize=12)
    plt.tick_params(axis='both', which='major', labelsize=12)
    # plt.axis([0, 1100, 0, 1100000])
    plt.grid(visible=True)
    plt.show()

def tf(x,y,z):
    return np.sqrt(x*x+y*y+z*z)

def oneplot(t,v,units,title):
    fig, ax = plt.subplots()
    mv = np.mean(v)
    ax.plot(t, v,label=f'{mv:.0f} DC')
    ax.legend()
    ax.set_title(title)
    ax.set_ylabel(units)
    ax.set_xlabel('Time (seconds)', fontsize=12)
    plt.tick_params(axis='both', which='major', labelsize=12)
    # plt.axis([0, 1100, 0, 1100000])
    plt.grid(visible=True)
    plt.show()

def lsd(t,v,sr,units,title):
    freqs, psd = signal.welch(v,fs=sr,nperseg=len(v)//2)
    lsd = np.sqrt(psd) 
    lsfreqs = freqs[1]+freqs[1:] # Duplicate first nonzero point, LS doesn't like 0 freq
    lspsd = signal.lombscargle(t,v,lsfreqs/(2*np.pi)) # Convert from Hz to rads/sec
    lslsd = np.sqrt(lspsd)
    plt.figure(figsize=(5, 4))
    plt.loglog(freqs, lsd, label='Welch')
    plt.loglog(lsfreqs, lslsd, label='Lomb-Scargle')
    plt.title('LSD  '+title)
    plt.xlabel('Frequency (Hz)')
    plt.ylabel(units+'/rtHz')
    plt.tight_layout()
    plt.grid(visible=True)
    plt.show()

def threelsd(x,y,z,sr,units,title,lx,ly,lz,welchfactor):
    xfreqs, xpsd = signal.welch(x,fs=sr,nperseg=len(x)//welchfactor)
    lsdx = np.sqrt(xpsd)
    yfreqs, ypsd = signal.welch(y,fs=sr,nperseg=len(y)//welchfactor)
    lsdy = np.sqrt(ypsd)
    zfreqs, zpsd = signal.welch(z,fs=sr,nperseg=len(z)//welchfactor)
    lsdz = np.sqrt(zpsd)
    plt.figure(figsize=(5, 4))
    plt.loglog(xfreqs,lsdx, label=lx)
    plt.loglog(yfreqs,lsdy, label=ly)
    plt.loglog(zfreqs,lsdz, label=lz)
    plt.legend()
    plt.title('LSD  '+title)
    plt.xlabel('Frequency (Hz)')
    plt.ylabel(units+'/rtHz')
    plt.tight_layout()
    plt.grid(visible=True)
    plt.show()

def sg(v,sr,units,title):
    freqs, times, spectrogram = signal.spectrogram(v,fs=sr)
    plt.figure(figsize=(5, 4))
    plt.imshow(spectrogram, aspect='auto', origin='lower') # cmap='hot_r', 
    plt.title(title)
    plt.ylabel('Frequency')
    plt.xlabel('Time')
    plt.tight_layout()
    plt.ylim([0, sr/2])
    plt.show()

# Reference paper: Xu, Lei, et al. "Simulation analysis of magnetic gradient full-tensor measurement system.",
#   Mathematical Problems in Engineering 2021 (2021): 1-13.
# Their formulations use 1..n sensor designation, kept that here to avoid transcription errors
    
def ftmgcross(d,B1x,B1y,B1z,B2x,B2y,B2z,B3x,B3y,B3z,B4x,B4y,B4z):
    # Calculate FTMG for four-sensor cross with separation d
    # Sensor layout:    2
    #                 3   1
    #                   4
    return (1/d)*[[B1x-B3x, B1y-B3y, B1z-B3z],[B2x-B4x, B2y-B4y, B2z-B4z], [B1z-B3z, B2z-B4z, B3x+B4y-(B1x+B2y)]]

def ftmget(d,B1x,B1y,B1z,B2x,B2y,B2z,B3x,B3y,B3z):
    # Calculate FTMG for equilateral triangle with side length d
    # Sensor layout:    2
    #                 3   1
    return np.asarray(1/sqrt(3)*d)*[
        [sqrt(3)*(B1x-B3x), sqrt(3)*(B1y-B3y), sqrt(3)*(B1z-B3z)],
        [2*B2x-(B1x+B3x), 2*B2y-(B1y+B3y), 2*B2z-(B1z+B3z)],
        [sqrt(3)*(B1z-B3z), 2*B2z-(B1z+B3z), (B1y+B3y)-2*B2y-sqrt(3)*(B1x-B3x)]]
    
