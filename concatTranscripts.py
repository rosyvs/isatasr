from __future__ import absolute_import
import os
from rosy_asr_utils import *
from natsort import natsorted 

# Concatenate all transcripts in a session

args_ctl =os.path.join('configs', '4SG.txt') # list of session directories 
transcript_in_dir = 'transcripts_segwise' # subdirectory containing multiple transcripts to concatenate
with open(args_ctl) as ctl:
    sesslist = (line.rstrip() for line in ctl) 
    sesslist = list(line for line in sesslist if line)

for sesspath in sesslist: 
    print(f'sesspath: {sesspath}')
    sesspath = sesspath.strip()
    sessname = os.path.basename(sesspath)
    transcriptDir = os.path.join(sesspath,transcript_in_dir)
    transcriptFullDir = os.path.join(sesspath,'transcript_full') # where full session asr will be stored
    transcriptFullFile = os.path.join(transcriptFullDir,f"{sessname}.txt") # full session ASR results
    if not os.path.exists(transcriptFullDir):
        os.makedirs(transcriptFullDir)
    # loop over asr results
    transcript_list = [f for f in os.listdir(transcriptDir) if f.endswith('.txt')]
    n_transcript = len(transcript_list)
    # sort by block/segment number
    transcript_list = natsorted(transcript_list)
    transcript_fullsess = []

    for f in transcript_list:
        transcriptFile = os.path.join(transcriptDir,f)
        if not os.path.isfile(transcriptFile): 
            transcript = ''
        else: 
            transcript = open(transcriptFile,'r').read()
            transcript = format_sentences(transcript)
        transcript_fullsess.append(transcript)

        # append all ASR results to a single file
    with open(transcriptFullFile,'w') as outfile:
        outfile.write('\n'.join(transcript_fullsess))

