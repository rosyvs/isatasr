# format manual annotations (speaker ID and transcription from human transcriber/REV) 
# to generate label file with specific structure

from numpy import exp
import sys
import os
import re
import argparse
import csv
import pandas as pd
from rosy_asr_utils import strip_punct

annotation_dir = './data/id_labelled/cher_transcripts' # where to find manual annotation csv files
args_ctl =os.path.join('configs', '4SG.txt') # list of session directories to run ASR on
utt_padding = 0.0 # because utterances are on seconds resolution, some briefer utterances had the same start and end second - pad if so

 
def HHMMSS_to_sec(time_str):
    """Get Seconds from time with milliseconds."""
    if time_str.count(':')==2:
        h, m, s = time_str.split(':')
    elif time_str.count(':')==3:
    # temp fix for files with : as Second/millisecond delimiter and tenths of a second only - Cher's google sheets annotations
        h, m, s, ms = time_str.split(':')
        s = int(s)+float(ms)/10
    else:
        print(f'input string format not supported: {time_str}')
    return int(h) * 3600 + int(m) * 60 + float(s) 


# ITERATE OVER SESSIONS
with open(args_ctl) as ctl:
    sesslist = (line.rstrip() for line in ctl) 
    sesslist = list(line for line in sesslist if line)

for sesspath in sesslist: 
    print(f'sesspath: {sesspath}')
    sesspath = sesspath.strip()
    sessname = os.path.basename(sesspath)
    csvfile = os.path.join(annotation_dir, f'{sessname}_diarized.csv') # read labels from here

    labelFile = os.path.join(sesspath, f'utt_labels_{sessname}.csv') # will be created
    with open(csvfile, 'r', newline='') as in_file:
        reader = csv.reader(in_file)
        # skip header
        next(reader)
        curlen = 0.0
        labels = [] # transcript with speaker labels and block/segment numbers

        for utt in reader:
            if not ''.join(utt).strip(): # skip blank lines
                continue
            print(utt)
            start_HHMMSS,speaker,utterance,end_HHMMSS = utt
            # clean up speaker and utterance for ASR
            speaker = re.sub(' ','',speaker)
            speaker = re.sub(':','',speaker)
            utterance_clean = re.sub("[\(\[].*?[\)\]]", " ", utterance)
            utterance_clean = strip_punct(utterance_clean) 
            start_sec = HHMMSS_to_sec(start_HHMMSS)-utt_padding
            end_sec = HHMMSS_to_sec(end_HHMMSS)+utt_padding


            labels.append((speaker, utterance, start_sec,end_sec))

    labels= pd.DataFrame(labels, columns = ('speaker', 'utterance', 'start_sec','end_sec'))
    labels.to_csv(labelFile,index=False)