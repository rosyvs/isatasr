#!/usr/bin/env python3
# asrBlks.py  <ctl file of session paths>
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
from google.protobuf.json_format import MessageToJson, MessageToDict
import json

client = speech.SpeechClient.from_service_account_file("isatasr-91d68f52de4d.json") 
asr_srate = 16000 # sampling rate to use for ASR, will resampel the input audio if necessary

args_ctl =os.path.join('configs', 'deepSample2_temp.txt') # list of session directories to run ASR on
# ctl has list of paths to sessions to process
with open(args_ctl) as ctl:
    sesslist = (line.rstrip() for line in ctl) 
    sesslist = list(line for line in sesslist if line)

for sesspath in sesslist: 
    print(f'sesspath: {sesspath}')
    sesspath = sesspath.strip()
    sessname = os.path.basename(sesspath)
    wavfile = os.path.join(sesspath, f'{sessname}.wav')
    asrDir = os.path.join(sesspath,'asr_segwise')
    jsonDir = os.path.join(sesspath,'JSON_segwise')

    # asrBlockDir = asrDir + '_reblocked' # segment-wise ASR will be concatenated to distinguish from ASR results run on entire block
    asrFullDir = os.path.join(sesspath,'asr_full') # where full session asr will be stored
    asrFullFile = os.path.join(asrFullDir,f"{sessname}.asr") # full session ASR results
    if os.path.exists(asrFullFile):
        open(asrFullFile, 'w').close() # clear file before appending
    blkmapFile = os.path.join(sesspath,f'{sessname}.blk')

    audio = AudioSegment.from_file(wavfile)
    srate = audio.frame_rate
    if not asr_srate == srate:
        audio = audio.set_frame_rate(asr_srate)
        srate = asr_srate
 


    # check if asr files already exist, if so, zip them up to make a backup then delete   
    os.makedirs(asrDir, exist_ok=True)
    # if not os.path.exists(asrBlockDir):
    #     os.makedirs(asrBlockDir)
    os.makedirs(asrFullDir, exist_ok=True)
    
    # check if asr file already existed, and backup if so
    if os.path.isfile(asrDir):
        now = datetime.now()
        datestr = now.strftime("%d-%m-%Y_%H%M%S")
        zipfile = shutil.make_archive(base_name =os.path.join(asrDir,f'backup_{datestr}'), 
        format='zip', 
        root_dir = asrDir,
        base_dir = asrDir)
        print(f"ASR already existed. Backed the file up to {zipfile}") 
        os.remove(asrfile)
    
    os.makedirs(jsonDir, exist_ok=True)


    for line in open(blkmapFile):
        line = line.strip()
        if not line: continue
        b, s, segStart, segEnd = line.split()
        b = int(b)
        s = int(s)
        segStart = float(segStart)
        segEnd= float(segEnd)
        print(f'Processing segment: {s}')

        # extract segment and send only this to ASR
        seg_audio = audio[segStart*1000:segEnd*1000]

        # EXPERIMENT: normalise segment volume before passing to ASR
        seg_audio = effects.normalize(seg_audio)
        #\EXPERIMENT

        # bytes = io.BytesIO()
        # audio.export(bytes)
        bytes=seg_audio.raw_data
        fullresult, best = transcribeExtra_bytestream(bytes, client, srate)
        result_json = MessageToDict(fullresult._pb)


        ## write segmentwise ASR result
        # fullresult
        jsonFile = os.path.join(jsonDir, f"{sessname}_{s}.json")

        with open(jsonFile, "w") as jf:
            json.dump(result_json, jf, indent=4)
        # just transcript words
        asrfile = os.path.join(asrDir, f"{sessname}_{s}.asr")
        with open(asrfile,'w') as outfile:
            outfile.write(best + '\n')

        # # append segment ASRresults to the corresponding block
        # asrblockfile = os.path.join(asrBlockDir, f"{sessname}_{b}.asr")
        # with open(asrblockfile,'a') as outfile:
        #     outfile.write(res + '\n')

        # append all ASR results to a single file
        with open(asrFullFile,'a') as outfile:
            outfile.write(best + '\n')
