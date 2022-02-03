import os
import re
import pandas as pd
import jiwer 
import time
import string
import numpy as np
from rosy_asr_utils import *
from natsort import natsorted 

# this version will concatenate all ASR and all transcripts before computing WER. 
# Use this if the ASR blocks and transcript blocks did not align
# such is the case when different segmentation settings are used for ASR vs transcribed audio

# loop over sessions in control file and compute WER for any with both ASR and REV transcripts

args_ctl =os.path.join('configs', 'deep5.txt')
verstr = 'deep5_VAD_REV'
asrDirPattern = 'asr_full'
transcriptDirPattern = 'REVtranscripts'

with open(args_ctl) as ctl: # reads lines without empties
    sesslist = (line.rstrip() for line in ctl) 
    sesslist = list(line for line in sesslist if line)

all_sess_data = []

for sesspath in sesslist: 
    sess_data = []
    start = time.process_time()
    sesspath = sesspath.strip()
    sessname = os.path.basename(sesspath)
    print(f'COMPUTING WER FOR SESSION: {sessname}')
    asrDir = os.path.join(sesspath,asrDirPattern)
    transcriptDir = os.path.join(sesspath,transcriptDirPattern)

    asr_fullsess = []
    transcript_fullsess = []

    if not os.path.exists(asrDir):
        print(f'- no ASR directory ({asrDirPattern}) for this session')
        continue
    # loop over asr files 
    asr_list = [f for f in os.listdir(asrDir) if f.endswith('.asr')]
    n_asr = len(asr_list)
    # sort by block/segment number
    asr_list = natsorted(asr_list)


    for f in asr_list:
        start = time.process_time()
        asrFile = os.path.join(asrDir,f)
        if not os.path.isfile(asrFile): 
            asr_wordcount = None
            asr_exists = False
            asr = ''
        else: 
            asr = open(asrFile,'r').read()
            asr = format_text_for_wer(asr)
        asr_fullsess.append(asr)

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
    asr_fullsess = ' '.join(asr_fullsess)


    if not transcript_fullsess.strip():
        transcript_exists=False
        print('- no transcript for session')

    else:
        transcript_exists=True
    if not asr_fullsess.strip():
        asr_exists=False
        print('- no ASR for session')
    else:
        asr_exists=True
    if transcript_exists and asr_exists:
        print(f'TRANSCRIPT: {transcript_fullsess}')
        print(f'ASR: {asr_fullsess}')
        transcript_fullsess = transcript_fullsess.split() 
        asr_fullsess = asr_fullsess.split() 

        transcript_wordcount = len(transcript_fullsess)
        asr_wordcount = len(asr_fullsess)
        wer = jiwer.wer(transcript_fullsess, asr_fullsess)
        wer_meas = jiwer.compute_measures(transcript_fullsess, asr_fullsess)

        aligned, edit_ops =  align_words(transcript_fullsess, asr_fullsess)
        aligned.to_csv(os.path.join(sesspath,f'alignment_{verstr}_{sessname}.csv'), index=False)

    else: 
        wer = None
        wer_meas = {'mer':None,'substitutions':None, 'deletions':None, 'insertions':None }
    end = time.process_time()
    time_elapsed = end-start
    sess_data = [sessname,n_asr,n_transcript, asr_exists, asr_wordcount,transcript_exists, transcript_wordcount, \
        wer,wer_meas['mer'],wer_meas['substitutions'], wer_meas['deletions'],wer_meas['insertions'],\
             wer_meas['substitutions']/transcript_wordcount, wer_meas['deletions']/transcript_wordcount,wer_meas['insertions']/transcript_wordcount]
    sess_data = pd.DataFrame([sess_data], columns = ['session','n_asr','n_transcript','asr_exists','asr_wordcount',' transcript_exists','transcript_wordcount',\
    'wer','mer','substitutions','deletions','insertions','sub_rate','del_rate','ins_rate'])
    sess_data.to_csv(os.path.join(sesspath,f'sesswise_wer_{verstr}_{sessname}.csv'), index=False,float_format='%.3f')

    all_sess_data.append(sess_data)

# Summary of WER over all requested sessions
pd.concat(all_sess_data).to_csv( f'results/sesswise_wer_{verstr}.csv',index=False, float_format='%.3f') 