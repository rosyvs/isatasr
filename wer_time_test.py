import os
import re
from numpy.core.shape_base import block
import pandas as pd
import jiwer 
import time
import string
import Levenshtein

wer_test_files = 'wer_time_testing'
sessname = 'test'

# # JIWER has some nice formatting options
# transform = jiwer.Compose([
#     jiwer.ToLowerCase(),
#     jiwer.RemovePunctuation()
# ]) 
block_data = []

for b in [10,100]:
    start = time.process_time()
    asrFile = os.path.join(wer_test_files,f'test{b}.asr')
    if not os.path.isfile(asrFile): 
        asr_wordcount = 0
        asr_exists = False
    else: 
        asr = open(asrFile,'r').read().replace('\n',' ')
        asr = re.sub('\s+',' ',asr)
        asr = [word.strip(string.punctuation) for word in asr.split()]# remove punc except within words
        asr_wordcount = len(asr)
        asr = ' '.join(asr)
        asr_exists = True



    transcriptFile = os.path.join(wer_test_files,f'test{b}.txt')
    if not os.path.isfile(transcriptFile): 
        transcript_wordcount = 0
        transcript_exists = False
    else:
        transcript = open(transcriptFile, 'r').readlines()
        transcript = open(transcriptFile,'r').read().replace('\n',' ')
        transcript = re.sub('\s+',' ',transcript)
        transcript = [word.strip(string.punctuation) for word in transcript.split()]# remove punc except within words
        transcript_wordcount = len(transcript)
        transcript = ' '.join(transcript)
        transcript_exists = True
    
    if transcript_exists and asr_exists:
        print(f'TRANSCRIPT: {transcript}')
        print(f'ASR: {asr}')
        wer = jiwer.wer(transcript, asr)
        wer_meas = jiwer.compute_measures(transcript, asr)
        edit_ops = pd.DataFrame(Levenshtein.editops(transcript, asr), columns = ['operation','transcript_ix','asr_ix'])
    else:
        wer = -1
    end = time.process_time()
    time_elapsed = end-start
    block_data.append([sessname, b, asr_exists, asr_wordcount, transcript_exists, transcript_wordcount, \
        wer,wer_meas['mer'],wer_meas['substitutions'], wer_meas['deletions'],wer_meas['insertions'],time_elapsed])

# make Df to store blockwise metrics
block_summary = pd.DataFrame(block_data, columns = ['session','block','asr_exists','asr_wordcount',' transcript_exists','transcript_wordcount',\
    'wer','mer','substitutions','deletions','insertions','time'])
block_summary.to_csv(os.path.join('test_wer.csv'))