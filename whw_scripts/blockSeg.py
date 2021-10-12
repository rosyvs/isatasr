# blockSeg <ctl>
# block segments into ~1-min blocks
# input from <sess>/segments output to <sess>/blocks

from pydub import AudioSegment
import re
import sys
import os
import argparse

parser = argparse.ArgumentParser(description='form blocks from segments')
parser.add_argument('ctl')
parser.add_argument('--blocksecs', default='60')
args = parser.parse_args()

blksecs = int(args.blocksecs)

for sess in open(args.ctl):
	sess = sess.strip()
	segDir = os.path.join(sess,'segments')
	name = os.path.dirname(sess)
	segmap = os.path.join(segDir,'%s.seg' % name)
	blkDir = os.path.join(sess,'blocks')
	if not os.path.exists(blkdir):
		os.makedir(blkDir)
	blkmap = []
	blknum= 0

	cur = []
	curlen = 0.0
	for seg in open(segmap):
		seg = seg.strip()
		snum,beg,end = seg.split()
		dur = end - beg

		# split segments longer than requested block duration
		if dur < blksecs:
			blkmap.append( (seg,blknum) )
			blknum += 1
			cur = []
			curlen = 0.0

		# add segment to current block
		if (curlen + dur) <= blksecs:
			cur.append(snum)
			curlen += dur
			continue

		# save current block in map
		if len(cur) > 0:
			for s in cur:
				blkmap.append( (s,blknum) )
			blknum += 1
			cur = []
			curlen = 0.0

		# add new segment to cur
		if (curlen + dur) <= blksecs:
			cur.append(snum)
			curlen += dur
			continue

		# seg too large, have to split

