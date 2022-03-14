# quick script to combine transcripts and ASR for annotators/ NLP
import os
import csv
import pandas as pd
import re
from collections import defaultdict
from rosy_asr_utils import name_counter, format_text_for_wer
import jiwer
import json
from statistics import mean

args_ctl =os.path.join('configs', 'deepSample2.txt') # list of session directories to extract segments from
label_fname_pattern = 'utt_labels_{sessname}.csv' # relative to session directory
asrTypes = {'Google':'asr_segwise','GoogleShort':'asr_short_segwise','Watson': 'asr_watson_segwise','WatsonConcat':'asr_watson_concat_segwise','REVConcat':'asr_rev_concat_segwise'} # Friendly label:directory name
JSONdirs = {'Google':'JSON_segwise','Watson': 'JSON_watson_segwise','WatsonConcat':'JSON_watson_concat','REVConcat':'JSON_rev_concat'} # Friendly label:directory name

all_sess = []
utt_counter = 0

# ITERATE OVER SESSIONS
with open(args_ctl) as ctl:
    sesslist = (line.rstrip() for line in ctl) 
    sesslist = list(line for line in sesslist if line)

for sesspath in sesslist: 
    sesspath = sesspath.strip()
    sessname = os.path.basename(sesspath)
   

    labelFile = os.path.join(sesspath,label_fname_pattern.format(**locals()))
    label_df = pd.read_csv(labelFile,keep_default_na=False)

    # get group TODO derive some kinda group ID
    group = set([s  for s in label_df['speaker'] if re.search('Student' ,s,re.IGNORECASE)])

    label_df['recordingID'] = sessname

    

    # get lesson no
    label_df['lesson'] = re.search('SI_+L(\d)', sessname, re.IGNORECASE).group(1)

    label_df['period'] = re.search('SI_+L\d_p(\d)', sessname, re.IGNORECASE).group(1)

    # get an identifier for class instance (combo of lesson, period, date)

    label_df["transcript_type"] = 'human'

    label_df['transcript_norm'] = label_df['utterance'].apply(format_text_for_wer)
    label_df['wordcount'] = label_df['utterance'].apply(lambda x: len(x.split()))
    label_df['norm_wordcount'] = label_df['transcript_norm'].apply(lambda x: len(x.split()))
    # filter out empty utterances 
    label_df = label_df[label_df['norm_wordcount'] >0]

    label_df.reset_index(inplace=True)
    label_df = label_df.rename(columns={"index":"utterance_in_session","utterance":"transcript"})
    label_df['utterance_overall'] = label_df.index + utt_counter

    # count student names in transcript
    label_df['names_count'] = label_df['transcript'].apply(name_counter)
    
    # null measures for WER
    label_df["wer"] = None
    label_df["substitutions"] = None
    label_df["deletions"] = None
    label_df["insertions"] = None

    sess_df = label_df
    utt_counter += len(label_df)


    # get ASR results
    for a in asrTypes:

        # Load JSON of ASR result for Concat pipelines
        JSONdir = JSONdirs.get(a)
        if a == 'WatsonConcat':
            with open(os.path.join(sesspath, JSONdir, f'{sessname}.json')) as jf:
                result = json.load(jf)
            word_timings =  [r['alternatives'][0]['timestamps'] for r in result['results']]
            word_timings = [elm for sublist in word_timings for elm in sublist]

            word_confidence =  [r['alternatives'][0]['word_confidence'] for r in result['results']]
            word_confidence = [elm for sublist in word_confidence for elm in sublist]
            words = zip(word_timings, word_confidence)

        if a == 'REVConcat':
            with open(os.path.join(sesspath, JSONdir, f'{sessname}.json')) as jf:
                result = json.load(jf)

            word_starts =  [ r['ts'] for m in result['monologues'] for r in m['elements']  if r['type'] == 'text']
            word_ends =  [ r['end_ts'] for m in result['monologues'] for r in m['elements']  if r['type'] == 'text']
            word_confidence = [ r['confidence'] for m in result['monologues'] for r in m['elements']  if r['type'] == 'text']

            # word_timings = [(r['value'], r['ts'], r['end_ts']) for m in result['monologues'] for r in m['elements']  if r['type'] == 'text']
            # word_confidence = [(r['value'], r['confidence']) for m in result['monologues'] for r in m['elements']  if r['type'] == 'text']
            words = zip(word_starts, word_ends, word_confidence)

        concatStart=0.0
        for i, row in label_df.iterrows():
            row['transcript_type'] = a
            s = row["utterance_in_session"]
            asrFile = os.path.join(sesspath, asrTypes[a] ,f'{sessname}_{row["utterance_in_session"]}.asr')
            reference_norm = row['transcript_norm']
            concatEnd = concatStart + row["end_sec"] - row["start_sec"]

            if os.path.isfile(asrFile): 
                asr = open(asrFile,'r').read()
                asr_norm = format_text_for_wer(asr)

                # WER metrics 
                row['wer'] = jiwer.wer(row['transcript_norm'].split(), asr_norm.split())
                wer_meas = jiwer.compute_measures(row['transcript_norm'].split(), asr_norm.split())
                row['substitutions'] = wer_meas['substitutions']
                row['deletions'] = wer_meas['deletions']
                row['insertions'] = wer_meas['insertions']
                row['BOWdistance'] = ( len(set(asr_norm.split())-set(reference_norm.split()) ) + \
                    len(set(reference_norm.split())-set(asr_norm.split()) ) )\
                    / (len(reference_norm.split()) + len(asr_norm.split()))

                # put asr in transcript columns, overwriting human transcript
                row['transcript'] = asr
                row['transcript_norm'] = asr_norm
                row['wordcount'] = len(asr.split())
                row['norm_wordcount'] = len(asr_norm.split())



            # # Get utterance-level mean confidence (from full-reult JSON files)
            # if a == 'REVConcat' or a == 'WatsonConcat':
            #     print(f'concat start: {concatStart}, concat end: {concatEnd}')
            #     # words_from_concat = [w[0] for w in word_timings if (w[2]>concatStart and w[1]<concatEnd)]
            #     # wordconf_from_concat = [conf[1] for (tim, conf) in words if tim[2]>concatStart and tim[1]<concatEnd]
            #     words_from_concat = [w[0] for w in word_timings if (w[2]>concatStart and w[1]<concatEnd)]
            #     wordconf_from_concat = [conf for (st, en, conf) in words if en>concatStart and st<concatEnd]
            #     print(words_from_concat, wordconf_from_concat)
            #     if wordconf_from_concat:
            #         uttconf = mean(wordconf_from_concat)
            #     else:
            #         uttconf = None

            #     print(f'Confidence: {uttconf} {" ".join(words_from_concat)}')
            # concatStart = concatEnd # increment timing counter for next segment


            # if a == 'Google':
            #     with open(os.path.join(sesspath, JSONdir, f'{sessname}_{s}.json')) as jf:
            #         result = json.load(jf)
            #         if row['transcript'].strip(): # confidence only exists if ASR returned words
            #             word_confidence =  [r['alternatives'][0]['confidence'] for r in result['results']]
            #         # word_confidence = [elm for sublist in word_confidence for elm in sublist]
            #         uttconf = mean(word_confidence)
            # if a == 'Watson':
            #     with open(os.path.join(sesspath, JSONdir, f'{sessname}_{s}.json')) as jf:
            #         result = json.load(jf)
            #         word_confidence =  [r['alternatives'][0]['word_confidence'] for r in result['results']]
            #         word_confidence = [elm[1] for sublist in word_confidence for elm in sublist]
            #         uttconf = mean(word_confidence) if word_confidence else None
            # if a == 'GoogleShort':
            #     uttconf = None
            # row['confidence'] = uttconf


            sess_df = sess_df.append(row)

               

                            
            #allASR[a].append(utterance_in_session, speaker, asr, start_sec, end_sec, lesson, recordingID, a, names_count , wer, subs, dels, ins)


    # allASR = pd.DataFrame(allASR)
    # label_df = pd.concat([label_df, allASR], axis=0)

    #df1.append(df2, ignore_index=True)


    # # transcript wordcount - do after merging asr in

                # asr_norm = format_text_for_wer(asr)
                # asr_wordcount = len(asr.split())
                # asr_norm_wordcount =  len(asr_norm.split())




    all_sess.append(sess_df)


all_sess_df = pd.concat(all_sess)


all_sess_df = all_sess_df[[
    'utterance_overall',
    'utterance_in_session',
    'recordingID',
    'lesson',
    'period',
    'speaker',
    'transcript_type', 
    'transcript',
    'transcript_norm',
    'start_sec',
    'end_sec',
    'wordcount',
    'norm_wordcount',
    'names_count',
    'wer',
    'substitutions',
    'deletions',
    'insertions',
    'BOWdistance'
]
]

all_sess_df.to_csv(os.path.join('..','EDM22', 'ASRDeepSample2.csv'))
