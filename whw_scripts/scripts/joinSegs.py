# joinSegs.py  <sessionpath>
# join segs into single wav file named ex.wav

import pydub
from pydub import AudioSegment
from pydub.utils import make_chunks
import shutil
import sys
import os
import re
import subprocess
import argparse

parser = argparse.ArgumentParser(description='join files')
parser.add_argument('sesspath')
args = parser.parse_args()

sessDir = args.sesspath
sessName = os.path.basename(sessDir)
segDir = '%s/test/wav/segments/1' % sessDir

#list and sort segments
Segs = []
for file in os.listdir(segDir):
	# file name is <sess>_<seg#>.wav
	field = file.split('_')
	num = re.sub('.wav', '', field[len(field)-1])
	Segs.append(int(num))
if len(Segs) < 1:
	print args.sesspath, 'no segments'
	exit(-1)
Segs.sort()

# join segments
combined = AudioSegment.from_wav('%s/%s_0.wav' % (segDir,sessName))
for num in range(1,len(Segs)):
	segName = '%s_%d' % (sessName, Segs[num])
	infile = '%s/%s.wav' % (segDir, segName)
	next = AudioSegment.from_wav(infile)
	combined += next
combined.export('%s/%s_strip.wav' % (sessDir, sessName) , format='wav')
