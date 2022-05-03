import os
import pandas as pd
import jiwer 
from rosy_asr_utils import *
import csv

# ASR pipeline
# 1. prepSessDirs
# 2. VAD_segmenter / TAD_segmenter (uses automated segmentation) OR segFromAnnotation (uses timestamped transcript)
# 3. ASRsegwiseGoogle (or REV, Watson)
# 4. WER_by_speaker (after formatELANtranscripts/formatREVtranscripts)

# loop over sessions in control file and compute WER for any with both 
# ASR and ref transcripts at the segment level & corresponding segment numbers
# summarise WER by speaker: requires labelled utterances in utt_labels{sessname}.csv
# assumes 1 segment = 1 utterance! 
ctlfile = 'EXAMPLE'
args_ctl =os.path.join('configs', f'{ctlfile}.txt')
asrType = 'asr_segwise'
transcriptType = 'ELANtranscript_segwise'
label_fname_pattern = 'utt_labels_{sessname}.csv' # relative to session directory

by_codec = False # produce summary of WER by codec? Must be final field in sessname

def wer_df_summary(df):
    d={}
    d['n_segments'] = len(df.index)
    d['asr_wordcount'] = sum(df['asr_wordcount'])
    d[ 'transcript_wordcount'] = sum(df['transcript_wordcount'])
    sess_meas = wer_from_counts(sum(df['transcript_wordcount']), 
        df['substitutions'].sum(), 
        df['deletions'].sum(), 
        df['insertions'].sum())
    d['wer']=f'{sess_meas["wer"]:.3f}'
    d['mer']=f'{sess_meas["mer"]:.3f}'
    d['substitutions'] =  df['substitutions'].sum()
    d['deletions']= df['deletions'].sum()
    d['insertions'] =df['insertions'].sum()
    d['sub_rate']= f'{sess_meas["sub_rate"]:.3f}'
    d['del_rate']= f'{sess_meas["del_rate"]:.3f}'
    d['ins_rate']= f'{sess_meas["ins_rate"]:.3f}'
    return pd.Series(d)


with open(args_ctl) as ctl: # reads lines without empties
    sesslist = (line.rstrip() for line in ctl) 
    sesslist = list(os.path.normpath(line) for line in sesslist if line)


all_sess_seg_wer = []
all_sess_alignment = []

for sesspath in sesslist: 
    sesspath = sesspath.strip()
    sessname = os.path.basename(sesspath)
    print(f'COMPUTING SEGWISE WER FOR SESSION: {sessname}')
    asrDir = os.path.join(sesspath,asrType)
    transcriptDir = os.path.join(sesspath,transcriptType)

    # get utterance labels
    labelFile = os.path.join(sesspath,label_fname_pattern.format(**locals()))

    # get list of segments
    with open(labelFile) as in_file:
        reader = csv.reader(in_file, delimiter=",")
        # # skip header
        next(reader)

        seg_data = []
        # loop over segments
        aligned_segwise=[]
        for s, utt_labels in enumerate(reader):
            speaker,utterance,start_sec, end_sec = utt_labels
            speaker = speaker.title() # deal with cases where the name is not consistently capitalized
            asrFile = os.path.join(asrDir,f'{sessname}_{s}.asr')
            if not os.path.isfile(asrFile): 
                asr_wordcount = None
                asr_exists = False
                asr = ''
                print(f'--no ASR for segment {s}')
            else: 
                asr = open(asrFile,'r').read()
                asr = format_text_for_wer(asr)
                asr_exists = True
                asr_wordcount = len(asr.split())

            transcriptFile = os.path.join(transcriptDir,f'{sessname}_{s}.txt')
            if not os.path.isfile(transcriptFile): 
                transcript_wordcount = None
                transcript_exists = False
                transcript = ''
                print(f'--no transcript for segment {s}')

            else:
                transcript = open(transcriptFile,'r').read()
                transcript = format_text_for_wer(transcript) 
                transcript_exists = True
                transcript_wordcount = len(transcript.split())

            if transcript_exists and asr_exists and transcript_wordcount>0:
                # print(f'\nTRANSCRIPT: {transcript}')
                # print(f'ASR       : {asr}')

                wer = jiwer.wer(transcript.split(), asr.split())
                wer_meas = jiwer.compute_measures(transcript.split(), asr.split())
                aligned, edit_ops =  align_words(transcript.split(), asr.split())
                aligned['segment'] = s
                aligned_segwise.append(aligned)
            else:
                continue

            spk_type = 'TEACHER' if 'Teacher' in speaker else 'STUDENT'    
            seg_data.append([sessname,  s, speaker,spk_type,asr_exists, asr_wordcount, transcript_exists, transcript_wordcount, \
                wer,wer_meas['mer'],wer_meas['substitutions'], wer_meas['deletions'],wer_meas['insertions']])
        aligned_segwise = pd.concat(aligned_segwise)
        aligned_segwise.to_csv(os.path.join(sesspath,f'alignment_segwise_{asrType}_VS_{transcriptType}_{sessname}.csv'), index=False)

        # add session identifiers 
        aligned_segwise['recordingID'] = sessname
        all_sess_alignment.append(aligned_segwise)
        # make Df to store segmentwise metrics
        segwise_wer = pd.DataFrame(seg_data, columns = ['session','segment','speaker','speaker_type','asr_exists','asr_wordcount',' transcript_exists','transcript_wordcount',\
        'wer','mer','substitutions','deletions','insertions'])
        segwise_wer.to_csv(os.path.join(sesspath, f'segwise_wer_{asrType}_VS_{transcriptType}_{sessname}.csv') ) 
        segwise_wer['session'] =     segwise_wer['session'].astype('str') # because pandas saves as an object (??) datatype which can't be grouped by
        segwise_wer['speaker'] =     segwise_wer['speaker'].astype('str') # because pandas saves as an object (??) datatype which can't be grouped by
        segwise_wer['speaker_type'] =     segwise_wer['speaker_type'].astype('str') # because pandas saves as an object (??) datatype which can't be grouped by

        # summarise at the entire session level
        sess_subs = segwise_wer['substitutions'].sum()
        sess_dels = segwise_wer['deletions'].sum()
        sess_ins =  segwise_wer['insertions'].sum()
        sess_N = segwise_wer['transcript_wordcount'].sum()
        sess_meas = wer_from_counts(sess_N, sess_subs, sess_dels, sess_ins)

        # sumarize overall
        sess_summary = pd.DataFrame({'session':[sessname], 'speaker':['all']})
        sess_summary =    pd.concat( [sess_summary ,  wer_df_summary(segwise_wer).to_frame().T ],axis=1).reset_index()
        
        # summarize by speaker
        by_speaker = segwise_wer.groupby('speaker').apply(wer_df_summary).reset_index()
        by_speaker['session'] = sessname
        col = by_speaker.pop("session")
        by_speaker.insert(0, col.name, col)

        sess_summary = sess_summary.append(by_speaker, ignore_index=True).reset_index(drop=True, inplace=False).drop('index', axis=1)

        # sumamrize by speaker TYPE (student/teacher)
        by_speaker_type = segwise_wer.groupby('speaker_type').apply(wer_df_summary).reset_index()
        by_speaker_type['session'] = sessname
        col = by_speaker_type.pop("session") # reorder
        by_speaker_type.insert(0, col.name, col)
        by_speaker_type = by_speaker_type.rename(columns={"speaker_type":"speaker"})

        sess_summary = sess_summary.append(by_speaker_type, ignore_index=True).reset_index(drop=True, inplace=False)

        sess_summary.to_csv(os.path.join(sesspath, f'segwise_wer_SUMMARY_{asrType}_VS_{transcriptType}_{sessname}.csv'), index=False )
        
        all_sess_seg_wer.append(segwise_wer)

