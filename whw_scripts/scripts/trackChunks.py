#!/usr/bin/env python3
# python trackChunks.py <session path>
# read results/<sess>.cs
# find eer threshold and score each chunk
# print hyp and ref

import os
import re
import subprocess
import argparse

parser = argparse.ArgumentParser(description='print chunk scores')
parser.add_argument('sesspath', help='score file')
parser.add_argument('--results', default='results')
args = parser.parse_args()

sessDir = args.sesspath
sess = os.path.basename(sessDir)
trials = os.path.join(sessDir, 'test.txt')

# determine target/non-target for chunks
ref_class = {}
for line in open(trials):
	line = line.strip()
	val,target,chunk = line.split()
	file = os.path.basename(chunk)
	file = re.sub('.wav','',file)
	ref_class[file] = val

# read score for each chunk
scores = []
scoreFile = '%s/%s.cs' % (args.results, sess)
for line in open(scoreFile):
	line = line.strip()
	target,chunk,sscore = line.split()
	score = float(sscore)
	chunk = re.sub('chunks-1-','',chunk)
	ref = ref_class[chunk]
	scores.append( (score,chunk,ref) )
listsort = sorted(scores)

# find threshold
counts = []
n0 = 0
n1 = 0
for i in range(0,len(listsort)):
	if listsort[i][2] == '0':
		n0 += 1
	else:
		n1 += 1
	counts.append( (n0,n1) )
tot0 = n0
tot1 = n1
min = 0
minval = 1000
for i in range(0,len(counts)):
	err_dif = abs(counts[i][1] - (tot0 - counts[i][0]) )
	if err_dif < minval:
		minval = err_dif
		min = i

thresh = listsort[min][0]
print 'threshold: %f' % thresh

print '%s\t\t\t%s\t\t%s\t%s' %('name','score','ref','hyp')
for i in range(0,len(scores)):
	if scores[i][0] <= thresh:
		val = '0'

	else:
		val = '1'
	print '%s\t%f\t%s\t%s' % (scores[i][1], scores[i][0], scores[i][2], val)
