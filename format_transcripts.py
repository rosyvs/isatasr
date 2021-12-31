import docx
import os
import re
from rosy_asr_utils import *

# Process REV transcript .docx files: reduce and save in correct session directories
transcriptDocxDir = os.path.expanduser(os.path.normpath(
    '~/Dropbox (Emotive Computing)/iSAT/AudioPrepro/data/transcripts_unsorted/Crystal-deepSample/')) # input
sessDir = os.path.normpath(os.path.expanduser(
    '~/Dropbox (Emotive Computing)/iSAT/AudioPrepro/data/deepSample/')) # where sessions are stored. Will output in separate /transcript dir per session dir. 

# Sometimes the transcripts were done for 1-minute blocks, other times for the whole session.
# Parsing the REV transcript filename is different in each case, so make sure to set the following flag correctly
blocked = False


# loop over files and convert
for file in os.listdir(transcriptDocxDir):
    print(file)
    if ((not file.endswith('.docx')) or (file.startswith('~'))): 
        continue
    basename = re.sub('.docx', '', file)
    

    if blocked:
        field = basename.split('_')
        blk = field[len(field)-1]
        sessName = '_'.join(field[0:-1])
    else:
        sessName = basename
        transcriptDir = os.path.join(sessDir, sessName, 'REVtranscripts')

    if not os.path.exists(transcriptDir):
        os.makedirs(transcriptDir)

    if blocked:
        clean_REV_transcript(docx_fname=os.path.join(transcriptDocxDir ,file), 
            txt_fname=os.path.join(transcriptDir, f"{sessName}_{blk}.txt"))
    else:
        clean_REV_transcript(docx_fname=os.path.join(transcriptDocxDir ,file), 
            txt_fname=os.path.join(transcriptDir, f"{sessName}.txt"))