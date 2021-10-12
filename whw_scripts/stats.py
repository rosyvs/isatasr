#!/usr/bin/env python3
# python stats.py <session path> or <ctl file>
# read  eer and chunk scores
# find err rate and count for each tag combination

import os
import re
import subprocess
import argparse

parser = argparse.ArgumentParser(description=' chunk stats')
parser.add_argument('--ctl', default='')
parser.add_argument('--sesspath', default='')
parser.add_argument('--scores', default='results')
args = parser.parse_args()

# get sorted list of sessions
sesslist = []
if args.ctl:
	for sess in open(args.ctl):
		sess = sess.strip()
		sesslist.append(sess)
elif args.sesspath:
	sesslist.append(args.sesspath)

global_stats  = {'t':(0,0), 'bt':(0,0), 'Bt':(0,0), 'nt':(0,0), 'Nt':(0,0),
		'bnt':(0,0), 'BNt':(0,0), 'b':(0,0), 'n':(0,0), 'e':(0,0),
		's':(0,0), 'st':(0,0), 'bs':(0,0), 'bst':(0,0), 'ns':(0,0)}
for sess in sesslist:
	sessDir = sess
	trials = os.path.join(sessDir, 'test.txt')
	name = os.path.basename(sessDir)

#	# determine ref target/non-target for chunks
#	ref_class = []
#	for line in open(trials):
#		line = line.strip()
#		val,target,cnk = line.split()
#		file = os.path.basename(cnk)
#		file = re.sub('.wav','',file)
#		ref_class.append(val)

	# get normalized tag string for each chunk
	tags={}
	tagsFile = os.path.join(sessDir, '%s.cnk' % name)
	if not os.path.exists(tagsFile):
		#print('file not found:', tagsFile)
		continue
	for line in open( tagsFile ):
		line = line.strip()
		cnk,tgs = line.split()
		cnk = re.sub('.wav', '', cnk)
		ts = []
		for i in range( len(tgs) ): ts.append(tgs[i])
		ts = sorted( set(ts) )
		tgs = ''.join([i for i in ts])
		if tgs == 'bn': tgs = 'b'
		tags[cnk] = tgs

	# get threshold
	val = ''
	eerFile = '%s/%s.eer' % (args.scores,name)
	if not os.path.exists(eerFile):
		#print('file not found', eerFile)
		continue
	for line in open(eerFile):
		if not line.startswith('thresh'): continue
		x,val = line.split()
		break
	if not val:
		#print('threshold not found')
		continue
	thresh = float(val)

	# read score for each chunk
	hyp_class = []
	scoreFile = os.path.join(args.scores, name + '.cs')
	if not os.path.exists(scoreFile):
		#print('file not found', scoreFile)
		continue
	for line in open(scoreFile):
		line = line.strip()
		target,cnk,sscore = line.split()
		cnk = re.sub('^.*-','',cnk)
		score = float(sscore)
		if score > thresh: val = '1'
		else: val = '0'
		hyp_class.append( (cnk,val) )

	tag_stats  = {'t':(0,0), 'bt':(0,0), 'Bt':(0,0), 'nt':(0,0), 'Nt':(0,0),
		'bnt':(0,0), 'BNt':(0,0), 'b':(0,0), 'n':(0,0), 'e':(0,0),
		's':(0,0), 'st':(0,0), 'bs':(0,0), 'bst':(0,0), 'ns':(0,0)}
	for i in range(len(hyp_class)):
		cnk = hyp_class[i][0]
		h_class = int(hyp_class[i][1])

		# get ref class
		r_tag = tags[cnk] 
		if r_tag.find('t') != -1:
			r_class = 1
		else:
			r_class = 0
		if h_class == r_class: correct = 1
		else: correct = 0

		if r_tag in tag_stats:
			tot_correct = tag_stats[r_tag][0] + correct
			total = tag_stats[r_tag][1] + 1
			tag_stats[r_tag] = (tot_correct, total)
			tot_correct = global_stats[r_tag][0] + correct
			total = global_stats[r_tag][1] + 1
			global_stats[r_tag] = (tot_correct, total)
		else:
			print('tag not found', r_tag)

	outstr = name
	sess_correct = 0
	sess_total = 0
	for rec in tag_stats:
		num_correct = tag_stats[rec][0]
		total = tag_stats[rec][1]
		if total > 0:
			rate = float(num_correct)/float(total)
		else:
			rate = 0.0
		outstr += ' %s(%d %.2f)' % (rec, total, rate)
		sess_correct += num_correct
		sess_total += total
	if sess_total >0:
		sess_rate = float(sess_correct)/float(sess_total)
	else:
		sess_rate = 0.0
	outstr += ' pool(%d %.2f)' % (sess_total, sess_rate)
	print(outstr)
print('Pooled')
outstr = ''
global_correct = 0
global_total = 0
for rec in global_stats:
		num_correct = global_stats[rec][0]
		total = global_stats[rec][1]
		if total > 0:
			rate = float(num_correct)/float(total)
		else:
			rate = 0.0
		outstr += ' %s(%d %.2f)' % (rec, total, rate)
		global_correct += num_correct
		global_total += total
if global_total > 0:
	rate = float(global_correct)/float(global_total)
else:
	rate = 0.0
outstr +=  ' %s(%d %.2f)' % ('pool', global_total, rate)
print(outstr)
