from pydub import AudioSegment
from pydub.playback import play
from playsound import playsound
import time
import operator
import sys
import os
from pathlib import Path
import re
import argparse
import pandas as pd

# load .blk file (this has 1 row per segment, start and end times) 
# get orig audio length
# get intervals not passed by VAD
# play these intervals


args_ctl =os.path.join('configs', 'sesstoREV_2021-10-04.txt') # this is the control file - list of paths to sessname rel to this script

# ctl has list of paths to audio to process
with open(args_ctl) as ctl:
    sesslist = (line.rstrip() for line in ctl) 
    sesslist = list(os.path.normpath(line) for line in sesslist if line)
for sesspath in sesslist: 
    print(f'Session path: {sesspath}')
    sessname = Path(sesspath).stem
    sesspath = os.path.join(sesspath)
    wavpath = os.path.join(sesspath, f'{sessname}.wav')
    sessAudio = AudioSegment.from_file(wavpath)
    wavdur = sessAudio.duration_seconds
    # get segments in block
    blkmapFile = os.path.join(sesspath,f'{sessname}.blk')
    # blkmap = pd.read_csv(blkmapFile, 
    #     sep='\s+', header=None, index_col=False, 
	# 	dtype={0:'int',1:'int',2:'float',3:'float'},
	# 	names = ['block','segment','start_s','end_s'])   

    blk=[]
    seg=[] 
    segStart = [] 
    segEnd = []  
    for line in open(blkmapFile):
        line = line.strip()
        if not line: continue
        blki, segi, segStarti, segEndi = line.split()
        blki = int(blki)
        segi = int(segi)
        segStarti = float(segStarti)
        segEndi= float(segEndi)
        blk.append(blki)
        seg.append(segi)
        segStart.append(segStarti)
        segEnd.append(segEndi)

        if segi == 0:
            emptyStart = [0]
            emptyEnd = [segStarti]
            print('first segment')
        if segi >0 and (segStarti > segEnd[-2]):
            emptyEnd.append(segStarti)
            emptyStart.append(segEnd[-2])
        emptySegments = zip(emptyStart, emptyEnd)
    for s,e in emptySegments:
        unvoiced = sessAudio[1000*s:1000*e]
        print(f'{sessname}')
        print(f'--playing unvoiced audio {s:.2f} to {e:.2f} seconds')
        play(unvoiced)

