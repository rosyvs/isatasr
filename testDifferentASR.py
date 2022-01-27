from speechbrain.pretrained import EncoderDecoderASR
import torch

# Speechbrain pretrained Encoder-Decoder ASR
audio_file =  "/Users/roso8920/Dropbox (Emotive Computing)/iSAT/samples/spkrec/target_segments/target3.wav"
speechbrain_dir = "/Users/roso8920/Dropbox (Emotive Computing)/iSAT/speechbrain/"

asr_model = EncoderDecoderASR.from_hparams(source="speechbrain/asr-crdnn-rnnlm-librispeech", 
    savedir=f"{speechbrain_dir}/pretrained_models/asr-crdnn-rnnlm-librispeech")

asr_model.transcribe_file(audio_file)

# from memory 
normalized = asr_model.load_audio(audio_file)
asr_model.transcribe_batch(normalized, wav_lens=torch.tensor(1.0))



## WAV2VEC2
import os
import torchaudio
import requests
from transformers import Wav2Vec2ForCTC, Wav2Vec2Tokenizer
tokenizer = Wav2Vec2Tokenizer.from_pretrained("facebook/wav2vec2-base-960h")
model = Wav2Vec2ForCTC.from_pretrained("facebook/wav2vec2-base-960h")

