import os
import pandas as pd
import csv
from collections import defaultdict
# extract a dict for student ID <-> student name from original and anol=nymised transcripts

args_ctl =os.path.join('configs', 'deepSample2.txt') # list of session directories to extract segments from
# Process ELAN transcript .tsv files: reduce and save in correct session directories
anonELANdir = os.path.expanduser(os.path.normpath(
    '~/Dropbox (Emotive Computing)/iSAT/AudioPrepro/data/transcripts_unsorted/Crystal-deepSample2-ELAN/Anonymized/')) # input
ELANdir = os.path.expanduser(os.path.normpath(
    '~/Dropbox (Emotive Computing)/iSAT/AudioPrepro/data/transcripts_unsorted/Crystal-deepSample2-ELAN/RealNames/')) # input

def check_dupe_dicts(d1, d2):
    conflicts=[]
    for k in d1.keys() & d2.keys():
        if d1[k] != d2[k]:
            print(f'***Conflicting entries for key {k}. Values: {d1[k]}, {d2[k]}')
            conflicts.append(k)
    return conflicts


# ITERATE OVER SESSIONS
with open(args_ctl) as ctl:
    sesslist = (line.rstrip() for line in ctl) 
    sesslist = list(line for line in sesslist if line)

ID_to_name_all = defaultdict(list)
name_to_ID_all = defaultdict(list)

# loop over files and convert
for ELANfile in os.listdir(ELANdir):
    if ((not ELANfile.endswith('.txt')) or (ELANfile.startswith('~'))): 
        continue

    named = pd.read_table(os.path.join(ELANdir, ELANfile), skiprows=[0,1],  sep='\t', header=None, names=['speaker','nan','start','end','utterance'])
    anon = pd.read_table(os.path.join(anonELANdir, ELANfile), skiprows=[0,1],  sep='\t',header=None, names=['speaker','nan','start','end','utterance'])

    merged = named.merge(anon, how='inner', on=['start','end','utterance'], suffixes = ['_named','_anon'])
    ID_to_name = {anon:named for anon, named in zip(merged['speaker_anon'], merged['speaker_named'])}

    conflicts = check_dupe_dicts(ID_to_name_all,ID_to_name)
    for k,v in ID_to_name.items():
        if not v in ID_to_name_all[k]:
            ID_to_name_all[k].append(v) 

    name_to_ID = {named:anon for anon, named in zip(merged['speaker_anon'], merged['speaker_named'])}

    conflicts = check_dupe_dicts(name_to_ID_all,name_to_ID)
    for k,v in name_to_ID.items():
        if not v in name_to_ID_all[k]:
            name_to_ID_all[k].append(v) 

# write to file
w = csv.writer(open("../annotation/name_to_ID.csv", "w"))

for k,v in name_to_ID_all.items():
    w.writerow([k,','.join(v)])

w2 = csv.writer(open("../annotation/ID_to_name.csv", "w"))
for k,v in ID_to_name_all.items():
    w2.writerow([k,','.join(v)])
