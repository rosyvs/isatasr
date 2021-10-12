# reformat.py  <sess dir>
# find session with unannotated chucks
# play files in chunks dir for tagging
# input from stdin a label for file after playing
# output to corpora/orf/g<grade>/<sess>/chunks.tag

import shutil
import os
import re
import argparse

parser = argparse.ArgumentParser(description='get tag files')
parser.add_argument('dir')
args = parser.parse_args()

for sess in os.listdir(args.dir):
	new = sess.replace(' ','_')
	src = os.path.join(args.dir,sess)
	dst = os.path.join(args.dir,new)
	os.rename(src,dst)
