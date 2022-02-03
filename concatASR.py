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
from natsort import natsorted 


args_ctl =os.path.join('configs', '4SG.txt') # list of session directories to run ASR on
# ctl has list of paths to sessions to process
with open(args_ctl) as ctl:
    sesslist = (line.rstrip() for line in ctl) 
    sesslist = list(line for line in sesslist if line)

for sesspath in sesslist: 
    print(f'sesspath: {sesspath}')
    sesspath = sesspath.strip()
    sessname = os.path.basename(sesspath)
    asrDir = os.path.join(sesspath,'asr_segwise')
    asrFullDir = os.path.join(sesspath,'asr_full') # where full session asr will be stored
    asrFullFile = os.path.join(asrFullDir,f"{sessname}.asr") # full session ASR results
    if not os.path.exists(asrFullDir):
        os.makedirs(asrFullDir)
    # loop over asr results
    asr_list = [f for f in os.listdir(asrDir) if f.endswith('.asr')]
    n_asr = len(asr_list)
    # sort by block/segment number
    asr_list = natsorted(asr_list)
    asr_fullsess = []

    for f in asr_list:
        asrFile = os.path.join(asrDir,f)
        if not os.path.isfile(asrFile): 
            asr_wordcount = None
            asr_exists = False
            asr = ''
        else: 
            asr = open(asrFile,'r').read()
            asr = format_text_for_wer(asr)
        asr_fullsess.append(asr)

        # append all ASR results to a single file
    with open(asrFullFile,'w') as outfile:
        outfile.write('\n'.join(asr_fullsess))

