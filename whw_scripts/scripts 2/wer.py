#!/usr/bin/env python3
# wer.py <hyp file> <ref file>

import re
import sys
import os
import argparse

parser = argparse.ArgumentParser(description='segment session files')
parser.add_argument('--hyp', default='')
parser.add_argument('--ref', default='')
parser.add_argument('--segdir', default='segments')
args = parser.parse_args()


with open(args.hyp) as f:
    hstr =  ' '.join(line.strip() for line in f)  
with open(args.ref) as f:
    rstr =  ' '.join(line.strip() for line in f)  

cmd = 'bin/sclite -l 5000 -h "%s" -r "%s" -i wsj -o pralign > /dev/null' % \
	(hstr, rstr)
