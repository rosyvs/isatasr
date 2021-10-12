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
	subprocess.call(['python','../scripts/mkRefWav.py', sess])
