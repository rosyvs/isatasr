import shutil
import sys
import os
import re
import subprocess
import argparse
from TAD_orig.tad_chunks import Frame, frame_generator, read_wave, write_wave

# # if calling from terminal (see whw code):
# parser = argparse.ArgumentParser(description='provide session list (.ctl file)')
# parser.add_argument('ctl')
# args = parser.parse_args()

# for devel: 
args_ctl = os.path.join('configs', 'one_sess.txt')



with open(args_ctl) as ctl:
    sesslist = (line.rstrip() for line in ctl) 
    sesslist = list(os.path.normpath(line) for line in sesslist if line)

for sesspath in sesslist: # TEMP DEBUG
    print(f'sesspath: {sesspath}')
    sesspath = sesspath.strip()
    sessname = os.path.basename(sesspath)
    tgtDir = os.path.join(sesspath,'targets')
    segDir = os.path.join(sesspath,'segments')

    print(f'Attempting TAD for {sessname}...')
    # check for target audio
    if not os.path.exists(tgtDir):
        print(' !! No target audio provided. Please provide a subfolder "targets" containing .wav files in the session directory')
        continue

    tgt_list = [f for f in os.listdir(tgtDir) if f.endswith('.wav')]
    n_tgt = len(tgt_list)
    if n_tgt ==0:
        print(' !! No target audio provided. Please provide .wav files in the session\'s /targets/ subfolder')
        continue
    #     
    for t in tgt_list:
        print(f'    generating XVector for target {t}...')
        # make MFCCs from target audio
        # compute XVector embedding of target

    
    seg_list = [f for f in os.listdir(segDir) if f.endswith('.wav')]
    for s in seg_list:

        # make MFCCs from segment audio
        # ? chunk to frames before or after MFCC? 


        for f in frames:
        # compute XVector embedding of frame
        # PLDA scoring 

            score = is_target(tgt_XVs, frame_XV)