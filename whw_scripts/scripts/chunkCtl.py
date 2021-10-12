# chunkCtl.py  <ctl file>
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
parser.add_argument('--minsil',default='0.9')
args = parser.parse_args()

for sess in open(args.ctl):
	sess = sess.strip()
	print(sess)
	sessName = os.path.basename(sess)
	wav = '%s/%s.wav' % (sess,sessName)
	subprocess.call(['python','scripts/vad_wav.py', wav,'--minsil',args.minsil])
	subprocess.call(['python','scripts/chunkSegs.py', sess])
