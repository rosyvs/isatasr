# alignTrans.py <csv transcript> <aws transcript>
import os
import re
import string
import json
import subprocess
import argparse

parser = argparse.ArgumentParser(description='align transcript')
parser.add_argument('csv')
parser.add_argument('aws')
parser.add_argument('--sft', default='n')
args = parser.parse_args()


# read reference csv file
# create list of startSec, endSec, Speaker, text
sp = ''
txt = ''
st = 0
ed = 0
header = 0
Ref = []
for line in open(args.csv):
	if not header:
		header = 1
		continue
	if line.startswith('?'): continue
	
	if line.find('"') != -1:
		field = line.split('"')
		refString = field[1]
		refString = re.sub('\,', ' ',refString)
		line = field[0] + ' ' + refString  + ' ' + field[2]
		
	field = line.split(',')
	refString = ''.join([i if ord(i) < 128 else "'" for i in field[4]])
	refString = re.sub('\.', '',refString)
	refString = re.sub('\?', '',refString)
	refString = refString.lower()
	refString = re.sub(' +ll ', "'ll ", refString)
	refString = re.sub(' +s ', "'s ", refString)
	refString = re.sub(' +t ', "'t ", refString)
	refString = re.sub(' +re ', "'re ", refString)
	refString = re.sub(' i m ', " i'm ", refString)
	refString = re.sub(' i +d ', " i'd ", refString)
	refString = re.sub(' you d ', " you'd ", refString)
	refString = re.sub(' - ', ' ', refString)
	refString = re.sub('\[inaudible\]', ' ', refString)
	refString = re.sub('- ', ' ', refString)
	field[4] = refString

	# start time
	if field[0]:
		if field[0].find(':') != -1:
			tt = field[0].split(':')
			# shift time fields
			if args.sft == 'y':
				st = (60 * int(tt[1])) + int(tt[2])
			else:
				st = (60 * int(tt[0])) + int(tt[1])
		else:
			st = int(field[0])
	
		ss = field[3].strip()
		if ss == 'T':
			sp = 'T'
		else:
			sp = 'S'
	
		txt += ' ' + field[4]

		# if end time too
		if field[1]:
			if field[1].find(':') != -1:
				tt = field[1].split(':')
				if args.sft == 'y':
					ed = (60 * int(tt[1])) + int(tt[2])
				else:
					ed = (60 * int(tt[0])) + int(tt[1])
			else:
				ed = int(field[1])
			if ed == st: ed +=1
	
			# save turn
			Ref.append( (st, ed, sp, txt) )
			st = 0
			ed = 0
			sp = ''
			txt = ''
		else:
			ed = 0
	
	# end time
	elif field[1]:
		if field[1].find(':') != -1:
			tt = field[1].split(':')
			if args.sft == 'y':
				ed = (60 * int(tt[1])) + int(tt[2])
			else:
				ed = (60 * int(tt[0])) + int(tt[1])
		else:
			ed = int(field[1])
		if ed == st: ed +=1

		txt += ' ' + field[4]
	
		# save turn
		Ref.append( (st, ed, sp, txt) )
		st = 0
		ed = 0
		sp = ''
		txt = ''
	else:
		txt += ' ' + field[4]

# read json asw transcript file
with open(args.aws, 'r') as f:
	data = json.load(f)

# create hyp string and get word timings
hw = []
wst = []
wet = []
n_items = len(data["results"]["items"])
for i in range(0, n_items):
	if data["results"]["items"][i]["type"] == "pronunciation":
		hw.append(data["results"]["items"][i]["alternatives"][0]["content"])
		x = float(data["results"]["items"][i]["start_time"])
		y = float(data["results"]["items"][i]["end_time"])
		wst.append(x)
		wet.append(y)
 
# align hyp words with transcript turns
h = 0
htxt = ''
t_c_tot = 0
t_s_tot = 0
t_d_tot = 0
t_i_tot = 0
s_c_tot = 0
s_s_tot = 0
s_d_tot = 0
s_i_tot = 0
bg_tot = 0

for r in range(0,len(Ref)):
	tst = float(Ref[r][0])
	tet = float(Ref[r][1])
	sp = Ref[r][2]

	while (h < len(hw)) and (wst[h] < (tst-1.0)):
		print hw[h], wst[h], wet[h]
		bg_tot += 1
		h += 1
	while (h<len(hw)) and (wet[h] <= tet):
		htxt += ' ' + hw[h]
		h += 1
	if (h<len(hw)) and (wst[h] < tet):
		htxt += ' ' + hw[h]
		h += 1
	if h >= len(hw): break
	
	hypf = 'xx_hyp'
	hypString = htxt
	hypString = re.sub('\.', '',hypString)
	hypString = re.sub('\?', '',hypString)
	hypString = re.sub('\"', '',hypString)
	#hypString.encode('ascii','ignore')
	hypString = hypString.lower()
	if len(hypString) == 0:
		hypString = 'X'
	with open(hypf, 'w') as outfile:
		outfile.write(hypString + '\n')

	reff = 'xx_ref'
	#refString = Ref[r][3]
	refString = ''.join([i if ord(i) < 128 else "'" for i in Ref[r][3]])
	refString = re.sub('\.', '',refString)
	refString = re.sub('\?', '',refString)
	refString = re.sub('\"', '',refString)
	#refString.encode('ascii','ignore')
	refString = refString.lower()
	with open(reff, 'w') as outfile:
		outfile.write(refString + '\n')
	cmd = 'bin/sclite -l 5000 -h "%s" -r "%s" -i wsj -o pralign > /dev/null' % (hypf, reff)
	subprocess.call(cmd, shell=True)
 
	praf = 'xx_hyp.pra'
	for line in open(praf):
		if line.startswith('REF'):
			print line
		if line.startswith('HYP'):
			print line
		if not line.startswith('Scores'): continue
		str = re.sub('^.*\)', '', line)
		c,s,d,i = str.split()
		ci = int(c)
		si = int(s)
		di = int(d)
		ii = int(i)
		tot = ci + si + di
		err = si + di + ii
		e_rate = float(err)/float(tot)
		print 'count', c,s,d,i
		print 'tot', tot, 'err', err, 'e_rate', e_rate
		print 'start', tst, 'end', tet
		print '---------------'
		if sp == 'T':
			t_c_tot += ci
			t_s_tot += si
			t_d_tot += di
			t_i_tot += ii
		else:
			s_c_tot += ci
			s_s_tot += si
			s_d_tot += di
			s_i_tot += ii
	htxt = ''
tot = t_c_tot + t_s_tot + t_d_tot
err = t_s_tot + t_d_tot + t_i_tot
print 'Teacher Correct %i  Sub %i  Del %i  Ins %i  Err_rate %.3f\n' % \
	(t_c_tot, t_s_tot, t_d_tot, t_i_tot, float(err)/float(tot))
tot = s_c_tot + s_s_tot + s_d_tot
err = s_s_tot + s_d_tot + s_i_tot
print 'Student Correct %i  Sub %i  Del %i  Ins %i  Err_rate %.3f\n' % \
	(s_c_tot, s_s_tot, s_d_tot, s_i_tot, float(err)/float(tot))
print 'BG', bg_tot
