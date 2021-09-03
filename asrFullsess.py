#!/usr/bin/env python3
# asrBlks.py  <ctl file of session paths>
from __future__ import absolute_import
import speech_recognition as sr
import os
import io
import re
import argparse
import pandas as pd
from google.cloud import speech
import soundfile 
import librosa
import math
from datetime import datetime
import shutil
# enter below in terminal: 
# set GOOGLE_APPLICATION_CREDENTIALS="isatasr-91d68f52de4d.json"
client = speech.SpeechClient.from_service_account_file("isatasr-91d68f52de4d.json")

# parser = argparse.ArgumentParser(description='run google_recognizer')
# parser.add_argument('ctl')
# args = parser.parse_args()

args_ctl =os.path.join('configs', 'asr_comparison_mics_onesess.txt')
# args_ctl =os.path.join('configs', 'one_sess.txt')

def transcribe_file(speech_file, client):
    """Transcribe the given audio file using Google cloud speech."""

    with io.open(speech_file, "rb") as audio_file:
        content = audio_file.read()


    audio = speech.RecognitionAudio(content=content)
    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=16000,
        language_code="en-US",
        model="video"
    )
    result=[]
    try:
        response = client.recognize(config=config, audio=audio)

    # Each result is for a consecutive portion of the audio. Iterate through
    # them to get the transcripts for the entire audio file.
        for r in response.results:
            # The first alternative is the most likely one for this portion.
            best = r.alternatives[0].transcript
            result.append(best)
            print(best)
    except Exception as ex:
        print(f"An exception of type {type(ex).__name__} occurred.")
        raise ex

    return('\n'.join(result))

# ctl has list of paths to sessions to process
#for sesspath in open(args.ctl):
with open(args_ctl) as ctl:
    sesslist = (line.rstrip() for line in ctl) 
    sesslist = list(line for line in sesslist if line)

for sesspath in sesslist: # TEMP DEBUG
    print(f'sesspath: {sesspath}')
    sesspath = sesspath.strip()
    tagfile = os.path.join(sesspath, 'seg.tag')
    wavDir = os.path.join(sesspath, 'segments')
    sessname = os.path.basename(sesspath)
    asrDir = os.path.join(sesspath,'asr_segwise')
    asrBlockDir = os.path.join(sesspath,'asr_blockwise')
    blkMap = pd.read_csv(os.path.join(sesspath,f'{sessname}.blkmap'), sep='\s+', header=None, names = ['segments','block'])
    s2bMap = {}
    for _, row in blkMap.iterrows():
        block = row['block']
        segments = [int(s) for s in row['segments'].split(',')]
        for i in segments:
            s2bMap[i] = block

    # get list of files to transcribe
    wavList = []
    for file in os.listdir(wavDir):
        if not file.endswith('.wav'): continue
        base = re.sub('.wav', '', file)
        field = base.split('_')
        sg = field[len(field)-1]
        wavList.append( int(sg) )
    wavList.sort()
    
    # # TEMP DEBUG
    # wavList = wavList[0:4] # run on a small subset to save compute time
    # # \TEMP DEBUG

    # check if asr files already exist, if so, zip them up to make a backup then delete   
    if not os.path.exists(asrDir):
        os.makedirs(asrDir)
    else: 
        asr_already_here = os.listdir(asrDir)
        if len(asr_already_here) == 0:
            print("ASR dir already existed but is empty. Will proceed.")
        else:
            now = datetime.now()
            datestr = now.strftime("%d-%m-%Y_%H%M%S")
            print(f"ASR dir already existed AND contains .asr files. Will back these up to {datestr}.zip then delete .asr files") 
            shutil.make_archive(f'{asrDir}_backup_{datestr}', 'zip', asrDir)
            for f in asr_already_here:
                print(f'...deleting {f}')
                os.remove(os.path.join(asrDir, f))

    if not os.path.exists(asrBlockDir):
        os.makedirs(asrBlockDir)
    else: 
        asr_already_here = os.listdir(asrBlockDir)
        if len(asr_already_here) == 0:
            print("ASR blockwise dir already existed but is empty. Will proceed.")
        else:
            now = datetime.now()
            datestr = now.strftime("%d-%m-%Y_%H%M%S")
            print(f"ASR blockwise dir already existed AND contains .asr files. Will back these up to {datestr}.zip then delete .asr files") 
            shutil.make_archive(f'{asrBlockDir}_backup_{datestr}', 'zip', asrBlockDir)
            for f in asr_already_here:
                print(f'...deleting {f}')
                os.remove(os.path.join(asrBlockDir, f))

    for s in wavList:
        res=''

    # identify block for this segment
        try:
            b = s2bMap[s]
        except: 
            print(f'no block found for segment: {sessname} {s}')
            continue
        
        wavfile = os.path.join(wavDir, f'{sessname}_{s}.wav')
        # check duration - if >1min split buffer into two then reconcatenate. in future would be nice to do on stream rather than writing wav
        if librosa.get_duration(filename=wavfile) >59:
            print(f'{sessname}_{s} Audio > 1 minute - will split for transcription')
            tmpWavDir = './workingWavs'
            if not os.path.exists(tmpWavDir):
                os.makedirs(tmpWavDir)
            wavaudio , fs = soundfile.read(wavfile)
            nfiles = math.ceil(wavaudio.size/(59*fs))
            print(f'splitting into {nfiles} files')
            reslist=[]
            for i in range(0,nfiles):
                truncated = wavaudio[i*59*fs:(i+1)*59*fs]
                wavfile_trunc = os.path.join(tmpWavDir,f'{os.path.basename(wavfile)}-{i}.wav')
                soundfile.write(wavfile_trunc,truncated, fs)
                reslist.append(transcribe_file(wavfile_trunc, client))
            res = ' '.join(reslist)
        else:    
            res = transcribe_file(wavfile, client)
        print('%s_%d' % (sessname,s), res)

        # write segmentwise asr result
        asrfile = os.path.join(asrDir, f"{sessname}_{s}.asr")
        with open(asrfile,'w') as outfile:
            outfile.write(res + '\n')

        # append segment asr transcripts to the coresponding block
        asrblockfile = os.path.join(asrBlockDir, f"{sessname}_{b}.asr")
        with open(asrblockfile,'a') as outfile:
            outfile.write(res + '\n')

