# quick script to combine transcripts for annotators
import os
import csv
import pandas as pd
import re

args_ctl =os.path.join('configs', 'deepSample2.txt') # list of session directories to extract segments from
label_fname_pattern = 'utt_labels_{sessname}.csv' # relative to session directory

all_sess = []


# ITERATE OVER SESSIONS
with open(args_ctl) as ctl:
    sesslist = (line.rstrip() for line in ctl) 
    sesslist = list(line for line in sesslist if line)

for sesspath in sesslist: 
    sesspath = sesspath.strip()
    sessname = os.path.basename(sesspath)
   

    labelFile = os.path.join(sesspath,label_fname_pattern.format(**locals()))
    label_df = pd.read_csv(labelFile,index_col=None,keep_default_na=False)

    # get group
    group = set([s  for s in label_df['speaker'] if re.search('Student' ,s,re.IGNORECASE)])

    # get lesson no
    label_df['lesson'] = re.search('SI_+L(\d)', sessname, re.IGNORECASE).group(1)

    label_df['sessionID'] = sessname
    all_sess.append(label_df)

all_sess_df = pd.concat(all_sess)
all_sess_df.reset_index(inplace=True)
all_sess_df = all_sess_df.rename(columns={"index":"utterance_in_session"})
all_sess_df.reset_index(inplace=True)
all_sess_df = all_sess_df.rename(columns={"index":"utterance_overall"})
