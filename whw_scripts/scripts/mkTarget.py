#!/usr/bin/env python3
# python mkTarget.py <session path>
# read chunk tags
# find clean segment 2sec <= length <= 5 sec

import os
import re
from pydub import AudioSegment
import argparse

parser = argparse.ArgumentParser(description='get ref segment')
parser.add_argument('sesspath', help='score file')
parser.add_argument('--tgtlen', default='3')
parser.add_argument('--minlen', default='1')
args = parser.parse_args()

min_seglen = int(args.minlen)
sessDir = args.sesspath
sessName = os.path.basename(sessDir)
chunksDir = os.path.join(sessDir, 'test/wav/chunks/1')
targDir = os.path.join(sessDir, 'test/wav/targets/1')
sess = os.path.basename(sessDir)
tagfile = os.path.join(sessDir, '%s.cnk' % sess)

segs = []
curseg = ''
st = -1
ed = -1
# find spans of clean speech
for line in open(tagfile):
	line = line.strip()
	file,tags = line.split()
	file = re.sub('.wav','',file)
	field = file.split('_')
	cnk = field[len(field)-1]
	seg = field[len(field)-2]

	# new segment
	if seg != curseg:
		# save seg stats
		if st > -1:
			seglen = ed - st +1
			segs.append( (seglen, st,curseg) )
		st = -1
		ed = -1
		curseg = seg

	# check tags for current chunk
	if tags.find('t') != -1:
		if tags.find('b') != -1: clean = 0
		elif tags.find('B') != -1: clean = 0
		elif tags.find('n') != -1: clean = 0
		elif tags.find('N') != -1: clean = 0
		else: clean = 1
	else:
		clean = 0

	if clean:
		ed = int(cnk)
		if st == -1:
			st = int(cnk)
	else:
		if st > -1:
			seglen = ed - st +1
			segs.append( (seglen, st,curseg) )
			st = -1

segs.sort(reverse=True)

# find target of specified length
# start with longest segments
tgt = []
need = int(args.tgtlen)
for i in range(len(segs)):
	cnt = int(segs[i][0])
	st = int(segs[i][1])
	seg = segs[i][2]

	num = min(cnt, need)
	for i in range(num):
		tgt.append((seg,st + i))
	need -= num
	if need == 0: break


if len(tgt) < 1:
	print('no target in %s' % sessName)
elif len(tgt) < 3:
	print('short target in %s' % sessName)
else:
	if not os.path.exists(targDir): os.makedirs(targDir)
	# join chunks to create target file
	combined = AudioSegment.from_wav('%s/%s_%s_%d.wav' % \
			(chunksDir,sessName,tgt[0][0],tgt[0][1]))
	for num in range(1,3):
		infile = '%s/%s_%s_%d.wav' % \
			(chunksDir,sessName,tgt[num][0],tgt[num][1])
		next = AudioSegment.from_wav(infile)
		combined += next
	combined.export('%s/%s.wav' % (targDir, sessName) , format='wav')
