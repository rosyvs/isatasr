# extract labelled audio of interest from full session listed in csv file
# make a .blk file based on the ground-truth utterance boundaries from diarized, timestamped transcript
# each utterance becomes a segment
# segments are blocked to ~1min blocks for comparability to VAD/ sending to REV

# this only works for specific transcripts that were doe manually in a sreadsheet with quirky timestamp format, affects 4 smallgroup files from fall 2021

from numpy import exp
from pydub import AudioSegment
import os
import re
import csv
import pandas as pd
from rosy_asr_utils import strip_punct

# options for writing audio
channels = 1
sample_width = 2
sample_rate = 48000
bit_depth = 16
export_segment_audio = True
blksecs = 59 # Google has refused some blocks if exactly 60 seconds 
utt_padding = 0.0 # because utterances are on seconds resolution, some briefer utterances had the same start and end second - pad if so

annotation_dir = './data/id_labelled/cher_transcripts' # where to find manual annotation csv files
args_ctl =os.path.join('configs', '4SG.txt') # list of session directories to run ASR on

def HHMMSS_to_sec(time_str):
    """Get Seconds from time with milliseconds."""
    if time_str.count(':')==2:
        h, m, s = time_str.split(':')
    elif time_str.count(':')==3:
    # temp fix for files with : as Second/millisecond delimiter and tenths of a second only
        h, m, s, ms = time_str.split(':')
        s = int(s)+float(ms)/10
    else:
        print(f'input string format not supported: {time_str}')
    return int(h) * 3600 + int(m) * 60 + float(s) 

# ITERATE OVER SESSIONS
with open(args_ctl) as ctl:
    sesslist = (line.rstrip() for line in ctl) 
    sesslist = list(line for line in sesslist if line)

for sesspath in sesslist: 
    print(f'sesspath: {sesspath}')
    sesspath = sesspath.strip()
    sessname = os.path.basename(sesspath)
    csvfile = os.path.join(annotation_dir, f'{sessname}_diarized.csv') # read labels from here
    blkmapFile = os.path.join(sesspath, f'{sessname}.blk')
    blkDir= os.path.join(sesspath,'blocks')
    blockTranscriptDir = os.path.join(sesspath,'transcripts_blockwise')
    labelFile = os.path.join(sesspath,f'utt_labels_{sessname}.csv') # will be created
    
    if not os.path.exists(blkDir):
        os.makedirs(blkDir)
    if not os.path.exists(blockTranscriptDir):
        os.makedirs(blockTranscriptDir)
    if export_segment_audio: 
        segDir = os.path.join(sesspath,'segments')
        if not os.path.exists(segDir):
            os.makedirs(segDir)
        segTranscriptDir = os.path.join(sesspath,'transcripts_segwise')
        if not os.path.exists(segTranscriptDir):
                os.makedirs(segTranscriptDir)

    # load session audio
    sess_audio = AudioSegment.from_wav(os.path.join(sesspath, f'{sessname}.wav'))
    # use same defaults as for VAD to block uttern

    with open(csvfile, 'r', newline='') as in_file:
        reader = csv.reader(in_file)
        # skip header
        next(reader)
        curlen = 0.0
        blk = []
        b=0
        s=0
        this_block = AudioSegment.empty() # for raw audio data
        labels = [] # transcript with speaker labels and block/segment numbers
        block_transcript = [] # simple stripped blockwise transcript for computing WER 
        blockTRANSCRIPTfile = os.path.join(blockTranscriptDir,f'{sessname}_{b}.txt' ) 
        open(blockTRANSCRIPTfile, 'w').close() # clear file before appending

        for utt in reader:
            if not ''.join(utt).strip():
                continue
            print(utt)
            start_HHMMSS,speaker,utterance,end_HHMMSS = utt
            # clean up speaker and utterance for ASR
            speaker = re.sub(' ','',speaker)
            speaker = re.sub(':','',speaker)
            utterance_clean = re.sub("[\(\[].*?[\)\]]", " ", utterance)
            utterance_clean = strip_punct(utterance_clean) 
            start_sec = HHMMSS_to_sec(start_HHMMSS)-utt_padding
            end_sec = HHMMSS_to_sec(end_HHMMSS)+utt_padding
            dur = end_sec-start_sec
            seg_audio = sess_audio[start_sec*1000:end_sec*1000]

            if export_segment_audio:
                segWAVfile = os.path.join(segDir,f'{sessname}_{s}.wav' )
                seg_audio.export(segWAVfile, format='wav')
                segTRANSCRIPTfile = os.path.join(segTranscriptDir,f'{sessname}_{s}.txt' )
                with open(segTRANSCRIPTfile, 'w') as outfile:
                    outfile.write(utterance_clean)

            if dur > blksecs:
                print('utterance too long, TODO split')

            if curlen + dur > blksecs:
                # save out complete block
                blkWAVpath = os.path.join(blkDir,f'{sessname}_{b}.wav' )
                this_block.export(blkWAVpath, format='wav')
                # reset/increment counters
                b+=1
                curlen = dur
                this_block = seg_audio
                # clear nextblock text file
                blockTRANSCRIPTfile = os.path.join(blockTranscriptDir,f'{sessname}_{b}.txt' ) 
                open(blockTRANSCRIPTfile, 'w').close()

            else:
                curlen += dur
                this_block += seg_audio
            blockTRANSCRIPTfile = os.path.join(blockTranscriptDir,f'{sessname}_{b}.txt' )
            with open(blockTRANSCRIPTfile, 'a') as outfile:
                outfile.write(utterance_clean + '\n') 
            blk.append((b,s,start_sec,end_sec))
            labels.append((speaker, utterance, b,s,start_sec,end_sec))
            s+=1

        # catch final block! 
        blkWAVpath = os.path.join(blkDir,f'{sessname}_{b}.wav' )
        this_block.export(blkWAVpath, format='wav')


        with open(blkmapFile, 'w') as outfile:
            for b in blk:
                line = ' '.join(str(x) for x in b)
                outfile.write(line + '\n')

        # with open(transcriptFile, 'w') as outfile:
        #     outfile.write('\t'.join(('speaker', 'utterance', 'block','segment','start_sec','end_sec')) + '\n')
        #     for u in transcript:
        #         line = ' '.join(str(x) for x in u)
        #         outfile.write(line + '\n')

    labels= pd.DataFrame(labels, columns = ('speaker', 'utterance', 'block','segment','start_sec','end_sec'))
    labels.to_csv(labelFile,index=False)