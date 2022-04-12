import os
import json
from unittest import result
from google.protobuf.json_format import MessageToDict
from pathlib import Path
from pydub import AudioSegment
from pydub.utils import make_chunks
from time import sleep
from rosy_asr_utils import *
from pydub.audio_segment import AudioSegment, effects
from google.cloud import speech_v1 as speech1 # need this version for confidence






def googleASR(bytes, client,srate):
    """Transcribe the given audio bytestream using Google cloud speech, returning full output 
    including confidence, timing, diarization, alternatives"""

    audio = speech1.RecognitionAudio(content=bytes)
    config = speech1.RecognitionConfig(
        encoding=speech1.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=srate,
        enable_word_time_offsets=True,
        language_code="en-US",
        use_enhanced=True,
        model="video",
        enable_word_confidence = True,
        max_alternatives = 30)
        
    response = client.recognize(config=config, audio=audio)
    # GET RESULT AS DICT 
    result_dict = MessageToDict(response._pb)
    transcript=[]
    for r in response.results:
        # The first alternative is the most likely one for this portion.
        best = r.alternatives[0].transcript
        transcript.append(best)

    return(result_dict, transcript)

def reformat_result(result_dict, segmentID, previous_result=None):

    result_reformatted = result_dict #TODO


    return result_reformatted


def ASRchunk(chunk_bytes, chunk_metadata: dict, client_file: str):
    """chunk_bytes: PCM data
    chunk_metadata: dict containing the following keys
     'sample_width':int 
     'sample_rate' : int 
     'n_channels': int '
     'segmentID': str 
     'clientfile' json file containing google cloud services credentials
     
     """

    client = speech.SpeechClient.from_service_account_file(client_file)

    ASR_SRATE = 16000 # sampling rate to use for ASR, will resample the input audio if necessary
    ASR_CHANNELS = 1 # n channels to use for ASR, will adjsut if necessary
    ASR_SAMPLE_WIDTH = 2 # sample width to use for ASR, will adjust if necessary

    
    # convert chunk to required format for ASR
    audio = AudioSegment(chunk_bytes, sample_width=chunk_metadata['sample_width'], 
                                      frame_rate=chunk_metadata['sample_rate'],
                                      channels=chunk_metadata['n_channels'] )
    audio = audio.set_channels(ASR_CHANNELS).set_sample_width(ASR_SAMPLE_WIDTH).set_frame_rate(ASR_SRATE)

    # normalise segment volume before passing to ASR
    audio = effects.normalize(audio)

    audio_bytes=audio.raw_data

    result_dict, transcript = googleASR(audio_bytes, client, ASR_SRATE)
    print(transcript)
    result_reformatted = reformat_result(result_dict, chunk_metadata)
    return result_reformatted



if __name__ == "__main__":
    sample_file = 'data/EXAMPLE/EXAMPLE.MOV'
    client_file = "isatasr-91d68f52de4d.json"
    sample_audio = AudioSegment.from_file(sample_file)
    chunk_dur_sec = 10

    chunks = make_chunks(sample_audio, chunk_dur_sec*1000)
    
    # get chunk metadata from audioSegment
    chunk_metadata = {'sample_width': sample_audio.sample_width,
                      'sample_rate': sample_audio.frame_rate,
                      'n_channels': sample_audio.channels }

    for i, chunk in enumerate(chunks):
        # read successive chunks from a file as if a stream
        chunk_name = sample_file + f'_{i}'
        print(f'segmentID: {chunk_name}')
        chunk_metadata['segmentID'] = chunk_name


        # TODO check if any previous audio in the buffer and prepend to the bytes if so

        chunk_bytes = chunk.raw_data

        # do ASR on the chunk
        response, transcript = ASRchunk(chunk_bytes, chunk_metadata=chunk_metadata, client_file = client_file)

        # TODO add final chunklet of audio to buffer for next iteration

        # output result as dict ready for JSON 

        # also print ASR result to STDOUT

        # simulate waiting for stream
        sleep(chunk_dur_sec)