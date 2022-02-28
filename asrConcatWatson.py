from __future__ import absolute_import
from pydub.audio_segment import AudioSegment, effects
import os
import io
import re
import argparse
import pandas as pd
import math
from datetime import datetime
import shutil
from rosy_asr_utils import *
import WatsonUtils
import json

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Concatenate utterances before transcribing
# Split results back to utterances using word-level timing  
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

config = '/Users/roso8920/Dropbox (Emotive Computing)/iSAT/WatsonTranscription/real.config'
asr_srate = 16000 # sampling rate to use for ASR, will resampel the input audio if necessary

args_ctl =os.path.join('configs', 'deepSample2.txt') # list of session directories to run ASR on
# ctl has list of paths to sessions to process
with open(args_ctl) as ctl:
    sesslist = (line.rstrip() for line in ctl) 
    sesslist = list(line for line in sesslist if line)

for sesspath in sesslist: 
    print(f'sesspath: {sesspath}')
    sesspath = sesspath.strip()
    sessname = os.path.basename(sesspath)
    wavfile = os.path.join(sesspath, f'{sessname}.wav')
    asrDir = os.path.join(sesspath,'asr_watson_concat_segwise')
    # asrBlockDir = asrDir + '_reblocked' # segment-wise ASR will be concatenated to distinguish from ASR results run on entire block
    asrFullDir = os.path.join(sesspath,'asr_watson_concat_full') # where full session asr will be stored
    jsonDir = os.path.join(sesspath,'JSON_watson_concat')

    asrFullFile = os.path.join(asrFullDir,f"{sessname}.asr") # full session ASR results
    if os.path.exists(asrFullFile):
        open(asrFullFile, 'w').close() # clear file before appending
    blkmapFile = os.path.join(sesspath,f'{sessname}.blk')

    audio = AudioSegment.from_file(wavfile)
    srate = audio.frame_rate
    if not asr_srate == srate:
        audio = audio.set_frame_rate(asr_srate)
        srate = asr_srate

    os.makedirs(asrDir, exist_ok=True)
    # if not os.path.exists(asrBlockDir):
    #     os.makedirs(asrBlockDir)
    os.makedirs(asrFullDir, exist_ok=True)
    os.makedirs(jsonDir, exist_ok=True)

    concat_audio = AudioSegment.empty()
    concat_timings = {}
    concatStart = 0
    for line in open(blkmapFile):
        line = line.strip()
        if not line: continue
        b, s, segStart, segEnd = line.split()
        b = int(b)
        s = int(s)
        segStart = float(segStart)
        segEnd= float(segEnd)

        # extract segment 
        seg_audio = audio[segStart*1000:segEnd*1000]

        seg_audio = effects.normalize(seg_audio)

        concat_audio +=seg_audio
        concatEnd = concatStart + segEnd - segStart
        concat_timings[s] = (concatStart,concatEnd)
        concatStart = concatEnd # increment timing counter for next segment


    bytes=concat_audio.raw_data

    print(f'Running ASR for {s} segments conncatenated...')
    res = WatsonUtils.WatsonASR_bytes(bytes, config, f'l16; rate={srate}; endianness=little-endian')

    result = json.loads(res.text)

    # fullresult
    jsonFile = os.path.join(jsonDir, f"{sessname}.json")

    with open(jsonFile, "w") as jf:
        json.dump(result, jf, indent=4)

    # asrtext = result.get('results')
    asrtext = ""

    # consume results
    while bool(result.get('results')):
        asrtext = result.get('results').pop().get('alternatives').pop().get('transcript')+asrtext[:]
    print(asrtext)
    # append all ASR results to a single file
    with open(asrFullFile,'a') as outfile:
        outfile.write(asrtext + '\n')

    # get words and timings
    result = json.loads(res.text)
    word_timings =  [r['alternatives'][0]['timestamps'] for r in result['results']]
    word_timings = [elm for sublist in word_timings for elm in sublist]

    for s, (start, end) in concat_timings.items():

        seg_words = [w[0] for w in word_timings if w[2]>start and w[1]<end]
        print((s, ' '.join(seg_words)))

        # write segmentwise ASR result
        asrfile = os.path.join(asrDir, f"{sessname}_{s}.asr")
        with open(asrfile,'w') as outfile:
            outfile.write(' '.join(seg_words) + '\n')

        # # append segment ASRresults to the corresponding block
        # asrblockfile = os.path.join(asrBlockDir, f"{sessname}_{b}.asr")
        # with open(asrblockfile,'a') as outfile:
        #     outfile.write(res + '\n')



