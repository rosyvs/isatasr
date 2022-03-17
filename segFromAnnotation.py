# extract labelled audio of interest using timestamped transcription
# read in utt-labels.csv file based on the ground-truth utterance boundaries from diarized, timestamped transcript
# each utterance becomes a segment
# segments are blocked to ~1min blocks for comparability to VAD/ sending to REV

from pydub import AudioSegment
import os
import re
import csv
import pandas as pd
from rosy_asr_utils import *

# options for writing audio
channels = 1
sample_width = 2
sample_rate = 48000
bit_depth = 16
export_segment_audio = True
blksecs = 59 # Google has refused some blocks if exactly 60 seconds 


args_ctl =os.path.join('configs', 'deepSample2.txt') # list of session directories to extract segments from
label_fname_pattern = 'utt_labels_{sessname}.csv' # relative to session directory


# ITERATE OVER SESSIONS
with open(args_ctl) as ctl:
    sesslist = (line.rstrip() for line in ctl) 
    sesslist = list(line for line in sesslist if line)

for sesspath in sesslist: 
    print(f'sesspath: {sesspath}')
    sesspath = sesspath.strip()
    sessname = os.path.basename(sesspath)
    blkmapFile = os.path.join(sesspath, f'{sessname}.blk')

    labelFile = os.path.join(sesspath,label_fname_pattern.format(**locals()))

    if export_segment_audio: 
        segDir = os.path.join(sesspath,'segments')
        if not os.path.exists(segDir):
            os.makedirs(segDir)
    segTranscriptDir = os.path.join(sesspath,'ELANtranscript_segwise')
    if not os.path.exists(segTranscriptDir):
        os.makedirs(segTranscriptDir)

    # load session audio
    sess_audio = AudioSegment.from_wav(os.path.join(sesspath, f'{sessname}.wav'))
    # use same defaults as for VAD to block uttern

    with open(labelFile) as in_file:
        reader = csv.reader(in_file, delimiter=",")
        # # skip header
        next(reader)
        blk = []
        b=0
        curlen=0.0
        for s, utt in enumerate(reader):
            speaker,utterance,start_sec, end_sec = utt
            start_sec = float(start_sec)
            end_sec = float(end_sec)
            dur = end_sec-start_sec
            seg_audio = sess_audio[start_sec*1000:end_sec*1000]

            if export_segment_audio:
                segWAVfile = os.path.join(segDir,f'{sessname}_{s}.wav' )
                seg_audio.export(segWAVfile, format='wav')
                segTRANSCRIPTfile = os.path.join(segTranscriptDir,f'{sessname}_{s}.txt' )
                with open(segTRANSCRIPTfile, 'w') as outfile:
                    outfile.write(utterance)

            if dur > blksecs:
                print('utterance too long, TODO split')

            if curlen + dur > blksecs:
                # reset/increment counters
                b+=1
                curlen = dur

            else:
                curlen += dur
            blk.append((b,s,start_sec,end_sec))
    with open(blkmapFile, 'w') as outfile:
        for b in blk:
            line = ' '.join(str(x) for x in b)
            outfile.write(line + '\n')
