# cleanCtl.py  <ctl file>
# ctl file contains list of session paths
# call cleanSess.py for each session in list

import shutil
import sys
import os
import re
import subprocess
import argparse

parser = argparse.ArgumentParser(description=' clean Ctl')
parser.add_argument('ctl')
args = parser.parse_args()

for sess in open(args.ctl):
	sess = sess.strip()
	sessname = os.path.basename(sess)
	subprocess.call(['python','../scripts/cleanSess.py', sess])
