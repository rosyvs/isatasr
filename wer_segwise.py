import os
import re
import subprocess
import pandas as pd
import jiwer 
import time
import string
import numpy as np
from rosy_asr_utils import *

# compute WER for any with both ASR and reference transcripts for corresponding segments
args_ctl =os.path.join('configs', 'gold_Chris.txt')

# loop over sessions in control file and compute WER 
with open(args_ctl) as ctl: # reads lines without empties
    sesslist = (line.rstrip() for line in ctl) 
    sesslist = list(os.path.normpath(line) for line in sesslist if line)

for sesspath in sesslist: 
    sesspath = sesspath.strip()
    sessname = os.path.basename(sesspath)
    print(f'COMPUTING SEGWISE WER FOR SESSION: {sessname}')
    asrDir = os.path.join(sesspath,'asr_segwise_gained')
    transcriptDir = os.path.join(sesspath,'transcripts_segwise')

    # get list of segments
    seglist = []
    for file in os.listdir(asrDir):
        if not file.endswith('.asr'): continue
        base = re.sub('.asr', '', file)
        field = base.split('_')
        s= field[len(field)-1]
        seglist.append( int(s) )
    seglist.sort()
    print(f'-{len(seglist)} segments found')

    seg_data = []
    # loop over segments
    aligned_segwise=[]
    for s in seglist:
        start = time.process_time()
        asrFile = os.path.join(asrDir,f'{sessname}_{s}.asr')
        if not os.path.isfile(asrFile): 
            asr_wordcount = None
            asr_exists = False
            asr = ''
            print(f'--no ASR for segment {s}')
        else: 
            asr = open(asrFile,'r').read()
            asr = format_text_for_wer(asr)
            asr_exists = True
            asr_wordcount = len(asr.split())



        transcriptFile = os.path.join(transcriptDir,f'{sessname}_{s}.txt')
        if not os.path.isfile(transcriptFile): 
            transcript_wordcount = None
            transcript_exists = False
            transcript = ''
            print(f'--no transcript for segment {s}')

        else:
            transcript = open(transcriptFile,'r').read()
            transcript = format_text_for_wer(transcript) 
            transcript_exists = True
            transcript_wordcount = len(transcript.split())
        
        if transcript_exists and asr_exists:
            print(f'\nTRANSCRIPT: {transcript}')
            print(f'ASR       : {asr}')

            wer = jiwer.wer(transcript.split(), asr.split())
            wer_meas = jiwer.compute_measures(transcript.split(), asr.split())
            aligned, edit_ops =  align_words(transcript.split(), asr.split())
            aligned['segment'] = s
            aligned_segwise.append(aligned)
        else:
            wer = None
            wer_meas = {'mer':None,'substitutions':None, 'deletions':None, 'insertions':None }
        end = time.process_time()
        time_elapsed = end-start
        seg_data.append([sessname, s, asr_exists, asr_wordcount, transcript_exists, transcript_wordcount, \
            wer,wer_meas['mer'],wer_meas['substitutions'], wer_meas['deletions'],wer_meas['insertions'],time_elapsed])
    aligned_segwise = pd.concat(aligned_segwise)
    aligned_segwise.to_csv(os.path.join(sesspath,f'alignment_segwise_{sessname}.csv'), index=False)

    # make Df to store segmentwise metrics
    seg_summary = pd.DataFrame(seg_data, columns = ['session','segment','asr_exists','asr_wordcount',' transcript_exists','transcript_wordcount',\
    'wer','mer','substitutions','deletions','insertions','time'])
    seg_summary.to_csv(os.path.join(sesspath, f'segwise_wer_{sessname}.csv') ) 

    # summarise at the entire session level
    sess_subs = seg_summary['substitutions'].sum()
    sess_dels = seg_summary['deletions'].sum()
    sess_ins =  seg_summary['insertions'].sum()
    sess_N = seg_summary['transcript_wordcount'].sum()
    sess_meas = wer_from_counts(sess_N, sess_subs, sess_dels, sess_ins)

    sess_summary = pd.DataFrame({'session':sessname, 
                    'speaker': 'all',
                    'n_segments':len(seglist), 
                    'asr_wordcount':sum(seg_summary['asr_wordcount']),
                    'transcript_wordcount':sum(seg_summary['transcript_wordcount']),
                    'wer': sess_meas['wer'],
                    'mer':sess_meas['mer'],
                    'substitutions': sess_subs,
                    'deletions': sess_dels,
                    'insertions': sess_ins,
                    'sub_pct': sess_meas['sub_pct'],
                    'del_pct': sess_meas['del_pct'],
                    'ins_pct': sess_meas['ins_pct'],
                    },
                    index=[0])
    sess_summary.to_csv(os.path.join(sesspath, f'segwise_wer_SUMMARY_{sessname}.csv') )
