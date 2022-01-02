import torchaudio
import wave
import glob
import os
import pandas as pd
from speechbrain.pretrained import EncoderClassifier, SpeakerRecognition

speechbrain_dir = "/Users/roso8920/Dropbox (Emotive Computing)/iSAT/speechbrain/"

#####
verstr = 'spkv_test1_debug'
precompute_targets=True # set to false for tests of sample-sample pairings
model_type = 'ecapa' # 'ecapa' or 'xvect'
#####

test_cfg_file = os.path.join('configs','speaker_verification','tests', f'{verstr}_config.csv')
test_cfg = pd.read_csv(test_cfg_file, index_col=False)

# load models
if model_type == 'ecapa':
    encoder = EncoderClassifier.from_hparams(source="speechbrain/spkrec-ecapa-voxceleb", 
        savedir=f"{speechbrain_dir}/pretrained_models/spkrec-ecapa-voxceleb")
    verifier = SpeakerRecognition.from_hparams(source="speechbrain/spkrec-ecapa-voxceleb", 
        savedir=f"{speechbrain_dir}/pretrained_models/spkrec-ecapa-voxceleb")
if model_type == 'xvect':
    encoder = EncoderClassifier.from_hparams(source="speechbrain/spkrec-xvect-voxceleb", 
        savedir=f"{speechbrain_dir}/pretrained_models/spkrec-xvect-voxceleb")
    SpeakerRecognition.from_hparams(source=f"{speechbrain_dir}/pretrained_models/spkrec-xvect-voxcelebTEST", 
        savedir=f"{speechbrain_dir}/pretrained_models/spkrec-xvect-voxceleb")


if precompute_targets:
    # precompute embeddings for enrollment targets (x1) and save in a dict w filepath as key
    target_files = list(set(test_cfg['x1path'])) 
    target_embeddings = {}
    for t in target_files:
        signal, fs = torchaudio.load(t)
        if not fs == 16000:
            # fs must be 16000 
            to16k = torchaudio.transforms.Resample(fs, 16000)
            signal = to16k(signal)
        target_embeddings[t] = encoder.encode_batch(signal)

# function to run verification on a row of test_cfg DataFrame
def df_spkrVerification(row, encoder, verifier, target_embeddings=None):
    if not target_embeddings:
        fs1 = torchaudio.info(row['x1path']).sample_rate
        x1, fs1 = torchaudio.load(row['x1path'], frame_offset=int(row['x1start_s']*fs1), 
            num_frames=int(fs1*(row['x1end_s']-row['x1start_s'])))

        if not fs1==16000:
            to16k = torchaudio.transforms.Resample(fs1, 16000)
            x1 = to16k(x1)

        xv1 = encoder.encode_batch(x1)
 
    else:
        xv1 = target_embeddings[row['x1path']]
    
    # read and encode test sample
    fs2 = torchaudio.info(row['x2path']).sample_rate
    x2, fs2 = torchaudio.load(row['x2path'], frame_offset=int(row['x2start_s']*fs2), 
        num_frames=int(fs2*(row['x2end_s']-row['x2start_s'])))
    if not fs2==16000:
        to16k = torchaudio.transforms.Resample(fs2, 16000)
        x2 = to16k(x2)
    xv2 = encoder.encode_batch(x2)

    score = verifier.similarity(xv1,xv2)
    print(f'#{row.name}: {row["x1speaker"]} vs {row["x2speaker"]}. Verification score: {score.item()}')
    row['score'] = score.item()
    return row
    
# iterate over test pairings
result = test_cfg.apply(df_spkrVerification,
    encoder=encoder, verifier=verifier, target_embeddings=target_embeddings,
    axis = 1)


