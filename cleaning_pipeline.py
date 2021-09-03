#%% imports

import pandas as pd
import os
import numpy as np
import librosa as lr # requires ffmpeg: https://www.gyan.dev/ffmpeg/builds/ 
from utils import print_plot_play
from scipy.io import wavfile
import speech_recognition as asr
#TODO use pydub instad of librosa and scipy.io for io audio? 
#%% extract audio from video

video_path = os.path.normpath("./media/video/")
video_fname = 'Disk Problem_trimmed_062121'
debug_crop = 20 # crop audio to this many seconds for devel, otherwise set to None
if debug_crop != None: 
    verstr = f"_crop{debug_crop}s" # filename flag for exported audio
else: 
    verstr=''
y,sr = lr.load(os.path.normpath(video_path + '/' + video_fname + '.mp4'),sr=None, duration = debug_crop)
print_plot_play(y=y, sr=sr, text='raw audio: ')
# librosa.display.specshow
#%% write audio 

audio_path = os.path.normpath("./media/audio/")
fname_y = os.path.normpath(audio_path + '/' + video_fname + verstr + '.wav')
wavfile.write(fname_y, sr, y.astype(np.int16) ) # needs to be 16bit PCM for speech_recognition

#%% transcribe
# r=asr.Recognizer() # this is a bit clunky - OO, only reads audio from file (not direct from a variable)
# with asr.WavFile(fname_y) as source:              # use "test.wav" as the audio source
#     asr_obj = r.record(source)   
# transcript =r.recognize_sphinx(asr_obj)
# print(transcript)

# %% noisereduce noise gating: nonstationary vs stationary
# se also: Per-Channel Energy Normalization
# 
from noisereduce import reduce_noise 
y_1 = reduce_noise(y=y, sr=sr, time_constant_s=1, prop_decrease = 0.8 )
print_plot_play(y=y_1, sr=sr, text='nonstationary noise reduction with noisereduce.reduce_noise ')
# transcript = asr.recognize_sphinx(y_1)
# print(transcript)
y_2 = reduce_noise(y=y, sr=sr, stationary=True, prop_decrease = 0.8 )
print_plot_play(y=y_2, sr=sr, text='Stationary noise reduction with noisereduce.reduce_noise ')

#%% Wiener filtering
import soundpy as sp
y_3, sr = sp.filtersignal(y,sr = sr,filter_type = 'wiener', filter_scale=1) 
print_plot_play(y=y_3, sr=sr, text='Wiener filter with soundpy')

y_4, sr = sp.filtersignal(y_1,sr = sr,filter_type = 'wiener', filter_scale=1) 
print_plot_play(y=y_4, sr=sr, text='Wiener filter after NS noise reduction')

# metricGAN+