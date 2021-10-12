# vadCtl.py  <ctl file>
# ctl file contains list of session paths
# call vad_wav.py and chunkSegs.py for each session in list

import shutil
import sys
import os
import re
import subprocess
import argparse

parser = argparse.ArgumentParser(description=' score Ctl')
parser.add_argument('ctl')
parser.add_argument('--agg', default='1')
parser.add_argument('--win_size', default='300',help='window size in msec')
args = parser.parse_args()

for sess in open(args.ctl):
	sess = sess.strip()
	print(sess)
	sessName = os.path.basename(sess)
	wav = '%s/%s.wav' % (sess,sessName)
	subprocess.call(['python3','scripts/vad_wav.py', wav,\
		'--agg', args.agg, '--win_size', args.win_size])
