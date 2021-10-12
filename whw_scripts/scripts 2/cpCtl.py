# cpCtl.py  <ctl file>
# cp sessions in list into structure for annotation

import shutil
import sys
import os
import re
import argparse

parser = argparse.ArgumentParser(description='cpCtl')
parser.add_argument('ctl')
parser.add_argument('--inRoot', default='corpora/orf/g1')
parser.add_argument('--outRoot', default='set2/Orf/corpora/orf/g1')
args = parser.parse_args()

if not os.path.exists(args.outRoot):
	os.makedirs(args.outRoot)

for sess in open(args.ctl):
	sess = sess.strip()
	srcDir = '%s/%s' % (args.inRoot, sess)
	dstDir = '%s/%s' % (args.outRoot, sess)
	shutil.copytree(srcDir, dstDir)
