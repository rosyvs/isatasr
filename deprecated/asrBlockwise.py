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
import pathlib
# enter below in terminal: 
# set GOOGLE_APPLICATION_CREDENTIALS="isatasr-91d68f52de4d.json"
client = speech.SpeechClient.from_service_account_file("isatasr-91d68f52de4d.json")

# parser = argparse.ArgumentParser(description='run google_recognizer')
# parser.add_argument('ctl')
# args = parser.parse_args()

args_ctl =os.path.join('configs', 'sg_asr_211012.txt')

def transcribe_file(speech_file, client):
    """Transcribe the given audio file using Google cloud speech."""

    with io.open(speech_file, "rb") as audio_file:
        content = audio_file.read()


    audio = speech.RecognitionAudio(content=content)
    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=16000, # TODO auto detect
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
    sesspath = sesspath.strip()
    wavDir = os.path.join(sesspath, 'blocks')
    sessname = os.path.basename(sesspath)
    asrDir = os.path.join(sesspath,'asr_blockwise')
    print(f'Processing session: {sessname}...')
    # get list of files to transcribe
    wavList = []
    for file in os.listdir(wavDir):
        if not file.endswith('.wav'): continue
        base = re.sub('.wav', '', file)
        wavList.append( base )
    wavList.sort()
    
    # # TEMP DEBUG
    # wavList = wavList[0:4] # run on a small subset to save compute time
    # # \TEMP DEBUG

    # check if asr files already exist, if so, zip them up to make a backup then delete   
    if not os.path.exists(asrDir):
        os.makedirs(asrDir)


    for w in wavList:
        print(f'Processing block: {w}')
        wavfile = os.path.join(wavDir, f'{w}.wav')
        asrfile = os.path.join(asrDir, f'{w}.asr')
        
        # check if asr file already existed, and backup if so
        if os.path.isfile(asrfile):
            now = datetime.now()
            datestr = now.strftime("%d-%m-%Y_%H%M%S")
            zipfile = shutil.make_archive(base_name =os.path.join(asrDir,f'backup_{datestr}_{pathlib.Path(asrfile).stem}'), 
            format='zip', 
            root_dir = asrDir,
            base_dir = os.path.basename(asrfile))

            print(f"ASR already existed. Backed the file up to {zipfile}") 
            os.remove(asrfile)

        # check duration - if >1min split buffer into two then reconcatenate. Needs to be strictly less than 1 minute
        if librosa.get_duration(filename=wavfile) >59: # google is a bit finicky, so go slightly below 1 min
            print(f'{w} Audio >= 1 minute - will split for transcription')
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
        print(f'{w}: {res}')

        # append asr result to full session asr
        with open(asrfile,'w') as outfile:
            outfile.write(res + '\n')

