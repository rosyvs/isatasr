# python mkTrials.py <path to session>
# generate test.txt, the target hyp pairs and ref label

import os
import re
import subprocess
import argparse

parser = argparse.ArgumentParser(description='mk verification test set')
parser.add_argument('sess_path', help='session path')
parser.add_argument('--filter', default='y')
parser.add_argument('--seg', default='chunks')
parser.add_argument('--video', default='omit')
parser.add_argument('--minlen', default='0.9')
args = parser.parse_args()

sessDir = args.sess_path
sessName = os.path.basename(args.sess_path)
min_bytes = float(args.minlen) * 32000

tagFile = os.path.join(sessDir, '%s.cnk' % sessName)
targWav = 'targets/1/%s.wav' % sessName

trialsFile =  os.path.join(sessDir, 'test.txt')
trF = open(trialsFile, 'w')

count = 0
count_omit = 0
count_short = 0
count_video = 0

if not  os.path.exists(tagFile):
	print tagFile, 'not found'
	exit(-1)
for line in open(tagFile):
	line = line.strip()
	file,tag = line.split()
	tag = tag.lower()

	# check segment length
	filepath = '%s/test/wav/%s/1/%s' % (sessDir, args.seg, file)
	fbytes = os.stat(filepath).st_size
	if fbytes < min_bytes:
		count_short += 1
		continue

	if tag.find('u') != -1:
		count_omit += 1
		continue
	# video
	elif tag.find('v') != -1:
		count_video += 1
		continue

	else:
		tstWav = '%s/1/%s' % (args.seg, file)
		# target
		if tag.find('t') != -1:
			cl = '1'
		else:
			cl = '0'
		trF.write('%s %s %s\n' % (cl,targWav, tstWav))
		count += 1

print '%d trials' % count
print '%d omit' % count_omit
print '%d short' % count_short
print '%d video' % count_video
