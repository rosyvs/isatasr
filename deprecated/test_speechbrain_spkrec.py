import torchaudio
import glob
import os
import pandas as pd
from speechbrain.pretrained import EncoderClassifier, SpeakerRecognition

speechbrain_dir = "/Users/roso8920/Dropbox (Emotive Computing)/iSAT/speechbrain/"

print('Testing xvector embedding...')
signal, fs = torchaudio.load(f"{speechbrain_dir}/samples/audio_samples/example1.wav")
classifier = EncoderClassifier.from_hparams(source="speechbrain/spkrec-xvect-voxceleb", 
savedir=f"{speechbrain_dir}/pretrained_models/spkrec-xvect-voxceleb")
embeddings = classifier.encode_batch(signal)
print(embeddings[0,0,0:20])
#~~~~~
print('Testing ECAPA embedding...')
signal, fs = torchaudio.load(f"{speechbrain_dir}/samples/audio_samples/example1.wav")
classifier = EncoderClassifier.from_hparams(source="speechbrain/spkrec-ecapa-voxceleb", 
savedir=f"{speechbrain_dir}/pretrained_models/spkrec-ecapa-voxceleb")
embeddings = classifier.encode_batch(signal)
print(embeddings[0,0,0:20])
#~~~~~
# Uses pretrained model
# if it can't fined a local copy, it will download from Huggingface.
# source="speechbrain/spkrec-xvect-voxceleb" is sufficient although this is not the local path
print('Testing XVECT speaker verification using generic source path...')
verification = SpeakerRecognition.from_hparams(source="speechbrain/spkrec-xvect-voxceleb", 
savedir=f"{speechbrain_dir}/pretrained_models/spkrec-xvect-voxceleb")
score, prediction = verification.verify_files(f"{speechbrain_dir}/samples/voxceleb_samples/wav/id10001/1zcIwhmdeo4/00001.wav", 
f"{speechbrain_dir}/samples/voxceleb_samples/wav/id10001/1zcIwhmdeo4/00002.wav")
print(f'...same ID: score {score}, prediction {prediction}')
#~~~~~
# same as above but specifying full local path for pretrained model also works
print('Testing XVECT speaker verification using local pretrained model...')
verification = SpeakerRecognition.from_hparams(source=f"{speechbrain_dir}/pretrained_models/spkrec-xvect-voxcelebTEST", 
savedir=f"{speechbrain_dir}/pretrained_models/spkrec-xvect-voxcelebTEST")
score, prediction = verification.verify_files(f"{speechbrain_dir}/samples/voxceleb_samples/wav/id10001/1zcIwhmdeo4/00001.wav", 
f"{speechbrain_dir}/samples/voxceleb_samples/wav/id10001/1zcIwhmdeo4/00002.wav")
print(f'...same ID: score {score}, prediction {prediction}')
# in both these examples a symlink file is annoyongly made in the current directory, it seems to be using this 

# something weird happens when the files are from different directories - it seems to read from the wrong directory
# e.g. cosine similarity is 1 for 00001.wav one from id10001 and the other from id10002
# referencing a nonexistent file 00002b.wav gives an error
# but renaming id 10002 file 00002 to 00002b.wav and referencing 10002/xxx/00002.wav does not give error and seems to be reading from id 10001 directory
print('Testing XVECT speaker verification on different ID, same filename...')
score2, prediction2 = verification.verify_files(f"{speechbrain_dir}/samples/voxceleb_samples/wav/id10001/1zcIwhmdeo4/00001.wav",
f"{speechbrain_dir}/samples/voxceleb_samples/wav/id10002/xTV-jFAUKcw/00001.wav")
print(f'...different ID, same filename: score {score2}, prediction {prediction2}')

# # it is making an alias for each audio file in the current dir, losing the directory structure which defines what speaker ID the sample came from

