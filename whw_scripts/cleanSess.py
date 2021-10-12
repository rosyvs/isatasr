#!/usr/bin/env python3
# cleanSess.py  <sessionPath>
# read eer and chunks scores for session
# filter out all chunks that score less than threshold

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
parser.add_argument('--tag', default='_clean')
parser.add_argument('--results', default='results')
args = parser.parse_args()

sessDir = args.sesspath
sessName = os.path.basename(args.sesspath)
chunksDir = os.path.join(sessDir, 'test/wav/chunks/1')
eerFile = os.path.join(args.results, '%s.eer' % sessName)
scoreFile = os.path.join(args.results, '%s.cs' % sessName)

# read threshold
val = ''
for line in open(eerFile):
	line = line.strip()
	if line.startswith('threshold'):
		name,val = line.split()
		break
if not val:
	print('threshold value not found')
	exit(-1)
crit = float(val)

# read chunk score file and concatenate above threshold chunks
first = 1
for line in open(scoreFile):
	line = line.strip()
	targ,cnk,val = line.split()
	if float(val) < crit: continue

	cnk = re.sub('chunks-1-', '', cnk)
	infile = '%s/%s.wav' % (chunksDir, cnk)
	if first:
		combined = AudioSegment.from_wav(infile)
		first = 0
	else:
		next = AudioSegment.from_wav(infile)
		combined += next
combined.export('%s/%s_clean.wav' % (sessDir, sessName) , format='wav')
