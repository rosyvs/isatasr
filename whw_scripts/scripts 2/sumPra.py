# python sumPra.py

import os
import subprocess
import string
import re
import argparse

parser = argparse.ArgumentParser(description='score session')
parser.add_argument('inDir')
parser.add_argument('--tmp', default='tmp', help='Temporary Files Directory')
parser.add_argument('--bin', default='bin', help='Binaries Directory')
args = parser.parse_args()

pra = []
for file in os.listdir(args.inDir):
	if not file.endswith('.pra'): continue
	pra.append(file)

pra.sort()
tot_cor = 0
tot_sub = 0
tot_del = 0
tot_ins = 0
print('ID correct substitutions deletions insertions WER')
for file in pra:
	for line in open(os.path.join(args.inDir,file)):
		if line.startswith('Scores:'): break
	line = line.strip()
	line = re.sub('^.*\) ','',line)
	cor,sub,xdel,ins = line.split()
	ncor = int(cor)
	nsub = int(sub)
	ndel = int(xdel)
	nins = int(ins)
	ref = ncor + nsub + ndel
	wacc = float(ncor)/float(ref)
	wer = (float(nsub+ndel+nins))/float(ref)
	print(file, cor, sub, xdel, ins, '%0.2f' % wer)

	tot_cor += ncor
	tot_sub += nsub
	tot_del += ndel
	tot_ins += nins
tot_ref = tot_cor + tot_sub + tot_del
wacc = float(tot_cor)/float(tot_ref)
wer = float(tot_sub+tot_del+tot_ins)/float(tot_ref)
print('Total',tot_cor, tot_sub, tot_del, tot_ins, '%0.2f' % wer)

