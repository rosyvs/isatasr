import os
import re
import csv
from operator import itemgetter

from rosy_asr_utils import *


# Process REV transcript .docx files: reduce and save in correct session directories
ELANdir = os.path.expanduser(os.path.normpath(
    '~/Dropbox (Emotive Computing)/iSAT/AudioPrepro/data/transcripts_unsorted/Crystal-deepSample2-ELAN/')) # input
baseSessDir = os.path.normpath(os.path.expanduser(
    '~/Dropbox (Emotive Computing)/iSAT/AudioPrepro/data/deepSample2/')) # where sessions are stored. Will output in separate /transcript dir per session dir. 



deidentify = True # attempts to redact names from the transcript TODO


# loop over files and convert
for ELANfile in os.listdir(ELANdir):
    print(ELANfile)
    if ((not ELANfile.endswith('.txt')) or (ELANfile.startswith('~'))): 
        continue
    sessName = re.sub('.txt', '', ELANfile)
    sessName = re.sub('transcript-diarized-timestamped_', '', sessName)

    sessDir = os.path.join(baseSessDir, sessName)
    print(sessDir)

    # will be created
    transcriptDir = os.path.join(sessDir, 'ELANtranscript')
    transcriptFile = os.path.join(transcriptDir, f'{sessName}.txt') 
    labelFile = os.path.join(sessDir, f'utt_labels_{sessName}.csv') 
    labels=[]

    if not os.path.exists(transcriptDir):
        os.makedirs(transcriptDir)

    with open(os.path.join(ELANdir, ELANfile)) as in_file:
        reader = csv.reader(in_file, delimiter="\t")
        # skip headers
        next(reader)
        next(reader)
        reader =  sorted(reader, key=itemgetter(2))


        labels = [] # transcript with speaker labels 
        transcript = [] # simple transcript without labels for computing WER
        open(transcriptFile, 'w').close() # clear file before appending

        for utt in reader:
            if not ''.join(utt).strip():
                continue
            speaker,_,start_HHMMSS, end_HHMMSS, utterance = utt
            start_sec = HHMMSS_to_sec(start_HHMMSS)
            end_sec = HHMMSS_to_sec(end_HHMMSS)
            
            labels.append((speaker, utterance, start_sec,end_sec)) 
            transcript.append(utterance) 


    with open(transcriptFile, 'w') as outfile:
        for u in transcript:
            if u.strip():
                print(u)
                outfile.write(u + '\n')

    labels= pd.DataFrame(labels, columns = ('speaker', 'utterance', 'start_sec','end_sec'))
    labels.to_csv(labelFile,index=False)
