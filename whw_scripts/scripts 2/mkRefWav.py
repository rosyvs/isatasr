#!/usr/bin/env python3
# mkRefWav.py  <sessionPath>
# filter out all chunks not containing target

import pydub
from pydub import AudioSegment
import shutil
import sys
import os
import re
import subprocess
import argparse

parser = argparse.ArgumentParser(description='clean wav file')
parser.add_argument('sesspath')
parser.add_argument('--ext', default='ref')
args = parser.parse_args()

sessDir = args.sesspath
sessName = os.path.basename(args.sesspath)
chunksDir = os.path.join(sessDir, 'test/wav/chunks/1')
tagFile = os.path.join(sessDir, '%s.cnk' % sessName)

# read tag file and concatenate above threshold chunks
first = 1
for line in open(tagFile):
	line = line.strip()
	cnk,tag = line.split()
	if tag.find('t') == -1: continue

	infile = '%s/%s' % (chunksDir, cnk)
	if first:
		combined = AudioSegment.from_wav(infile)
		first = 0
	else:
		next = AudioSegment.from_wav(infile)
		combined += next
combined.export('%s/%s_%s.wav' % (sessDir, sessName,args.ext) , format='wav')
