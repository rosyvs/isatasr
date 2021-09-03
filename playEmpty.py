#!/usr/bin/env python3
# playEmpty.py <path to session>

from pydub import AudioSegment
from playsound import playsound
import time
import operator
import sys
import os
import re
import argparse

parser = argparse.ArgumentParser(description='tag chunk files')
parser.add_argument('sess')
args = parser.parse_args()

asrDir = os.path.join(args.sess, 'asr')
segDir = os.path.join(args.sess, 'segments')

empty = []
for file in os.listdir(asrDir):
	asrfile = os.path.join(asrDir,file)
	fbytes = os.stat(asrfile).st_size
	if fbytes < 2:
		empty.append(file)

empty.sort()
for f in empty:
	wav = os.path.join(segDir, f)
	wav = re.sub('.asr','.wav',wav)
	print(wav)
	playsound(wav)
	print('>', end='', flush=True)
	line = sys.stdin.readline()
