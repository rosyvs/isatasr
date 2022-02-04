import os
import re
import pandas as pd
import jiwer 
import time
import string
import numpy as np
from rosy_asr_utils import *
from natsort import natsorted 

# loop over sessions in control file and get stats on transcripts

ctlfile = 'deepSample2'
args_ctl =os.path.join('configs', f'{ctlfile}.txt')
verstr = 'deepSample2'
transcriptDirPattern = 'ELANtranscript'

with open(args_ctl) as ctl: # reads lines without empties
    sesslist = (line.rstrip() for line in ctl) 
    sesslist = list(line for line in sesslist if line)

all_sess_data = []

for sesspath in sesslist: 
    sess_data = []
    sesspath = sesspath.strip()
    sessname = os.path.basename(sesspath)
    transcriptDir = os.path.join(sesspath,transcriptDirPattern)

    transcript_fullsess = []

    if not os.path.exists(transcriptDir):
        print('- no transcript for session')
        continue
    # loop over transcript files
    transcript_list = [f for f in os.listdir(transcriptDir) if f.endswith('.txt') and not f.endswith('_diarized.txt')]
    n_transcript = len(transcript_list)
    transcript_list = natsorted(transcript_list) # sort by block/seg number

    for f in transcript_list:
        transcriptFile = os.path.join(transcriptDir,f)
        if not os.path.isfile(transcriptFile): 
            transcript_wordcount = None
            transcript_exists = False
            transcript = ''
        else:
            transcript = open(transcriptFile,'r').read()
            transcript = format_text_for_wer(transcript) 
        transcript_fullsess.append(transcript)
    # concatenate blocks
    transcript_fullsess = ' '.join(transcript_fullsess)


    if not transcript_fullsess.strip():
        transcript_exists=False
        print('- no transcript for session')

    else:
        transcript_exists=True
    
    transcript_fullsess = transcript_fullsess.split() 
    transcript_wordcount = len(transcript_fullsess)

    sess_data = [sessname,n_transcript, transcript_wordcount]
    sess_data = pd.DataFrame([sess_data], columns = ['session','n_transcript','transcript_wordcount'])

    all_sess_data.append(sess_data)

# Summary of transcript over all requested sessions
pd.concat(all_sess_data).to_csv( f'results/transcript_stats_{verstr}.csv',index=False, float_format='%.3f') 