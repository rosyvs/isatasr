# python lenChunks.py <session>
# find longest, shortest and total number of segs

import os
import re
import subprocess
import argparse

parser = argparse.ArgumentParser(description='mk verification test set')
parser.add_argument('sess', help='score file')
parser.add_argument('--segdir', default='segments')
args = parser.parse_args()

#segDir = '%s/test/wav/segments/1' % args.sess
segDir = '%s/%s' % (args.sess, args.segdir)
base = os.path.basename(args.sess)

maxs = 0.0
maxf = ''
mins = 100000.0
count = 0
total = 0.0
for file in os.listdir(segDir):
	filepath = os.path.join(segDir, file)
	fbytes = os.stat(filepath).st_size -44
	nsec = float(fbytes)/32000.0
	print(file, nsec)
	total += nsec
	if nsec < mins: mins = nsec
	if nsec > maxs:
		maxs = nsec
		maxf = file
	count += 1
minm = mins/60.0
maxm = maxs/60.0
totm = total/60.0
print('%s count: %d   total: %0.2f   min: %0.2f   max: %0.2f  av: %0.2f' % (base,count, totm, minm, maxm, (totm/count)* 60))
#print('count: %d   min: %f   max: %f' % (count, mins, maxs))
#print('count: %d   min: %f   max: %f %s ' % (count, mins, maxs, maxf))

