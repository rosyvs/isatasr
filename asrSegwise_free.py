#!/usr/bin/env python3
# asrBlks.py  <ctl file of session paths>
import speech_recognition as sr
import os
import io
import re
import argparse
import pandas as pd


parser = argparse.ArgumentParser(description='run google_recognizer')
parser.add_argument('ctl')
args = parser.parse_args()

# # TEMP DEBUG
# args_ctl = 'seg_ctl1.txt'
# # \TEMP DEBUG
def transcribe_file(speech_file, client):
    """Transcribe the given audio file using Google cloud speech."""
    with io.open(speech_file, "rb") as audio_file:
        content = audio_file.read()

    audio = speech.RecognitionAudio(content=content)
    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=16000,
        language_code="en-US",
    )

    response = client.recognize(config=config, audio=audio)

    # Each result is for a consecutive portion of the audio. Iterate through
    # them to get the transcripts for the entire audio file.
    for result in response.results:
        # The first alternative is the most likely one for this portion.
        print(u"Transcript: {}".format(result.alternatives[0].transcript))


# ctl has list of paths to sessions to process
for sesspath in open(args.ctl):
    sesspath = sesspath.strip()
    tagfile = os.path.join(sesspath, 'seg.tag')
    wavDir = os.path.join(sesspath, 'segments')
    sessName = os.path.basename(sesspath)
    asrDir = os.path.join(sesspath,'asr_segwise')
    blkMap = pd.read_csv(os.path.join(sesspath,f'{sessName}.blkmap'), sep='\s+', header=None, names = ['segments','block'])
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
    
    if not os.path.exists(asrDir):
        os.makedirs(asrDir)
    
    for s in wavList:
        wavfile = '%s/%s_%d.wav' % (wavDir,sessName,s)

        # Initialize the recognizer
        r = sr.Recognizer()
 
        # Traverse the audio file and listen to the audio
        with sr.AudioFile(wavfile) as source:
            audio_listened = r.listen(source)
 
        # Try to recognize the listened audio
        # And catch expections.
        try:    
            rec = r.recognize_google(audio_listened)
 
            print('%s_%d' % (sessName,s), rec)

            #fh.write(rec+" ")
 
        # If google could not understand the audio
        except sr.UnknownValueError:
            print(f"Could not understand audio for segment: {sessName}_{s}")
            rec=''
        # If the results cannot be requested from Google.
        # Probably an internet connection error.
        except sr.RequestError as e:
            print("Could not request results.")
            rec=''

        # identify block for this segment
        b = s2bMap[s]

        # append segment asr transcripts to the coresponding block
        asrfile = os.path.join(asrDir, f"{sessName}_{s}.asr")
        with open(asrfile,'w') as outfile:
            outfile.write(rec + '\n')

        asrBlockDir = os.path.join(sesspath,'asr_blockwise')
        if not os.path.exists(asrBlockDir):
            os.makedirs(asrBlockDir)
        # append segment asr transcripts to the coresponding block
        asrblockfile = os.path.join(asrBlockDir, f"{sessName}_{b}.asr")
        with open(asrblockfile,'a') as outfile:
            outfile.write(rec + '\n')

