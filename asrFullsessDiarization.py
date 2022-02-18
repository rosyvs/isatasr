#!/usr/bin/env python3
# asrBlks.py  <ctl file of session paths>
from __future__ import absolute_import
import os
import re
import argparse
import pandas as pd
from google.cloud import speech, storage
from rosy_asr_utils import transcribe_diarize_file_async, create_bucket, upload_blob

from datetime import datetime
import shutil
import pathlib
# enter below in terminal: 
# set GOOGLE_APPLICATION_CREDENTIALS="isatasr-91d68f52de4d.json"
client = speech.SpeechClient.from_service_account_file("isatasr-91d68f52de4d.json")
storage_client = storage.Client.from_service_account_json("isatasr-91d68f52de4d.json", project='isatasr')

# parser = argparse.ArgumentParser(description='run google_recognizer')
# parser.add_argument('ctl')
# args = parser.parse_args()

args_ctl =os.path.join('configs', 'asr_comparison_mics_onesess.txt')
# args_ctl =os.path.join('configs', 'one_sess.txt')

# ctl has list of paths to sessions to process
#for sesspath in open(args.ctl):
with open(args_ctl) as ctl:
    sesslist = (line.rstrip() for line in ctl) 
    sesslist = list(os.path.normpath(line) for line in sesslist if line)

for sesspath in sesslist: # TEMP DEBUG
    print(f'sesspath: {sesspath}')
    sesspath = sesspath.strip()
    sessname = os.path.basename(sesspath)
    asrDir = os.path.join(sesspath,'asr_fullsess')
    asrfile = os.path.join(asrDir, f"{sessname}_diarized.asr") # this is where the ASR will be saved

    if not os.path.exists(asrDir):
        os.makedirs(asrDir)


        
    wav_local_path = os.path.join(f'{sesspath}/{sessname}.wav')
    wav_uri = f"gs://isat_mictest/{sessname}.wav"
    bucket = storage_client.get_bucket('isat_mictest')
    # check whether file is already uploaded:
    blob = bucket.get_blob(f'{sessname}.wav')
    if blob is None:        
        create_bucket('isat_mictest', storage_client)
        upload_blob(wav_local_path,'isat_mictest',f'{sessname}.wav', storage_client)

    transcript, words = transcribe_diarize_file_async(wav_uri, client)

    # save
    csvfile=os.path.join(asrDir, f"{sessname}_diarized.csv")
    # check if asr file already existed, and backup if so
    if os.path.isfile(asrfile):
        now = datetime.now()
        datestr = now.strftime("%d-%m-%Y_%H%M%S")
        zipfile = shutil.make_archive(base_name =os.path.join(asrDir,f'backup_{datestr}_{pathlib.Path(asrfile).stem}'), 
        format='zip', 
        root_dir = asrDir)
        # ,base_dir = os.path.basename(asrfile))

        print(f"ASR already existed. Backed the file up to {zipfile}") 
        os.remove(asrfile)
    
    words = pd.DataFrame(words).to_csv(csvfile)

    # write whole session asr result
    with open(asrfile,'w') as outfile:
        outfile.write(' '.join(transcript))
        

