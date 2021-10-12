#!/usr/bin/env python3
# cpTags.py  <sessionRoot>
# get tagged cnk files from tags dir
# remove duplicate records
# write to session dir

import shutil
import sys
import os
import re
import argparse

parser = argparse.ArgumentParser(description='cp chunk tag files')
parser.add_argument('root')
parser.add_argument('--tags', default='tags')
args = parser.parse_args()

for file in os.listdir(args.tags):
	if not file.endswith('.cnk'): continue
	name = re.sub('.cnk', '', file)
	sessDir = os.path.join(args.root, name)
	if not os.path.exists(sessDir):
		print("can't find session %s" % sessDir)
		continue

	dstF = open( os.path.join(sessDir, file), 'w')
	prevFile = ''
	prevTag = ''
	for line in open(os.path.join(args.tags, file)):
		line = line.strip()
		field=line.split()
		if len(field) != 2:
			print('bad record: %s' % line)
			continue
		file = field[0]
		tag = field[1]
		
		if not prevFile:
			prevFile = file
			prevTag = tag
			continue

		if file != prevFile:
			# remove commas
			prevTag = re.sub(',', '', prevTag)
			# write to destination
			dstF.write('%s %s\n' % (prevFile, prevTag))
		prevFile = file
		prevTag = tag
	if prevFile:
		# remove commas
		prevTag = re.sub(',', '', prevTag)
		# write to destination
		dstF.write('%s %s\n' % (prevFile, prevTag))
	dstF.close()
