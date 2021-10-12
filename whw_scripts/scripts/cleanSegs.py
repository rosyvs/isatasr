#!/usr/bin/env python3
# cleanSegs.py  <sessionPath>
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
parser.add_argument('--ext', default='_clean')
parser.add_argument('--results', default='results')
parser.add_argument('--outdir', default='clean_segs')
parser.add_argument('--tagfile', default='')
args = parser.parse_args()

sessDir = args.sesspath
sessName = os.path.basename(args.sesspath)
chunksDir = os.path.join(sessDir, 'test/wav/chunks/1')
eerFile = os.path.join(args.results, '%s.eer' % sessName)
scoreFile = os.path.join(args.results, '%s.cs' % sessName)
if not os.path.exists(args.outdir):
	os.makedirs(args.outdir)

# read tags to set target/non-target
if args.tagfile:
	tags = {}
	for line in open(os.path.join(sessDir,'%s.cnk' % sessName)):
		line = line.strip()
		cnk,tag = line.split()
		cnk = re.sub('.wav','',cnk)
		if tag.find('t') != -1:
			tag = 't'
		else:
			tag = 'n'
		tags[cnk] = tag
else:
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
curseg = ''
for line in open(scoreFile):
	line = line.strip()
	targ,cnk,val = line.split()
	cnk = re.sub('chunks-1-', '', cnk)

	if args.tagfile:
		if tags[cnk] != 't': continue
	else:
		if float(val) < crit: continue

	infile = '%s/%s.wav' % (chunksDir, cnk)

	field = cnk.split('_')
	cnknum = field[len(field)-1]
	segnum = field[len(field)-2]
	newseg = field[0]
	for i in range(1,len(field)-1):
		newseg += '_' + field[i]

	# if starting new segment
	if newseg != curseg:
		if curseg:
			# output current segment
			combined.export('%s/%s_clean.wav' % \
				(args.outdir, curseg) , format='wav')
		combined = AudioSegment.from_wav(infile)
		curseg = newseg
	else:
		next = AudioSegment.from_wav(infile)
		combined += next
combined.export('%s/%s_clean.wav' % (sessDir, curseg) , format='wav')
