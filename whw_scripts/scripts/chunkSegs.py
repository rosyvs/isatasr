# chunkSegs.py  <sessionPath>
# split the segments into fix lengthed chunks

import pydub
from pydub import AudioSegment
from pydub.utils import make_chunks
import shutil
import sys
import os
import re
import subprocess
import argparse

parser = argparse.ArgumentParser(description='check files')
parser.add_argument('sess')
parser.add_argument('--cklen', default='120.0')
parser.add_argument('--smin', default='2.0')
parser.add_argument('--segdir', default='segments')
parser.add_argument('--cnkdir', default='chunks')
args = parser.parse_args()

#wf = wave.open(args.wav, 'rb')
#num_channels = wf.getnchannels()
#assert num_channels == 1
#sample_width = wf.getsampwidth()
#assert sample_width == 2
#sample_rate = wf.getframerate()
#assert sample_rate == 16000
#pcm_data = wf.readframes(wf.getnframes())

chunk_len_sec = float(args.cklen)
seg_min_bytes = float(args.smin) * 32000

sessDir = args.sess
basename = os.path.basename(args.sess)
#segDir = '%s/test/wav/segments/1' % sessDir
segDir = '%s/%s' % (sessDir, args.segdir)
#chunkDir = '%s/test/wav/chunks/1' % sessDir
chunkDir = '%s/%s' % (sessDir, args.cnkdir)
if not os.path.exists(chunkDir):
	os.makedirs(chunkDir)

#list and sort segments
Segs = []
for file in os.listdir(segDir):
	# file name is <sess>_<seg#>.wav
	field = file.split('_')
	num = re.sub('.wav', '', field[len(field)-1])
	Segs.append(int(num))
Segs.sort()

# split each seg into 1 sec chunks
for num in Segs:
	segName = '%s_%d' % (basename, num)
	infile = '%s/%s.wav' % (segDir, segName)

	# check seg length, don't split if < smin secs
	fbytes = os.stat(infile).st_size
	if fbytes < seg_min_bytes:
		chunk_name = '%s/%s_%d.wav' % (chunkDir, segName, 0)
		shutil.copyfile(infile, chunk_name)
		continue

	myaudio = AudioSegment.from_file(infile , "wav") 
	chunk_length_ms = int(1000 * chunk_len_sec) # pydub calculates in msec
	chunks = make_chunks(myaudio, chunk_length_ms) #Make chunks of one sec

	#Export all of the individual chunks as wav files
	for i, chunk in enumerate(chunks):
                chunk_name = '%s/%s_%d.wav' % (chunkDir, segName, i)
                chunk.export(chunk_name, format="wav")
	# if last chunk < 0.75 sec, join to prev chunk
	min_bytes = 0.75 * 32000
	fbytes = os.stat(chunk_name).st_size
	if fbytes < min_bytes:
		c1_name = '%s/%s_%d.wav' % (chunkDir, segName, len(chunks)-2)
		c2_name = '%s/%s_%d.wav' % (chunkDir, segName, len(chunks)-1)
	
		c1 = AudioSegment.from_wav(c1_name)
		c2 = AudioSegment.from_wav(c2_name)
		c3 = c1 + c2
		c3.export(c1_name, format="wav")
		os.remove(c2_name)