# even trying to use my own files it an alias with my isat samples 
# The predictions indicate cosine simialrity is high for different speakers
print('Testing XVECT speaker verification on iSAT targets...')
score3, prediction3 = verification.verify_files(f"{speechbrain_dir}../samples/spkrec/target_segments/target1.wav",
f"{speechbrain_dir}../samples/spkrec/target_segments/target2.wav")
print(f'...different ID, iSAT audio, using verify_files: score {score3}, prediction {prediction3}')

# what if we load these first using torchaudio? 
signal1, fs1 = torchaudio.load("/Users/roso8920/Dropbox (Emotive Computing)/iSAT/samples/spkrec/target_segments/target1.wav")
signal2, fs2 = torchaudio.load("/Users/roso8920/Dropbox (Emotive Computing)/iSAT/samples/spkrec/target_segments/target2.wav")
score, prediction = verification.verify_batch(signal1,signal2)
print(f'...different ID isat audio, using verify_batch: score {score}, prediction {prediction}')
# same score is given as for verify_files which is reassuring, but cosine simialrity is surprisingly high
# no symlinks are made for audio files :-) 



print('Loading pretrained ECAPA using generic source path...')
ecapa_verifier = SpeakerRecognition.from_hparams(source="speechbrain/spkrec-ecapa-voxceleb", 
    savedir=f"{speechbrain_dir}/pretrained_models/spkrec-ecapa-voxceleb")
print('Testing ECAPA speaker verification on iSAT targets...')
signal1, fs1 = torchaudio.load("/Users/roso8920/Dropbox (Emotive Computing)/iSAT/samples/spkrec/target_segments/target2.wav")
signal2, fs2 = torchaudio.load("/Users/roso8920/Dropbox (Emotive Computing)/iSAT/samples/spkrec/target_segments/target3.wav")
score, prediction = ecapa_verifier.verify_batch(signal1,signal2)
print(f'...different ID isat audio, using verify_batch: score {score}, prediction {prediction}')
# ECAPA still gives some false positives but less so. Gives lower cosine similarity overall. 

# what about multiple files in the batch? i.e. all target audio vs all test audio
print('Testing multiple files ECAPA embedding...')
signal, fs = torchaudio.load(f"{speechbrain_dir}/samples/audio_samples/example1.wav")
classifier = EncoderClassifier.from_hparams(source="speechbrain/spkrec-ecapa-voxceleb", 
savedir=f"{speechbrain_dir}/pretrained_models/spkrec-ecapa-voxceleb")
embeddings = classifier.encode_batch(signal)


print('Testing multiple ECAPA verification...')
target_audio_dir =  "/Users/roso8920/Dropbox (Emotive Computing)/iSAT/samples/spkrec/target_segments/"
target_files =  glob.glob(f"{target_audio_dir}*.wav")
results = []


test_audio_dir =  "/Users/roso8920/Dropbox (Emotive Computing)/iSAT/samples/spkrec/test_segments/"
test_files =  glob.glob(f"{test_audio_dir}*.wav")


# I don't think the tensor can have diffrent lengths - perhaps this would work with same -length files
for t1 in target_files:
    for t2 in test_files:
        t1_id = os.path.basename(t1)
        t2_id = os.path.basename(t2)

        signal1, fs1 = torchaudio.load(t1)
        signal2, fs2 = torchaudio.load(t2)
        score, prediction = ecapa_verifier.verify_batch(signal1,signal2)
        print(f'target:{t1_id} \ntest:{t2_id}. \n    score {score}, prediction {prediction}')

        results.append((t1_id, t2_id, score, prediction))

results = pd.DataFrame(results)


# Torchaudio.load can be used for extracting just required segments of audio from file
# you need to know the sample rate in advance
fs = 16000
frame_offset, num_frames = fs*0.5, fs*1 # extract 0.5-1.5 seconds
signal1, fs1 = torchaudio.load(t1, frame_offset=frame_offset, num_frames=num_frames)
signal2, fs2 = torchaudio.load(t2, frame_offset=frame_offset, num_frames=num_frames)

# or you can slice the tensor but this this less efficient
waveform1, fs = torchaudio.load(t1)
frame_offset, num_frames = fs*0.5, fs*1 
waveform1 = waveform1[:, frame_offset:frame_offset+num_frames]