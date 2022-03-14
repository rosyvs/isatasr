from __future__ import absolute_import
from pydub.audio_segment import AudioSegment, effects
import os
from datetime import datetime
import shutil
from rosy_asr_utils import *

from transformers import Wav2Vec2Processor, HubertForCTC, Wav2Vec2ForCTC, Wav2Vec2ProcessorWithLM
# from datasets import load_dataset
import soundfile as sf
import torch
import torchaudio
 
# load the model and preprocessor
# processor = Wav2Vec2ProcessorWithLM.from_pretrained("patrickvonplaten/wav2vec2-base-100h-with-lm")
# model = Wav2Vec2ForCTC.from_pretrained("patrickvonplaten/wav2vec2-base-100h-with-lm")
# language_model=True
# model_tag = 'w2v2LM'

processor = Wav2Vec2Processor.from_pretrained("facebook/hubert-large-ls960-ft")
model = HubertForCTC.from_pretrained("facebook/hubert-large-ls960-ft")
language_model=False
model_tag = 'hubert'
 
asr_srate = 16000 # sampling rate to use for ASR, will resampel the input audio if necessary

args_ctl =os.path.join('configs', 'deepSample2.txt') # list of session directories to run ASR on
# ctl has list of paths to sessions to process
with open(args_ctl) as ctl:
    sesslist = (line.rstrip() for line in ctl) 
    sesslist = list(line for line in sesslist if line)

for sesspath in sesslist: 
    print(f'sesspath: {sesspath}')
    sesspath = sesspath.strip()
    sessname = os.path.basename(sesspath)
    wavfile = os.path.join(sesspath, f'{sessname}.wav')
    asrDir = os.path.join(sesspath,f'asr_{model_tag}_segwise')
    # asrBlockDir = asrDir + '_reblocked' # segment-wise ASR will be concatenated to distinguish from ASR results run on entire block
    asrFullDir = os.path.join(sesspath,f'asr_{model_tag}_full') # where full session asr will be stored
    asrFullFile = os.path.join(asrFullDir,f"{sessname}.asr") # full session ASR results
    if os.path.exists(asrFullFile):
        open(asrFullFile, 'w').close() # clear file before appending
    blkmapFile = os.path.join(sesspath,f'{sessname}.blk')

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

        # extract segment as torchaudio and send only this to ASR
        fs1 = torchaudio.info(wavfile).sample_rate
        audio_tensor, fs1 = torchaudio.load(wavfile, frame_offset=int(segStart*fs1), 
            num_frames=int(fs1*(segEnd-segStart)) )

        if not fs1==asr_srate:
            to16k = torchaudio.transforms.Resample(fs1, 16000)
            audio_tensor = to16k(audio_tensor)

 
        # take argmax and decode
        with torch.no_grad():
            logits = model(audio_tensor).logits
        predicted_ids = torch.argmax(logits, dim=-1)
        
        if language_model:
            transcription = processor.batch_decode(logits.numpy()).text

        else:
            transcription = processor.batch_decode(predicted_ids)


        print(transcription)
            
        # write segmentwise ASR result
        asrfile = os.path.join(asrDir, f"{sessname}_{s}.asr")
        with open(asrfile,'w') as outfile:
            outfile.write(' '.join(transcription) + '\n')

        # # append segment ASRresults to the corresponding block
        # asrblockfile = os.path.join(asrBlockDir, f"{sessname}_{b}.asr")
        # with open(asrblockfile,'a') as outfile:
        #     outfile.write(res + '\n')

        # append all ASR results to a single file
        with open(asrFullFile,'a') as outfile:
            outfile.write(' '.join(transcription) + '\n')

