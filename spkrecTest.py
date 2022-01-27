import torchaudio
from torch import tensor, cat, squeeze
import wave
import glob
import os
import pandas as pd
import numpy as np
from speechbrain.pretrained import EncoderClassifier, SpeakerRecognition
from speechbrain.utils.metric_stats import EER
# from sklearn.manifold import TSNE

speechbrain_dir = "/Users/roso8920/Dropbox (Emotive Computing)/iSAT/speechbrain/"

#####
verstr = 'spkv_test4_debug'
precompute_targets=True # set to false for tests of sample-sample pairings
model_type = 'ecapa' # 'ecapa' or 'xvect'
# plot_tsne = True # plot clustering of embeddings color coded by label. < TSNE too slow on laptop
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
    verifier = SpeakerRecognition.from_hparams(source=f"{speechbrain_dir}/pretrained_models/spkrec-xvect-voxcelebTEST", 
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

# if plot_tsne:
#     labels_targ = [s + '_ENROLLMENT' for s in result['x1speaker']]
#     xv_targ = squeeze(cat(result['xv1'].to_list())).numpy()

#     labels_sample = result['x2speaker'].to_list()
#     xv_sample = squeeze(cat(result['xv2'].to_list())).numpy()   

#     labels_all = labels_targ + labels_sample
#     xv_all = np.concatenate((xv_targ, xv_sample),axis=0)

#     tsneer = TSNE(2, n_iter=250)
#     tsne_result = tsneer.fit_transform(xv_all)

# evaluate results
positive_scores = tensor(result.loc[result.match,'score'].to_list())
negative_scores = tensor(result.loc[~result.match,'score'].to_list())
result_EER, result_threshold = EER(positive_scores, negative_scores)

print(f'TEST COMPLETE. EER = {result_EER:.3f}, threshold = {result_threshold:.3f}')

result.to_csv(os.path.join('results','speaker_verification','tests', f'{verstr}_{model_type}_result.csv'))

# write summary to txt file
resfile = os.path.join('results','speaker_verification','tests', f'{verstr}_{model_type}_result.txt')

with open(resfile,'w') as outfile:
    outfile.write(f'n_pairs = {len(result)}\n')
    outfile.write(f'n_matches = {len(result[result["match"]])}\n')
    outfile.write(f'n_target_present = {len(result[~result["x2speaker"].str.match("_UNKNOWN")])}\n')
    outfile.write(f'n_unique_targetIDs = {len(set(result["x1speaker"]))}\n')
    outfile.write(f'n_unique_testIDs = {len(set(result["x2speaker"]))}\n')
    outfile.write(f'EER = {result_EER:.3f}\n')
    outfile.write(f'EER_threshold = {result_threshold:.3f}\n')



