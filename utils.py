import os
import numpy as np
from matplotlib import pyplot as plt
import IPython.display as ipd
import librosa
import pandas as pd
#%matplotlib inline

def print_plot_play(y, sr, text=''):
    """1. Prints information about an audio singal, 2. plots the waveform, and 3. Creates player
    
    Notebook: C1/B_PythonAudio.ipynb
    
    Args: 
        y: Input signal
        sr: Sampling rate of x    
        text: Text to print
    """
    print('%s sr = %d, y.shape = %s, y.dtype = %s' % (text, sr, y.shape, y.dtype))
    plt.figure(figsize=(8, 2))
    plt.plot(y, color='gray')
    plt.xlim([0, y.shape[0]])
    plt.xlabel('Time (samples)')
    plt.ylabel('Amplitude')
    plt.tight_layout()
    plt.show()
    ipd.display(ipd.Audio(data=y, rate=sr))