#!/usr/bin/env python3
# python findEer.py <session path>
# read scores_test output by talkback.sh
# find eer threshold and score each segment

import os
import re
import subprocess
import argparse

parser = argparse.ArgumentParser(description='mk verification test set')
parser.add_argument('sess', help='session path')
parser.add_argument('--scores', default='results')
parser.add_argument('--seg', default='chunks')
args = parser.parse_args()

sessDir = args.sess
trials = os.path.join(sessDir, 'test.txt')
name = os.path.basename(sessDir)

# determine target/non-target for segments
seg_class = {}
for line in open(trials):
	line = line.strip()
	val,target,seg = line.split()
	file = os.path.basename(seg)
	file = re.sub('.wav','',file)
	seg_class[file] = val

# read score for each segment
scores = []
if args.seg == 'chunks':
	scoreFile = os.path.join(args.scores, name + '.cs')
else:
	scoreFile = os.path.join(args.scores, name + '.ss')
for line in open(scoreFile):
	line = line.strip()
	target,seg,sscore = line.split()
	score = float(sscore)
	if args.seg == 'chunks':
		seg = re.sub('chunks-1-','',seg)
	else:
		seg = re.sub('segments-1-','',seg)
	val = seg_class[seg]
	scores.append( (score,seg,val) )
scores.sort()

# find threshold
counts = []
n0 = 0
n1 = 0
for i in range(0,len(scores)):
	if scores[i][2] == '0':
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
threshold = scores[min][0]

for i in range(0,len(scores)):
	print(scores[i][0], scores[i][1], scores[i][2])
	if i == min:
		print('___________________________')

# compute error rate
err_cnt = counts[min][1] + (tot0 - counts[min][0])
eer = float(err_cnt)/float(len(counts))
print('eer=', eer)
with open('%s/%s.eer' % (args.scores,name),'w') as outfile:
	outfile.write('threshold %f\n' % threshold)
	outfile.write('eer %f\n' % eer)
