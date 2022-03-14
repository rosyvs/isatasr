from __future__ import absolute_import
from pydub.audio_segment import AudioSegment, effects
import os
import io
import re
import argparse
import pandas as pd
import math
from datetime import datetime
import shutil
from rosy_asr_utils import *
import json
from rev_ai import apiclient
from rev_ai.models import MediaConfig
from rev_ai.streamingclient import RevAiStreamingClient
import io
import time

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Concatenate utterances before transcribing
# Split results back to utterances using word-level timing  
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

config = open('/Users/roso8920/Dropbox (Emotive Computing)/iSAT/rev_auth_token.txt','r')
auth_token = config.readline().rstrip()



# create your client
client = apiclient.RevAiAPIClient(auth_token)
# mediaconfig = MediaConfig("audio/x-raw", "interleaved", 16000, "S16LE", 1)
# client = RevAiStreamingClient(auth_token, mediaconfig)

asr_srate = 16000 # sampling rate to use for ASR, will resampel the input audio if necessary

args_ctl =os.path.join('configs', 'deepSample2b.txt') # list of session directories to run ASR on
# ctl has list of paths to sessions to process


tmpWavDir = './workingWavs'
if not os.path.exists(tmpWavDir):
    os.makedirs(tmpWavDir)

with open(args_ctl) as ctl:
    sesslist = (line.rstrip() for line in ctl) 
    sesslist = list(line for line in sesslist if line)

for sesspath in sesslist: 
    print(f'sesspath: {sesspath}')
    sesspath = sesspath.strip()
    sessname = os.path.basename(sesspath)
    wavfile = os.path.join(sesspath, f'{sessname}.wav')
    asrDir = os.path.join(sesspath,'asr_rev_concat_segwise')
    # asrBlockDir = asrDir + '_reblocked' # segment-wise ASR will be concatenated to distinguish from ASR results run on entire block
    asrFullDir = os.path.join(sesspath,'asr_rev_concat_full') # where full session asr will be stored
    jsonDir = os.path.join(sesspath,'JSON_rev_concat')

    asrFullFile = os.path.join(asrFullDir,f"{sessname}.asr") # full session ASR results
    if os.path.exists(asrFullFile):
        open(asrFullFile, 'w').close() # clear file before appending
    blkmapFile = os.path.join(sesspath,f'{sessname}.blk')

    audio = AudioSegment.from_file(wavfile)
    srate = audio.frame_rate
    if not asr_srate == srate:
        audio = audio.set_frame_rate(asr_srate)
        srate = asr_srate

    os.makedirs(asrDir, exist_ok=True)
    # if not os.path.exists(asrBlockDir):
    #     os.makedirs(asrBlockDir)
    os.makedirs(asrFullDir, exist_ok=True)
    os.makedirs(jsonDir, exist_ok=True)

    concat_audio = AudioSegment.empty()
    concat_timings = {}
    concatStart = 0
    for line in open(blkmapFile):
        line = line.strip()
        if not line: continue
        b, s, segStart, segEnd = line.split()
        b = int(b)
        s = int(s)
        segStart = float(segStart)
        segEnd= float(segEnd)

        # extract segment 
        seg_audio = audio[segStart*1000:segEnd*1000]

        seg_audio = effects.normalize(seg_audio)

        concat_audio +=seg_audio
        concatEnd = concatStart + segEnd - segStart
        concat_timings[s] = (concatStart,concatEnd)
        concatStart = concatEnd # increment timing counter for next segment


    # bytes=concat_audio.raw_data

    # gonan have to write out the concatenated audio and read in as a file
    concat_audio.export(os.path.join(tmpWavDir, f'{sessname}.wav'), format='wav')
    
    # MEDIA_GENERATOR = [bytes]
    # response_generator = client.start(MEDIA_GENERATOR)

    print(f'Running ASR for {s} segments conncatenated...')
    # send a local file
    job = client.submit_job_local_file(os.path.join(tmpWavDir, f'{sessname}.wav'))


    time.sleep(10) # idk, it takes a moment to make the job
    
    job_details = client.get_job_details(job.id)
    while str(job_details.status) != "JobStatus.TRANSCRIBED":
        time.sleep(10)
        # check job status
        job_details = client.get_job_details(job.id)
        print(job_details.status) 

    print("done", job_details.status)

    # retrieve transcript as text
    transcript_text = client.get_transcript_text(job.id)
    print(transcript_text)

    # retrieve transcript as JSON
    transcript_json = client.get_transcript_json(job.id)

    # fullresult
    jsonFile = os.path.join(jsonDir, f"{sessname}.json")

    with open(jsonFile, "w") as jf:
        json.dump(transcript_json, jf, indent=4)

    # get words and timings
    # asrtext =  ''.join([r['value'] for r in transcript_json['monologues'][0]['elements']])
    asrtext =  ''.join([r['value'] for m in transcript_json['monologues'] for r in m['elements'] ])

    # append all ASR results to a single file
    with open(asrFullFile,'a') as outfile:
        outfile.write(asrtext + '\n')

    word_timings = [(r['value'], r['ts'], r['end_ts']) for m in transcript_json['monologues'] for r in m['elements']  if r['type'] == 'text']

    for s, (start, end) in concat_timings.items():

        seg_words = [w[0] for w in word_timings if w[2]>start and w[1]<end]
        print((s, ' '.join(seg_words)))

        # write segmentwise ASR result
        asrfile = os.path.join(asrDir, f"{sessname}_{s}.asr")
        with open(asrfile,'w') as outfile:
            outfile.write(' '.join(seg_words) + '\n')


#### Stupid addon to read the result from .json file...