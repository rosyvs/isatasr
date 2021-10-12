# python mkTest.py <path to session>
# generate test file structure

import os
import re
import subprocess
import argparse

parser = argparse.ArgumentParser(description='generate test file structure')
parser.add_argument('sess_path', help='session path')
parser.add_argument('--data', default='data/test')
args = parser.parse_args()

sessDir = args.sess_path
sessName = os.path.basename(args.sess_path)
outDir = args.data
if not os.path.exists(outDir):
	os.makedirs(outDir)

trialInFile = os.path.join(sessDir, 'test.txt')
trialOutFile = os.path.join(outDir, 'trials')
spkFile = os.path.join(outDir, 'utt2spk')
wavFile = os.path.join(outDir, 'wav.scp')
