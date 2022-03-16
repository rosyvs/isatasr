import os
import json
from google.protobuf.json_format import MessageToJson, MessageToDict
from pathlib import Path
from pydub import AudioSegment
from rosy_asr_utils import *
from pydub.audio_segment import AudioSegment, effects
import argparse


parser = argparse.ArgumentParser(description='Run ASR on segments')
parser.add_argument('filelist', help='path to text file containing list of file paths to transcribe')
parser.add_argument('-m','--method', default='extra',help='Google ASR type: standard (video model), \
    extra (video model + confidence, timing,alternatives), short (streaming),')
args = parser.parse_args()

# # DEBUG 
# import sys
# parser = argparse.ArgumentParser(description='Run ASR on segments')
# sys.argv = ['asrSegwise.py', './configs/EXAMPLE.txt']
# args = parser.parse_args()
# # \DEBUG

client = speech.SpeechClient.from_service_account_file("isatasr-91d68f52de4d.json") 
asr_srate = 48000 # sampling rate to use for ASR, will resample the input audio if necessary
asr_channels = 1 # n channels to use for ASR, will adjsut if necessary
asr_sample_width = 2 # sample width to use for ASR, will adjust if necessary

# ctl has list of paths to sessions to process
with open(args.filelist) as ctl:
    sesslist = (line.rstrip() for line in ctl) 
    sesslist = list(line for line in sesslist if line)

for sesspath in sesslist: 
    print(f'sesspath: {sesspath}')
    print(f'Transcribing using Google with method "{args.method}"...')

    sesspath = sesspath.strip()
    sessname = os.path.basename(sesspath)
    wavfile = os.path.join(sesspath, f'{sessname}.wav')
    asrDir = os.path.join(sesspath,f'asr_{"short_" if args.method=="short" else "" }segwise')
    # asrBlockDir = asrDir + '_reblocked' # segment-wise ASR will be concatenated to distinguish from ASR results run on entire block
    asrFullDir = os.path.join(sesspath,f'asr_{"short_" if args.method=="short" else "" }full') # where full session asr will be stored
    asrFullFile = os.path.join(asrFullDir,f"{sessname}.asr") # full session ASR results
    if os.path.exists(asrFullFile):
        open(asrFullFile, 'w').close() # clear file before appending
    blkmapFile = os.path.join(sesspath,f'{sessname}.blk')

    # prefer wav if it exists, otherwise choose another audio file
    if os.path.exists(os.path.join(sesspath, f'{sessname}.wav')   ):
        audiofile = os.path.join(sesspath, f'{sessname}.wav')   
    else:
        audiofiles = [f for f in os.listdir(sesspath) if f.split('.')[-1] in ['MOV', 'mov', 'WAV', 'wav', 'mp4', 'mp3', 'm4a', 'aac', 'flac', 'alac', 'ogg']]
        if audiofiles:
            if len(audiofiles) > 1: # choose one format to proceed with
                for f in audiofiles:
                    if f.split('.')[-1] in ['wav', 'WAV']:
                        audiofile = os.path.join(sesspath, f)
                        continue
                    else:
                        audiofile = os.path.join(sesspath, f)
        else:
            print('WARNING: no audio files found. Skipping...')
            continue    
    aud_type = Path(audiofile).suffix
    print(f'Input media type: {aud_type}')

    # load session audio
    audio = AudioSegment.from_file(audiofile)
    # sample_rate = sess_audio.frame_rate
    # channels = sess_audio.channels

    # # set sample rate and channels 
    # sess_audio = sess_audio.set_frame_rate(vad_srate)
    #     srate = asr_srate 
    audio = audio.set_channels(asr_channels).set_sample_width(asr_sample_width).set_frame_rate(asr_srate)

    os.makedirs(asrDir, exist_ok=True)
    os.makedirs(asrFullDir, exist_ok=True)

    for line in open(blkmapFile):
        line = line.strip()
        if not line: continue
        b, s, segStart, segEnd = line.split()
        b = int(b)
        s = int(s)
        segStart = float(segStart)
        segEnd= float(segEnd)
        print(f'Processing segment: {s}')

        # extract segment and send only this to ASR
        seg_audio = audio[segStart*1000:segEnd*1000]

        # normalise segment volume before passing to ASR
        seg_audio = effects.normalize(seg_audio)

        # bytes = io.BytesIO()
        # audio.export(bytes)
        audio_bytes=seg_audio.raw_data
        if args.method == 'short':
            res = transcribe_short_bytestream(audio_bytes, client, asr_srate)

        elif args.method == 'standard': # standard
            res = transcribe_bytestream(audio_bytes, client, asr_srate)

        elif args.method == 'extra':
            fullresult, res = transcribeExtra_bytestream(audio_bytes, client, asr_srate)
            result_json = MessageToDict(fullresult._pb)
            jsonDir = os.path.join(sesspath,'JSON_segwise')
            os.makedirs(jsonDir, exist_ok=True)
            jsonFile = os.path.join(jsonDir, f"{sessname}_{s}.json")
            with open(jsonFile, "w") as jf:
                json.dump(result_json, jf, indent=4)

        # write segmentwise ASR result
        asrfile = os.path.join(asrDir, f"{sessname}_{s}.asr")
        with open(asrfile,'w') as outfile:
            outfile.write(res + '\n')

        # # append segment ASRresults to the corresponding block
        # asrblockfile = os.path.join(asrBlockDir, f"{sessname}_{b}.asr")
        # with open(asrblockfile,'a') as outfile:
        #     outfile.write(res + '\n')

        # append all ASR results to a single file
        with open(asrFullFile,'a') as outfile:
            outfile.write(res + '\n')

