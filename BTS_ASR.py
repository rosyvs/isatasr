import os
import json
from google.protobuf.json_format import MessageToDict
from pathlib import Path
from pydub import AudioSegment
from rosy_asr_utils import *
from pydub.audio_segment import AudioSegment, effects
import argparse


def GoogleASRchunk(chunk, clientfile):

    ASR_SRATE = 16000 # sampling rate to use for ASR, will resample the input audio if necessary
    ASR_CHANNELS = 1 # n channels to use for ASR, will adjsut if necessary
    ASR_SAMPLE_WIDTH = 2 # sample width to use for ASR, will adjust if necessary

    client = speech.SpeechClient.from_service_account_file(clientfile)
    
    # load session audio
    audio = AudioSegment.from_file(audiofile)
    audio = audio.set_channels(ASR_CHANNELS).set_sample_width(ASR_SAMPLE_WIDTH).set_frame_rate(ASR_SRATE)

    # normalise segment volume before passing to ASR
    seg_audio = effects.normalize(seg_audio)

    # bytes = io.BytesIO()
    # audio.export(bytes)
    audio_bytes=seg_audio.raw_data

    elif method == 'extra':
        fullresult, res = transcribeExtra_bytestream(audio_bytes, client, ASR_SRATE)
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

if __name__ == "__main__":
    stream_file = ''
    # read from a file as if a stream
    with io.open(stream_file, "rb") as audio_file:
    content = audio_file.read()