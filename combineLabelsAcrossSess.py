# quick script to combine transcripts and ASR for annotators/ NLP
import os
import csv
import pandas as pd
import re
from collections import defaultdict
from rosy_asr_utils import name_counter, format_text_for_wer
import jiwer

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

    label_df['sessionID'] = sessname

    # get lesson no
    label_df['lesson'] = re.search('SI_+L(\d)', sessname, re.IGNORECASE).group(1)


    label_df.reset_index(inplace=True)
    label_df = label_df.rename(columns={"index":"utterance_in_session","utterance":"transcript"})
    label_df["transcript_type"] = 'human'

    label_df['transcript_norm'] = label_df['transcript'].apply(format_text_for_wer)
    label_df['wordcount'] = label_df['transcript'].apply(lambda x: len(x.split()))
    label_df['norm_wordcount'] = label_df['transcript_norm'].apply(lambda x: len(x.split()))

    # count student names in transcript
    label_df['names_count'] = label_df['transcript'].apply(name_counter)
    
    # null measures for WER
    label_df["wer"] = None
    label_df["substitutions"] = None
    label_df["deletions"] = None
    label_df["insertions"] = None
    # filter out empty utterances 
    label_df = label_df[label_df['norm_wordcount'] >0]

    sess_df = label_df

    # get ASR results
    for a in asrTypes:
        for i, row in label_df.iterrows():
            row['transcript_type'] = a
            asrFile = os.path.join(sesspath, asrTypes[a] ,f'{sessname}_{row["utterance_in_session"]}.asr')
            if os.path.isfile(asrFile): 
                asr = open(asrFile,'r').read()
                asr_norm = format_text_for_wer(asr)

                # WER metrics 
                row['wer'] = jiwer.wer(row['transcript_norm'].split(), asr_norm.split())
                wer_meas = jiwer.compute_measures(row['transcript_norm'].split(), asr_norm.split())
                row['substitutions'] = wer_meas['substitutions']
                row['deletions'] = wer_meas['deletions']
                row['insertions'] = wer_meas['insertions']

                # put asr in transcript columns
                row['transcript'] = asr
                row['transcript_norm'] = asr_norm
                row['wordcount'] = len(asr.split())
                row['norm_wordcount'] = len(asr_norm.split())

                sess_df = sess_df.append(row)

        

                
               

                            
            #allASR[a].append(utterance_in_session, speaker, asr, start_sec, end_sec, lesson, sessionID, a, names_count , wer, subs, dels, ins)


    # allASR = pd.DataFrame(allASR)
    # label_df = pd.concat([label_df, allASR], axis=0)

    #df1.append(df2, ignore_index=True)


    # # transcript wordcount - do after merging asr in

                # asr_norm = format_text_for_wer(asr)
                # asr_wordcount = len(asr.split())
                # asr_norm_wordcount =  len(asr_norm.split())




    all_sess.append(sess_df)


all_sess_df = pd.concat(all_sess)
all_sess_df.reset_index(drop=True,inplace=True)
all_sess_df = all_sess_df.rename(columns={"index":"utterance_overall"})

all_sess_df.to_csv(os.path.join('..','annotation', 'combinedLabelsDeepSample2.csv'))