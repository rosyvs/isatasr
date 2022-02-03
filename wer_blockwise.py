import os
import re
import pandas as pd
import jiwer 
import time
import string
import numpy as np
from rosy_asr_utils import *

# loop over sessions in control file and compute WER for any with both ASR and REV transcripts at the block level
args_ctl =os.path.join('configs', 'sg_asr_211012.txt')

with open(args_ctl) as ctl: # reads lines without empties
    sesslist = (line.rstrip() for line in ctl) 
    sesslist = list(os.path.normpath(line) for line in sesslist if line)

for sesspath in sesslist: 
    sesspath = sesspath.strip()
    sessname = os.path.basename(sesspath)
    print(f'COMPUTING BLOCKWISE WER FOR SESSION: {sessname}')
    asrDir = os.path.join(sesspath,'asr_blockwise')
    transcriptDir = os.path.join(sesspath,'transcripts')

    # get list of blocks
    blklist = []
    for file in os.listdir(asrDir):
        if not file.endswith('.asr'): continue
        base = re.sub('.asr', '', file)
        field = base.split('_')
        b= field[len(field)-1]
        blklist.append( int(b) )
    blklist.sort()
    print(f'-{len(blklist)} blocks found')

    block_data = []
    # loop over blocks
    aligned_blockwise=[]
    for b in blklist:
        start = time.process_time()
        asrFile = os.path.join(asrDir,f'{sessname}_{b}.asr')
        if not os.path.isfile(asrFile): 
            asr_wordcount = None
            asr_exists = False
            asr = ''
            print(f'--no ASR for block {b}')
        else: 
            asr = open(asrFile,'r').read()
            asr = format_text_for_wer(asr)
            asr_exists = True
            asr_wordcount = len(asr.split())



        transcriptFile = os.path.join(transcriptDir,f'{sessname}_{b}.txt')
        if not os.path.isfile(transcriptFile): 
            transcript_wordcount = None
            transcript_exists = False
            transcript = ''
            print(f'--no transcript for block {b}')

        else:
            transcript = open(transcriptFile,'r').read()
            transcript = format_text_for_wer(transcript) 
            transcript_exists = True
            transcript_wordcount = len(transcript.split())
        
        if transcript_exists and asr_exists:
            print(f'TRANSCRIPT: {transcript}')
            print(f'ASR: {asr}')

            wer = jiwer.wer(transcript.split(), asr.split())
            wer_meas = jiwer.compute_measures(transcript.split(), asr.split())
            aligned, edit_ops =  align_words(transcript.split(), asr.split())
            aligned['block'] = b
            aligned_blockwise.append(aligned)
        else:
            wer = None
            wer_meas = {'mer':None,'substitutions':None, 'deletions':None, 'insertions':None }
        end = time.process_time()
        time_elapsed = end-start
        block_data.append([sessname, b, asr_exists, asr_wordcount, transcript_exists, transcript_wordcount, \
            wer,wer_meas['mer'],wer_meas['substitutions'], wer_meas['deletions'],wer_meas['insertions'],time_elapsed])
    aligned_blockwise = pd.concat(aligned_blockwise)
    aligned_blockwise.to_csv(os.path.join(sesspath,f'alignment_blockwise_{sessname}.csv'), index=False)

    # make Df to store blockwise metrics
    block_summary = pd.DataFrame(block_data, columns = ['session','block','asr_exists','asr_wordcount',' transcript_exists','transcript_wordcount',\
    'wer','mer','substitutions','deletions','insertions','time'])
    block_summary.to_csv(os.path.join(sesspath, f'blockwise_wer_{sessname}.csv') ) 
    # # get list of blocks with ASR
    # asrList=[]
    # for file in os.listdir(asrDir):
    #     if not file.endswith('.asr')
    #     base = re.sub('.asr', '', file)
    #     field = base.split('_')
    #     sg = field[len(field)-1]
    #     asrList.append( int(sg) )

    #     # get list of blocks with REV transcript
    # transcriptList=[]
    # for file in os.listdir(transcriptDir):
    #     if not file.endswith('.txt') or file.endswith('diarized.txt'): continue
    #     base = re.sub('.txt', '', file)
    #     field = base.split('_')
    #     sg = field[len(field)-1]
    #     transcriptList.append( int(sg) )