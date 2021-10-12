# mp2wav.py <mp4 file>
# extract audio track and downsample to 16k

import os
import re
import argparse

parser = argparse.ArgumentParser(description='extract wav')
parser.add_argument('--indir')
parser.add_argument('--outdir')
args = parser.parse_args()

for mp in os.listdir(args.indir):
	mp = mp.strip()
	if mp.endswith('.m4a'):
		wavFile = os.path.join(args.outdir, re.sub('.m4a','.wav',mp))
	elif mp.endswith('.mp4'):
		wavFile = os.path.join(args.outdir, re.sub('.mp4','.wav',mp))
	elif mp.endswith('.MP4'):
		wavFile = os.path.join(args.outdir, re.sub('.MP4','.wav',mp))
	elif mp.endswith('.mp3'):
		wavFile = os.path.join(args.outdir, re.sub('.mp3','.wav',mp))
	else:
		continue
	mpFile = os.path.join(args.indir,mp)
	cmd = 'ffmpeg -i %s -ac 1 -ar 16000 %s' % (mpFile, wavFile)
	os.system(cmd)

