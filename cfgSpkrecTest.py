import os 
import pandas as pd
from pydub.audio_segment import AudioSegment, effects

# generates configuration files for speaker verification tests, given a label file

# options
opts = {}
opts['frame_dur_s'] = 1.5
opts['frame_shift_s'] = 0.5
opts['sessions'] = os.path.join('configs', '4SG.txt') # path to session list 
opts['simulate_enrollment'] = True # simulate enrollment by extracting random utterance to use as target
opts['targets_dir'] = 'targets' # subdir of session directory containing enrollment audio (will create if simulating)
opts['labels_fname'] = 'utt_labels_{sessname}.csv' # relative to session directory

# get utterance-level timestamped speaker ID from annotations
verstr = 'spkv_test1'

with open(opts['sessions']) as ctl: # reads lines without empties
    sesslist = (line.rstrip() for line in ctl) 
    sesslist = list(line for line in sesslist if line)

def get_all_spkr_labels(labels, start_s, end_s):
    # pull speaker label for a defined audio interval
    # allowing for multiple labels per interval
    sample_labels = labels['']
    return sample_labels

def get_best_spkr_label(labels, start_s, end_s):
    # pull speaker label for a defined audio interval
    # choose majority label in case of overlap


def labels_to_samples(labels, audio_dur, frame_dur_s, frame_shift_s):
    # generate samples from speaker-labelled audio with corresponding speaker labels
    # unlabelled audio (could be speech, silence or background) to be labelled as 'Null'
    samples = []
    samp_start = range(0,audio_dur-frame_dur_s,frame_shift_s)
    for s in samp_start:
        sample_labels = get_all_spkr_labels(labels, start_s, end_s)


    return samples

cfg = [] # for storing list of test comparisons and timestamps
for sesspath in sesslist: 
    sess_data = []
    sesspath = sesspath.strip()
    sessname = os.path.basename(sesspath)
    wavfile = os.path.join(sesspath, f'{sessname}.wav')
    # TODO eval the below with custom variable name
    labelfile = os.path.join(sesspath, opts['labels_fname'].format(sessname=sessname) )
    labels = pd.read_csv(labelfile)

    wavfile = os.path.join(sesspath, f'{sessname}.wav')
    audio = AudioSegment.from_file(wavfile)
    session_duration = audio.duration_seconds

    ##
    sample_labels = labels["speaker"]


    ##

    samples = labels_to_samples(labels, session_duration,opts['frame_dur_s'], opts['frame_shift_s'])
    

