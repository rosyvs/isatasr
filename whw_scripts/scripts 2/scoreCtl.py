# scoreCtl.py  <ctl file>
# ctl file contains list of session paths
# call scoreChunks.bsh findEer.py for each session in list

import shutil
import sys
import os
import re
import subprocess
import argparse

parser = argparse.ArgumentParser(description=' score Ctl')
parser.add_argument('ctl')
args = parser.parse_args()

for sess in open(args.ctl):
	sess = sess.strip()
	sessname = os.path.basename(sess)
	target = '%s/test/wav/targets/1/%s.wav' % (sess, sessname)
	# skip if no target
	if not os.path.exists(target):
		print 'no target', sessname
		continue
	subprocess.call(['../scripts/scoreChunks.bsh', sess])
	subprocess.call(['python','../scripts/findEer.py', sess])
