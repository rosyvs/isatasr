#!/usr/bin/env python3
# tagChunks.py  --root <sessions root> --sesspath <session path>
# sessions root is dir containing a set of session dirs
# find session with unannotated chucks
# play files in chunks dir for tagging
# input from stdin a label for file after playing
# output to <sess>/chunks.tag

from pydub.utils import db_to_float
from pydub import AudioSegment
from playsound import playsound
import time
import operator
import sys
import os
import re
import argparse

parser = argparse.ArgumentParser(description='tag chunk files')
parser.add_argument('--root', default='data/MathLessons/sess')
parser.add_argument('--sesspath', default='')
parser.add_argument('--preview', default='10')
args = parser.parse_args()

tags = ['1','2','3','4','5','b','B','n','N']

def tag_file(file):

	while 1:
		print(file)
		# play chunk
		playsound(file)

		print('>', end='', flush=True)
		line = sys.stdin.readline()
		line = line.strip()
		if not line: continue
		if line.startswith('-'):
			break
		elif line.startswith('h'):
			print('b - background speech moderate')
			print('B - background speech loud')
			print('h - help')
			print('n - noise moderate')
			print('N - noise loud')
			print('q - quit')
			print('[12345] - speaker numbers')
			continue
		elif line.startswith('q'):
			exit(-1)
		else:
			for i in range(len(line)):
				if not line[i] in tags:
					if line[i] == ',': continue
					print('unknown code: ',line[i])
					return ''
			break
	return line.lower()


def file_len(fname):
	i = -1
	with open(fname) as f:
		for i, l in enumerate(f):
			pass
	return i + 1


# get sorted list of sessions
sesslist = []
if args.root:
	for file in os.listdir(args.root):
		sesslist.append(file)
	sesslist.sort()
elif args.sesspath:
	sesslist.append(args.sesspath)

# dur in msec
pdur = int(args.preview) * 1000

# find first session that isn't done with tagging
for sess in sesslist:
	if args.root:
		sessDir = os.path.join(args.root, sess)
	else:
		sessDir = sess
	tagfile = os.path.join(sessDir, 'chunks.tag')
	#segsDir = os.path.join(sessDir, 'test/wav/segments/1')
	segsDir = os.path.join(sessDir, 'segments')
	#chunksDir = os.path.join(sessDir, 'test/wav/chunks/1')
	chunksDir = os.path.join(sessDir, 'chunks')

	name = os.path.basename(sess)

	# get list of chunks
	chunklist = []
	for file in os.listdir(chunksDir):
		if not file.endswith('.wav'): continue
		base = re.sub('.wav', '', file)
		field = base.split('_')
		ck = field[len(field)-1]
		sg = field[len(field)-2]
		chunklist.append( (int(sg), int(ck)) )

	# get already tagged files
	count = 0
	if os.path.exists(tagfile):
		count = file_len(tagfile)
		# if all done
		if len(chunklist) <= count: continue

	chunklist.sort(key = operator.itemgetter(0, 1))

	# get seg durations in secs
	seglen = []
	ps = 0
	for i in range(len(chunklist)):
		segnum = chunklist[i][0]
		if segnum > ps:
			seglen.append(cnknum)
			ps = segnum
		cnknum = chunklist[i][1]
	seglen.append(cnknum)

	# open output tag file
	tagF = open(tagfile, 'a')

	i = count
	lseg = -1
	while i < len(chunklist):
		segnum = chunklist[i][0]
		cnknum = chunklist[i][1]

		# if new segment play segment wav file
		if segnum != lseg:
			print('preview')
			segwavfile = '%s/%s_%s.wav' % (segsDir,name,segnum)
			segwav = AudioSegment.from_wav(segwavfile)
			dur = pdur
			if dur > (seglen[segnum] * 1000):
				dur = seglen[segnum] * 1000
			prev_audio = segwav[0:dur]
			outx = prev_audio.export('xxtmp.wav', format ="wav")
			outx.close()
			playsound('xxtmp.wav')
			time.sleep(1.0)

		# chunk to tag
		file = '%s/%s_%d_%d.wav' % (chunksDir, name, segnum, cnknum)

		tag = tag_file(file)
		if tag[0] == '-':
			i -= 1
			if i < 0: i=0
			continue

		tagF.write('%s_%d_%d.wav %s\n' % \
		 (name, chunklist[i][0], chunklist[i][1], tag))
		i += 1
		lseg = segnum
	tagF.close()

if os.path.exists('xxtmp.wav'): os.remove('xxtmp.wav')
