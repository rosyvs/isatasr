import os
import re
import csv
from operator import itemgetter
from pydub import AudioSegment

from rosy_asr_utils import *


# Process timestamps for enrollment for each student
# extract audio for each ID
# concatenate all utterances for that ID and export the audio


export_audio = True

ELANdir = os.path.expanduser(os.path.normpath(
    '~/Dropbox (Emotive Computing)/iSAT/AudioPrepro/data/transcripts_unsorted/Enrollment Annotations/')) # input
baseSessDir = os.path.normpath(os.path.expanduser(
    '~/Dropbox (Emotive Computing)/iSAT/AudioPrepro/data/deepSampleFull/')) # where sessions are stored. Will output in separate /transcript dir per session dir. 

# loop over files and convert
for ELANfile in os.listdir(ELANdir):
    print(ELANfile)
    if ((not ELANfile.endswith('.txt')) or (ELANfile.startswith('~'))): 
        continue
    sessname = re.sub('.txt', '', ELANfile)
    sessname = re.sub('Annotated_Enrollment_', '', sessname)

    sesspath = os.path.join(baseSessDir, sessname)
    print(sesspath)

    # directory for enrollment audio, will be created
    enrollDir = os.path.join(sesspath, 'enrollment')
    os.makedirs(enrollDir, exist_ok = True)
    labelFile = os.path.join(enrollDir, 'timestamps.csv')
    # read in enrollment timestamps
    labels=[]
    with open(os.path.join(ELANdir, ELANfile)) as in_file:
        reader = csv.reader(in_file, delimiter="\t")
        # skip headers
        next(reader)
        next(reader)
        reader =  sorted(reader, key=itemgetter(2))

        labels = [] # transcript with speaker labels 

        for utt in reader:
            if not ''.join(utt).strip():
                continue
            speaker,_,start_HHMMSS, end_HHMMSS, _ = utt
            start_sec = HHMMSS_to_sec(start_HHMMSS)
            end_sec = HHMMSS_to_sec(end_HHMMSS)
            
            labels.append((speaker, start_sec,end_sec)) 
    labels= pd.DataFrame(labels, columns = ('speaker','start_sec','end_sec'))
    labels.to_csv(labelFile,index=False)
    
    # identify speakers
    speakers = set(labels['speaker'])
    print(speakers)

    if not os.path.exists(os.path.join(sesspath, f'{sessname}.wav')):
        print('WARNING: no audio found for this session, but enrollment annotation exists. Skipping...')
        continue
    # read audio
    sess_audio = AudioSegment.from_wav(os.path.join(sesspath, f'{sessname}.wav'))

    # concatenate audio
    if export_audio:
        for s in speakers:
            enrAudio = AudioSegment.empty()
            labels_this_spkr = labels[labels['speaker'].str.match(s)]
            for [ix, row] in labels_this_spkr.iterrows():
                enrAudio += sess_audio[row['start_sec']*1000 : row['end_sec']*1000]
            enrFile = os.path.join(sesspath,enrollDir,f'enrollment_{s}.wav')  
            print(enrFile)      
            enrAudio.export(enrFile ,format='wav')
