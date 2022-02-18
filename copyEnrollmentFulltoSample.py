import os
import shutil
import re

# one-off script to copy enrollment audio from "full" session direcotry to 5-min sample directory

sessions = os.path.join('configs', 'deepSample2.txt') # txt file list of session paths
sesspath_in_stem = 'data/deepSampleFull/'
sesspath_out_stem = 'data/deepSample2/'

with open(sessions) as ctl: # reads lines without empties
    sesslist = (line.rstrip() for line in ctl) 
    sesslist = list(line for line in sesslist if line)
for sesspath in sesslist: 
    sessname = os.path.basename(sesspath) 
    sessname = re.sub( '_5min','',sessname)
    print(sessname)
    
    sesspath_in = os.path.join(sesspath_in_stem, sessname)
    enroll_in = os.path.join(sesspath_in, 'enrollment')

    sessname_out = sessname + '_5min'
    sesspath_out = os.path.join(sesspath_out_stem, sessname_out)
    enroll_out = os.path.join(sesspath_out, 'enrollment')

    print(enroll_in)
    print(enroll_out)
    shutil.copytree(enroll_in, enroll_out,dirs_exist_ok=True)