from cmath import exp
import os
import re
import csv
from operator import itemgetter

from rosy_asr_utils import *

#TODO: make this code less mingin

# Process ELAN transcript .tsv files: reduce and save 
ELANdir = os.path.expanduser(os.path.normpath(
    '/Users/roso8920/Dropbox (Emotive Computing)/iSAT/AudioPrepro/data/transcripts_unsorted/Crystal-deepSample2-ELAN/AnonymizedCorrectedJul2022')) # input
make_sorted_copy = True # ELAN outputs transcripts sorted by speaker not timestamp, save a sorted copy of ELAN transcript? 

export_transcript_to_sess = False # save iSAT-formatted transcripts (transcript .txt, labels .csv) in correct session directories (use if these already exist)

baseSessDir = os.path.normpath(os.path.expanduser(
    '~/Dropbox (Emotive Computing)/iSAT/AudioPrepro/data/deepSample2/')) # where sessions are stored. Will output in separate /transcript dir per session dir. 

# deidentify = True # attempts to redact names from the transcript TODO


# loop over files and convert
for ELANfile in os.listdir(ELANdir):
    if ((not ELANfile.endswith('.txt')) or (ELANfile.startswith('~'))): 
        continue
    sessName = re.sub('.txt', '', ELANfile)
    sessName = re.sub('transcript-diarized-timestamped_', '', sessName)

    if export_transcript_to_sess:
        sessDir = os.path.join(baseSessDir, sessName)

        # will be created
        transcriptDir = os.path.join(sessDir, 'ELANtranscript')
        transcriptFile = os.path.join(transcriptDir, f'{sessName}.txt') 
        labelFile = os.path.join(sessDir, f'utt_labels_{sessName}.csv') 
        labels=[]

    if make_sorted_copy:
        os.makedirs(os.path.join(ELANdir, 'sorted'), exist_ok=True)
    if not os.path.exists(transcriptDir):
        os.makedirs(transcriptDir)

    with open(os.path.join(ELANdir, ELANfile)) as in_file:
        reader = csv.reader(in_file, delimiter="\t")
        # skip headers
        hdr = next(reader)
        next(reader)
        reader =  sorted(reader, key=itemgetter(2)) # sort by timestamp


        labels = [] # transcript with speaker labels and timestamp in sec
        transcript = [] # simple transcript without labels for computing WER
        if make_sorted_copy:
            sortedFile = os.path.join(ELANdir, 'sorted', ELANfile)
            sorted_ELAN = [] # save a sorted version of the orig transcript format for upload
            open(sortedFile, 'w').close() # clear file before appending
        if export_transcript_to_sess:
            open(transcriptFile, 'w').close() # clear file before appending

        for utt in reader:
            if not ''.join(utt).strip():
                continue
            speaker,_,start_HHMMSS, end_HHMMSS, utterance = utt
            start_sec = HHMMSS_to_sec(start_HHMMSS)
            end_sec = HHMMSS_to_sec(end_HHMMSS)
            
            if export_transcript_to_sess:
                labels.append((speaker, utterance, start_sec,end_sec)) 
                transcript.append(utterance) 
            if make_sorted_copy:
                sorted_ELAN.append([speaker,start_HHMMSS, end_HHMMSS, utterance])
            # write out the sorted version of the transcript in tsv
    if make_sorted_copy: 
        with open(sortedFile, 'w') as outfile:
            # outfile.write(hdr[0])
            #outfile.write('\n\n')
            for u in sorted_ELAN:
                outfile.write('\t'.join(u) + '\n')    
    if export_transcript_to_sess:
        with open(transcriptFile, 'w') as outfile:
            for u in transcript:
                if u.strip():
                    print(u)
                    outfile.write(u + '\n')


        labels= pd.DataFrame(labels, columns = ('speaker', 'utterance', 'start_sec','end_sec'))
        labels.to_csv(labelFile,index=False, float_format='%.3f')
