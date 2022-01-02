import os 
import pandas as pd
import numpy as np
import re
import random
from pydub.audio_segment import AudioSegment, effects

# generates configuration files for speaker verification tests, given a label file for each session

# options
opts = {}
opts['frame_dur_s'] = 1.5
opts['frame_shift_s'] = 0.5
opts['sessions'] = os.path.join('configs', '4SG.txt') # path to session list 
opts['simulate_enrollment'] = True # simulate enrollment by extracting first utterances to use as target
opts['targets_dir'] = 'targets' # subdir of session directory containing enrollment audio (will create if simulating)
opts['labels_fname'] = 'utt_labels_{sessname}.csv' # relative to session directory
opts['cross_session'] = False # If True, pairings between sessions; if False, pairings within session only
opts['sampleVsample'] = False # if True, pairings between all samples; if False, pairings between enrolment and samples only
opts['density'] = 0.01 # float. Proportion of all possible pairings to use. If <1.0 will randomly sample from density*n pairings
opts['verstr'] = 'spkv_test1_debug'

with open(opts['sessions']) as ctl: # reads lines without empties
    sesslist = (line.rstrip() for line in ctl) 
    sesslist = list(line for line in sesslist if line)

def get_all_spkr_labels(labels, start_s, end_s):
    # pull speaker label for a defined audio interval
    # allowing for multiple labels per interval
    matched_utt = (labels['start_sec'] < end_s) & (labels['end_sec'] > start_s)
    sample_labels = labels.loc[matched_utt, 'speaker'].to_list()   
    if not matched_utt:
        sample_labels = '_UNKNOWN'
    return sample_labels

def get_best_spkr_label(labels, start_s, end_s):
    # pull speaker label for a defined audio interval
    # choose majority label in case of overlap
    overlap_duration = np.maximum(0.0,labels['end_sec'].clip(upper=end_s) - labels['start_sec'].clip(lower=start_s))
    if max(overlap_duration) == 0.0:
        best_sample_label='_UNKNOWN'
    else:
        best_sample_label = labels.loc[np.argmax(overlap_duration), 'speaker']
    return best_sample_label

def labels_to_samples(labels, audio_dur, frame_dur_s, frame_shift_s):
    # generate samples from speaker-labelled audio with corresponding speaker labels
    # unlabelled audio (could be speech, silence or background) to be labelled as 'Null'
    samples = []
    samp_start = np.arange(0,audio_dur-frame_dur_s,frame_shift_s)
    for s in samp_start:
        sample_label = get_best_spkr_label(labels, s, s+frame_dur_s)
        samples.append((s, s+frame_dur_s, sample_label))
    return samples

test_cfg = [] # for storing list of test comparisons and timestamps
enrollment_list_all=[]
sample_list_all=[]

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

    ## get list of samples
    sample_list = labels_to_samples(labels, session_duration,opts['frame_dur_s'], opts['frame_shift_s'])
    # add filename column TODO
    sample_list = [(wavfile,) + elms for elms in sample_list]
    ## get enrollment
    enrollment_list = []

    if opts['simulate_enrollment']:
        if not os.path.exists(os.path.join(sesspath, opts['targets_dir'])):
            os.makedirs(os.path.join(sesspath, opts['targets_dir']))
        # list speaker IDs
        speakers = list(set(labels['speaker']))
        enrol_dur = 10.0 # will concatenate first 10s of utterances from this target
        for t in speakers:
            labels_this_spkr = labels[labels['speaker'].str.match(t)]
            enrAudio = AudioSegment.empty() 
            starts_ms  = labels_this_spkr['start_sec'].to_list()*1000
            ends_ms = labels_this_spkr['end_sec'].to_list()*1000
            while enrAudio.duration_seconds <enrol_dur:
                enrAudio += audio[starts_ms.pop(0)*1000 : ends_ms.pop(0)*1000]
            enrAudio = enrAudio[0:1000*enrol_dur]    
            enrFile = os.path.join(sesspath,opts['targets_dir'],f'enrollment_simulated_{t}.wav')        
            enrAudio.export(enrFile ,format='wav')
            enrollment_list.append((enrFile, 0.0, enrol_dur,t))
    else: # read enrollment from targets_dir
        found_enrFiles = [f for f in os.listdir(os.path.join(sesspath,opts['targets_dir'])) if f.endswith('.wav')]
        for f in found_enrFiles:
            enrFile = os.path.join(sesspath,opts['targets_dir'], f)
            enrAudio = AudioSegment.from_file(enrFile)
            enrDur = enrAudio.duration_seconds
            # strip keyword parts of filename in crude attempt to get target name TODO update when we have real enrollment
            speaker = re.sub('.wav','',f)
            speaker = re.sub('enrollment_simulated_','',speaker)
            speaker = re.sub('enrollment_','',speaker)

            enrollment_list.append((enrFile, 0.0, enrol_dur,speaker))

    # append to all-session list        
    enrollment_list_all+=enrollment_list
    sample_list_all+=sample_list
    
    ## pair up within-session 
    if not opts['cross_session']:
        if not opts['sampleVsample']:
            for e in enrollment_list:
                for s in sample_list: 
                    test_cfg.append(e+s)
    
        if opts['sampleVsample']:
            # TODO disallow NA-NA pairings
            print('TODO')

# prune test list
if not (opts['density'] ==1.0):
    test_cfg = random.sample(test_cfg, int(len(test_cfg)*opts['density']))

# pair up cross-sessions
# TODO deal w duplicate speakerID across sessions that aren't actually the same person e.g. TargetedTeacher1

## write out test configuration
test_cfg_df = pd.DataFrame(test_cfg, columns=['x1path','x1start_s','x1end_s','x1speaker','x2path','x2start_s','x2end_s','x2speaker'])
test_cfg_df['match'] = test_cfg_df['x1speaker']==test_cfg_df['x2speaker']

print(f'Generated speaker verification test config for {opts["verstr"]}')
print(f'...containing {len(test_cfg)} comparisons')
print(f'...of which {len(test_cfg_df[test_cfg_df["match"]])} are matched speakers')

test_cfg_df.to_csv(os.path.join('configs','speaker_verification','tests', f'{opts["verstr"]}_config.csv'),index=False)