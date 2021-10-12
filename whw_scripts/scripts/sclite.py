# python sclite.py

import os
import subprocess
import string
import re
import argparse

parser = argparse.ArgumentParser(description='score session')
parser.add_argument('inDir')
parser.add_argument('--tmp', default='tmp', help='Temporary Files Directory')
parser.add_argument('--bin', default='bin', help='Binaries Directory')
args = parser.parse_args()

for file in os.listdir(args.inDir):
	if not file.endswith('.hyp'): continue

	hyp_file = os.path.join(args.inDir, file)
	ref_file = re.sub('.hyp','.ref',hyp_file)

	# compare ref and hyp strings with sclite
	# this generate tmp_pra file
	cmd = '%s/sclite  -l 5000 -h %s -r %s -i wsj -o pralign > /dev/null' % \
		(args.bin, hyp_file, ref_file)
	subprocess.call(cmd, shell=True)

#	# get aligned ref string from .pra file
#	for line in open(os.path.join(args.tmp, 'tmp_hyp.pra'), 'r'):
#		if line.startswith('REF:  '):
#			line = line.strip()
#			line = re.sub('REF:', '', line)
#			wrds = line.split()
#			refs=' '.join(i for i in wrds if not i.startswith('*'))
#
#	praFile = os.path.join(args.pra, '%s.pra' % sess)
#	with open(praFile, 'w') as outfile:
#		outfile.write(refs + '\n')
