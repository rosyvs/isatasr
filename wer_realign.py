import os
import re
from numpy.core.shape_base import block
import pandas as pd
import jiwer 

# loop over sessions in control file and compute WER for any with both ASR and REV transcripts
args_ctl = 'wer_ctl1.txt'

# this version works with segments that do not align to the REV transcript blocks.
# we will   


# JIWER has some nice formatting options
transformation = jiwer.Compose([
    jiwer.ToLowerCase(),
    jiwer.RemoveMultipleSpaces(),
    jiwer.RemoveWhiteSpace(replace_by_space=False),
    jiwer.SentencesToListOfWords(word_delimiter=" "),
    jiwer.RemoveEmptyStrings(),
    jiwer.RemovePunctuation()
]) 

for sesspath in open(args_ctl): # TEMP DEBUG

    sesspath = sesspath.strip()
    sessname = os.path.basename(sesspath)
    asrDir = os.path.join(sesspath,'asr_blockwise')
    transcriptDir = os.path.join(sesspath,'transcripts')
    blksDir =  os.path.join(sesspath,'blocks')

    # get list of blocks
    blklist = []
    for file in os.listdir(blksDir):
        if not file.endswith('.wav'): continue
        base = re.sub('.wav', '', file)
        field = base.split('_')
        sg = field[len(field)-1]
        blklist.append( int(sg) )
    blklist.sort()

    block_data = []
    # loop over blocks
    for b in blklist:
        asrFile = os.path.join(asrDir,f'{sessname}_{b}.asr')
        if not os.path.isfile(asrFile): 
            asr_wordcount = 0
            asr_exists = False
        else: 
            asr = open(asrFile,'r').read().replace('\n',' ')
            asr = re.sub('\s+',' ',asr)
            asr_wordcount = len(asr.split())
            asr_exists = True



        transcriptFile = os.path.join(transcriptDir,f'{sessname}_{b}.txt')
        if not os.path.isfile(transcriptFile): 
            transcript_wordcount = 0
            transcript_exists = False
        else:
            transcript = open(transcriptFile, 'r').readlines()
            transcript = open(transcriptFile,'r').read().replace('\n',' ')
            transcript = re.sub('\s+',' ',transcript)
            transcript_wordcount = len(transcript.split())
            transcript_exists = True
        
        if transcript_exists and asr_exists:
            wer = jiwer.wer(transcript, asr, truth_transform=transformation, hypothesis_transform=transformation)
        else:
            wer = -1

        block_data.append([sessname, b, asr_exists, asr_wordcount, transcript_exists, transcript_wordcount, wer])
    # make Df to store blockwise metrics
    block_summary = pd.DataFrame(block_data, columns = ['session','block','asr_exists','asr_wordcount',' transcript_exists','transcript_wordcount','wer'])
    block_summary.to_csv(file=os.path.join(sesspath, 'blockwise_wer.csv')
    
    # # get list of blocks with ASR
    # asrList=[]
    # for file in os.listdir(asrDir):
    #     if not file.endswith('.asr')
    #     base = re.sub('.asr', '', file)
    #     field = base.split('_')
    #     sg = field[len(field)-1]
    #     asrList.append( int(sg) )

    #     # get list of blocks with REV transcript
    # transcriptList=[]
    # for file in os.listdir(transcriptDir):
    #     if not file.endswith('.txt') or file.endswith('diarized.txt'): continue
    #     base = re.sub('.txt', '', file)
    #     field = base.split('_')
    #     sg = field[len(field)-1]
    #     transcriptList.append( int(sg) )

