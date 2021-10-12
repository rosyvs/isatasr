# getTags.py  <sess root>
# find session with unannotated chucks
# play files in chunks dir for tagging
# input from stdin a label for file after playing
# output to corpora/orf/g<grade>/<sess>/chunks.tag

import shutil
import os
import re
import argparse

parser = argparse.ArgumentParser(description='get tag files')
parser.add_argument('root')
parser.add_argument('--tags', default='tags')
args = parser.parse_args()


tagsDir = args.tags
if not os.path.exists(tagsDir):
	os.makedirs(tagsDir)

for sess in os.listdir(args.root):
	sessDir = os.path.join(args.root, sess)
	tagfile = os.path.join(sessDir, 'chunks.tag')

	if os.path.exists(tagfile):
		outfile = '%s/%s.cnk' % (tagsDir, sess)
		shutil.copyfile(tagfile, outfile)
