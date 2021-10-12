#!/usr/bin/env python3
# python sortEer.py <session path>
# sort sessions by classification error rate

import os
import re
import subprocess
import argparse

parser = argparse.ArgumentParser(description='sort eer results')
parser.add_argument('--results', default='results')
args = parser.parse_args()

def file_len(fname):
	i = -1
	with open(fname) as f:
		for i, l in enumerate(f):
			pass
	return i + 1

# list all .eer files
scores = []
for file in os.listdir(args.results):
	file = file.strip()
	if not file.endswith('.eer'): continue
	name = re.sub('.eer','',file)
	scorefile = '%s/%s.cs' % (args.results,name)
	count = file_len(scorefile)
	for line in open('%s/%s' % (args.results,file)):
		rate = float(line.strip())
	scores.append( (rate,name,count) )
listsort = sorted(scores)
for s in listsort:
	print(s[0],s[1],s[2])

