# quick script to combine transcripts and ASR for annotators/ NLP
import os
import csv
import pandas as pd
import re
from collections import defaultdict


args_ctl =os.path.join('configs', 'deepSample2.txt') # list of session directories to extract segments from
label_fname_pattern = 'utt_labels_{sessname}.csv' # relative to session directory
asrTypes = {'Google':'asr_segwise','Watson': 'asr_watson_segwise'} # Friendly label:directory name

all_sess = []


# ITERATE OVER SESSIONS
with open(args_ctl) as ctl:
    sesslist = (line.rstrip() for line in ctl) 
    sesslist = list(line for line in sesslist if line)

for sesspath in sesslist: 
    sesspath = sesspath.strip()
    sessname = os.path.basename(sesspath)
   

    labelFile = os.path.join(sesspath,label_fname_pattern.format(**locals()))
    label_df = pd.read_csv(labelFile,keep_default_na=False)

    # get group TODO group ID
    group = set([s  for s in label_df['speaker'] if re.search('Student' ,s,re.IGNORECASE)])

    # get lesson no
    label_df['lesson'] = re.search('SI_+L(\d)', sessname, re.IGNORECASE).group(1)

    label_df['sessionID'] = sessname

    allASR = defaultdict(list)
    # get ASR results
    for a in asrTypes:
        for s in label_df.index:
            asrFile = os.path.join(sesspath, asrTypes[a] ,f'{sessname}_{s}.asr')
            if not os.path.isfile(asrFile): 
                asr = '' 
                print(f'--no ASR found for segment {s}, check paths')
            else: 
                asr = open(asrFile,'r').read()
                print(asr)
                allASR[a].append(asr)
    allASR = pd.DataFrame(allASR)
    label_df = pd.concat([label_df, allASR], axis=1)
    all_sess.append(label_df)

all_sess_df = pd.concat(all_sess)
all_sess_df.reset_index(inplace=True)
all_sess_df = all_sess_df.rename(columns={"index":"utterance_in_session"})
all_sess_df.reset_index(inplace=True)
all_sess_df = all_sess_df.rename(columns={"index":"utterance_overall"})

all_sess_df.to_csv(os.path.join('..','annotation', 'combinedLabelsDeepSample2.csv'))