# all segments
all_sess_seg_wer = pd.concat(all_sess_seg_wer)

# Summary of WER over all requested sessions

# this is just for codec testing - set by_codec false if does not apply
if by_codec:
    all_sess_seg_wer['codec'] = all_sess_seg_wer['session'].str.rsplit(n=1,pat='_',expand=True)[1]
    all_by_codec = all_sess_seg_wer.groupby('codec',sort=False,as_index=False).apply(wer_df_summary).reset_index()
    all_by_sessXcodec = all_sess_seg_wer.groupby(['session','codec'],sort=False,as_index=False).apply(wer_df_summary).reset_index()
    all_by_speakerXcodec = all_sess_seg_wer.groupby(['speaker','codec'],sort=False,as_index=False).apply(wer_df_summary).reset_index()
    all_by_speakerTypeXcodec = all_sess_seg_wer.groupby(['speaker_type','codec'],sort=False,as_index=False).apply(wer_df_summary).reset_index()

all_overall = wer_df_summary(all_sess_seg_wer)
all_by_sess = all_sess_seg_wer.groupby('session',sort=False,as_index=False).apply(wer_df_summary).reset_index()
all_by_speaker = all_sess_seg_wer.groupby('speaker',sort=False,as_index=False).apply(wer_df_summary).reset_index()
all_by_speakerType = all_sess_seg_wer.groupby('speaker_type',sort=False,as_index=False).apply(wer_df_summary).reset_index()
all_by_sessXspeakerType = all_sess_seg_wer.groupby(['session','speaker_type'],sort=False,as_index=False).apply(wer_df_summary).reset_index()

#pd.concat(all_sess_seg_wer).to_csv( f'results/sesswise_wer_{verstr}.csv',index=False, float_format='%.3f') 
with pd.ExcelWriter(f'results/sesswise_WER_bygroups_{ctlfile}_{asrType}_VS_{transcriptType}.xlsx',engine='xlsxwriter',
                        engine_kwargs={'options': {'strings_to_numbers': True}}) as writer:
    all_overall.to_excel(writer, sheet_name='overall')
    all_by_sess.to_excel(writer, sheet_name='by_session')
    all_by_speaker.to_excel(writer, sheet_name='by_speaker')
    all_by_speakerType.to_excel(writer, sheet_name='by_speakerType')
    all_by_sessXspeakerType.to_excel(writer, sheet_name='by_sessXspeakerType')

    if by_codec:
        all_by_codec.to_excel(writer, sheet_name='by_codec')
        all_by_sessXcodec.to_excel(writer, sheet_name='by_sessXcodec')
        all_by_speakerXcodec.to_excel(writer, sheet_name='by_speakerXcodec')
        all_by_speakerTypeXcodec.to_excel(writer, sheet_name='by_speakerTypeXcodec')
all_sess_alignment = pd.concat(all_sess_alignment)
all_sess_alignment.to_csv(f'results/alignment_all_{ctlfile}_{asrType}_VS_{transcriptType}.csv')