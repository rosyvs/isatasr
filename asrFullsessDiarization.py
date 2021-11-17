#!/usr/bin/env python3
# asrBlks.py  <ctl file of session paths>
from __future__ import absolute_import
import os
import re
import argparse
import pandas as pd
#from google.cloud import speech
from google.cloud import speech_v1p1beta1 as speech # need the beta for diarizaiton
from google.cloud import storage
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

def transcribe_diarize_file_async(speech_uri, client):
    """Transcribe the given audio file using Google cloud speech."""

    audio =speech.RecognitionAudio(uri=speech_uri); 
    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=16000,
        language_code="en-US",
        enable_speaker_diarization=True,
        enable_word_time_offsets=True,
        diarization_speaker_count=6,
        model="video"
    )

    operation = client.long_running_recognize(config=config, audio=audio)
    print('Waiting for recognition to complete...')
    response = operation.result(timeout=3600) # timeout in seconds, default is too short
    result = response.results[-1] # the final element contains the actual transcript
    best = result.alternatives[0].words # choose most likely result
    
    # loop over each word and format the transcript
    transcript=[]
    speaker_tags = []
    speaker_last = None
    words = []
    for w in best:
        words.append({'start_time' : w.start_time.total_seconds(),
        'end_time' : w.end_time.total_seconds(),
        'speaker_tag' : w.speaker_tag,
        'word' : w.word})
        if (speaker_last == w.speaker_tag):
            transcript.append(w.word)
        else: 
            transcript.append(f"\n{w.start_time.total_seconds()}s (speaker {w.speaker_tag}): {w.word}")
        speaker_tags.append(w.speaker_tag)
        speaker_last = w.speaker_tag
    print(' '.join(transcript))

    return transcript, words

def create_bucket(bucket_name, storage_client):
    """Create a new bucket in specific location with storage class"""
    # bucket_name = "your-new-bucket-name"

    bucket = storage_client.bucket(bucket_name)
    if not bucket.exists():
        bucket.storage_class = "STANDARD"
        bucket = storage_client.create_bucket(bucket, location="us")
        print(f"Created bucket {bucket.name} in {bucket.location} with storage class {bucket.storage_class}")
    else:
        print(f"Bucket {bucket_name} already existed")
    return bucket

def upload_blob(source_file_name, bucket_name, destination_blob_name, storage_client):
    """Uploads a file to the bucket."""
    # The ID of your GCS bucket
    # bucket_name = "your-bucket-name"
    # The path to your file to upload
    # source_file_name = "local/path/to/file"
    # The ID of your GCS object
    # destination_blob_name = "storage-object-name"
    
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(destination_blob_name)
    print(f"Uploading {source_file_name} - please wait.")

    ## For slow upload speed
    storage.blob._DEFAULT_CHUNKSIZE = 2097152 # 10242 MB
    storage.blob._MAX_MULTIPART_SIZE = 2097152 # 2 MB
    blob.upload_from_filename(source_file_name,timeout=600.0)

    print(f"File {source_file_name} uploaded.")

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
        

