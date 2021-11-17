#!/usr/bin/env python3
# playBlocks.py <ctl file>

from pydub import AudioSegment
from playsound import playsound
import time
import operator
import sys
import os
import re
import argparse

parser = argparse.ArgumentParser(description='tag chunk files')
parser.add_argument('ctl')
args = parser.parse_args()

for file in open(args.ctl):
    file = file.strip()
    blocksDir = os.path.dirname(file)
    blkname = re.sub('.wav','', os.path.basename(file))
    field = blkname.split('_')
    name = '_'.join( field[i] for i in range(len(field)-1)) 
    blk = field[len(field)-1]
    asrDir = re.sub('blocks$','asr',blocksDir)
    segDir = re.sub('blocks$','segments',blocksDir)
    praDir = re.sub('blocks$','pra',blocksDir)
    sessDir = re.sub('blocks$','',blocksDir)

    # print pra alignment
    prafile = os.path.join(praDir,'%s_%s.hyp.pra' % (name,blk))
    for line in open(prafile):
        if line.startswith('REF:'):
            print(line)
        elif line.startswith('HYP:'):
            print(line)

    # get segments in block
    blkmap = os.path.join(sessDir,'%s.blkmap' % name)
    for line in open(blkmap):
        line = line.strip()
        if not line: continue
        segs,blks = line.split()
        if blks == blk: break
    sgl = segs.split(',')
    resp = '-'
    while resp.startswith('-'):
        for sg in sgl:
            sg_wav = os.path.join(segDir,'%s_%s.wav' % (name,sg))
            sg_asr = os.path.join(asrDir,'%s_%s.asr' % (name,sg))
            asr = ''
            for line in open(sg_asr):
                line + line.strip()
                asr += line + ' '
            print(sg, asr)
            playsound(sg_wav)
            time.sleep(1.0)

        print('>', end='', flush=True)
        resp = sys.stdin.readline()
    if resp.startswith('q'):
        exit(-1)
