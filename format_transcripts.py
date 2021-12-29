import docx
import os
import re
from rosy_asr_utils import *

# Process .docx files: reduce and save in correct session directories
transcriptDocxDir = os.path.expanduser(os.path.normpath('~/Dropbox (Emotive Computing)/iSAT/AudioPrepro/data/transcripts_unsorted/Crystal-deepSample/')) # input
sessDir = os.path.normpath(os.path.expanduser('~/Dropbox (Emotive Computing)/iSAT/AudioPrepro/data/deepSample/')) # where sessions are stored. Will output in separate /transcript dir per session dir. 
# ctl has list of paths transcripts to process

blkList = []

# loop over files and convert
for file in os.listdir(transcriptDocxDir):
    print(file)
    if ((not file.endswith('.docx')) or (file.startswith('~'))): 
        continue
    basename = re.sub('.docx', '', file)
    # UNCOMMENT FOR BLOCK VERSION:
    # field = basename.split('_')
    # blk = field[len(field)-1]
    # sessName = '_'.join(field[0:-1])
    sessName = basename
    transcriptDir = os.path.join(sessDir, sessName, 'transcripts')
#     field = sess.split('_')
#     blk = field[len(field)-1]
#     blkList.append( int(blk) )
# blklist.sort()
    if not os.path.exists(transcriptDir):
        os.makedirs(transcriptDir)
    
    
    # # read text from .docx
    # doc = docx.Document(os.path.join(transcriptDocxDir ,file))
    # doctext = [p.text for p in doc.paragraphs]
    # # write unstripped transcript to .txt
    # tscptfile = os.path.join(transcriptDir, f"{sessName}_{blk}_diarized.txt")
    # with open(tscptfile,'w') as outfile:
    #     outfile.write('\n'.join(doctext))

    # # strip the various Speaker IDs and crosstalk indicators  off
    # doc_stripped = [re.sub('Speaker \d+:','',line) for line in doctext]
    # doc_stripped = [re.sub('Students:','',line) for line in doc_stripped]
    # doc_stripped = [re.sub('group:','',line) for line in doc_stripped]
    # doc_stripped = [re.sub('\(laughs\)','',line) for line in doc_stripped]
    # doc_stripped = [re.sub('\(affirmative\)','',line) for line in doc_stripped]
    # doc_stripped = [re.sub('\[crosstalk\]','',line) for line in doc_stripped]
    # doc_stripped = [re.sub('\[inaudible\]','',line) for line in doc_stripped]
    # doc_stripped = [re.sub(r"\t",'',line) for line in doc_stripped]
    # doc_stripped = [line  for line in doc_stripped if not re.match(r'^\s*$', line)] # remove blank lines
    # # write stripped transcript to txt
    # tscptfile = os.path.join(transcriptDir, f"{sessName}_{blk}.txt")
    # with open(tscptfile,'w') as outfile:
    #     outfile.write('\n'.join(doc_stripped))


# UNCOMMENT FOR BLOCK VERSION:
    # norm_transcript(docx_fname=os.path.join(transcriptDocxDir ,file), 
    #                 txt_fname=os.path.join(transcriptDir, f"{sessName}_{blk}.txt"))

    norm_transcript(docx_fname=os.path.join(transcriptDocxDir ,file), 
                txt_fname=os.path.join(transcriptDir, f"{sessName}.txt"))