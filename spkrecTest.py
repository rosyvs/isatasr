import torchaudio
from torch import tensor, cat, squeeze
import os
import pandas as pd
import numpy as np
from speechbrain.pretrained import EncoderClassifier, SpeakerRecognition
from speechbrain.utils.metric_stats import EER
# from sklearn.manifold import TSNE
import re
import random
import json
import pprint
from pydub.audio_segment import AudioSegment, effects
from sklearn.metrics import accuracy_score, confusion_matrix, recall_score, precision_score
from rosy_asr_utils import get_overlap


def get_all_spkr_labels(labels, start_s, end_s):
    # pull speaker label for a defined audio interval
    # allowing for multiple labels per interval
    matched_utt = (labels['start_sec'] < end_s) & (labels['end_sec'] > start_s)
    sample_labels = labels.loc[matched_utt, 'speaker'].unique().tolist()
    if not any(matched_utt):
        sample_labels = ['_UNKNOWN']
    return sample_labels

def get_best_spkr_label(labels, start_s, end_s):
    # pull speaker label for a defined audio interval
    # choose majority label in case of overlap
    overlap_duration = np.maximum(0.0,labels['end_sec'].clip(upper=end_s) - labels['start_sec'].clip(lower=start_s))
    if max(overlap_duration) == 0.0:
        best_sample_label='_UNKNOWN'
    else:
        best_sample_label = labels.loc[np.argmax(overlap_duration), 'speaker']
    return best_sample_label

def labels_to_samples(labels, audio_dur, frame_dur_s, frame_shift_s, label_type = 'best'):
    # generate samples from speaker-labelled audio with corresponding speaker labels
    # unlabelled audio (could be speech, silence or background) to be labelled as 'Null'
    samples = []
    samp_start = np.arange(0,audio_dur-frame_dur_s,frame_shift_s)
    for s in samp_start:
        if label_type == 'best':
            sample_label = [get_best_spkr_label(labels, s, s+frame_dur_s)]
        if label_type == 'multi':
            sample_label = get_all_spkr_labels(labels, s, s+frame_dur_s)

        samples.append((s, s+frame_dur_s, sample_label))
    return samples

def any_label_match(labels_1, labels_2):
    # check if any labels in list/tuple labels_1 matches any labels in list/tuple labels_2
    # return True if so

    return any(set(labels_1).intersection(set(labels_2)))

def configure_spkrecTest(opts):
    # generates configuration files for speaker verification tests, given a label file for each session
    print('configuring speaker recognition test with provided options:')
    pprint.pprint(opts)
    test_cfg = [] # for storing list of test comparisons and timestamps
    enrollment_list_all=[]
    sample_list_all=[]

    for sesspath in opts['sessions']: 
        sesspath = sesspath.strip()
        sessname = os.path.basename(sesspath)
        print(f'______{sessname}______')
        wavfile = os.path.join(sesspath, f'{sessname}.wav')
        labelfile = os.path.join(sesspath, opts['labels_fname'].format(**locals()) )
        labels = pd.read_csv(labelfile)

        wavfile = os.path.join(sesspath, f'{sessname}.wav')
        audio = AudioSegment.from_file(wavfile)
        session_duration = audio.duration_seconds

        ## get list of samples
        sample_list = labels_to_samples(labels, session_duration,opts['frame_dur_s'], opts['frame_shift_s'], opts['label_type'])
        # add filename column 
        sample_list = [(wavfile,) + elms for elms in sample_list]
        ## get enrollment
        enrollment_list = []

        if opts['simulate_enrollment']:
            print('simulating enrollment from labelled utterances...')
            if not os.path.exists(os.path.join(sesspath, opts['targets_dir'])):
                os.makedirs(os.path.join(sesspath, opts['targets_dir']))
            # list speaker IDs
            speakers = list(set(labels['speaker']))
            enrDur = opts['enrollment_sec']# will concatenate first 10s of utterances from this target
            for t in speakers:
                labels_this_spkr = labels[labels['speaker'].str.match(t)]
                enrAudio = AudioSegment.empty() 
                starts_s  = labels_this_spkr['start_sec'].to_list()
                ends_s = labels_this_spkr['end_sec'].to_list()
                while enrAudio.duration_seconds <enrDur:
                    if starts_s:
                        enrAudio += audio[starts_s.pop(0)*1000: ends_s.pop(0)*1000]
                    else: # repeat if exhausted all utterances
                        enrAudio += enrAudio

                enrAudio = enrAudio[0:1000*enrDur]    
                enrFile = os.path.join(sesspath,opts['targets_dir'],f'enrollment_simulated_{t}.wav')        
                enrAudio.export(enrFile ,format='wav')
                enrollment_list.append((enrFile, 0.0, enrDur,[t]))

                # remove the audio used for enrollment from the sample list
                keep_ix = [not(elm[3]==t and get_overlap(elm[1], elm[2], 0.0, enrDur)>0.0) for elm in sample_list]
                sample_list = [sample_list[i] for i in range(0,len(keep_ix)) if keep_ix[i]]
 
        else: # read enrollment from targets_dir
            found_enrFiles = [f for f in os.listdir(os.path.join(sesspath,opts['targets_dir'])) if f.endswith('.wav')]
            print(f'found {len(found_enrFiles)} enrollment audio files...')

            for f in found_enrFiles:
                enrFile = os.path.join(sesspath,opts['targets_dir'], f)
                enrAudio = AudioSegment.from_file(enrFile)
                enrDur = enrAudio.duration_seconds
                # strip keyword parts of filename in crude attempt to get target name TODO update when we have real enrollment
                speaker = re.sub('.wav','',f)
                speaker = re.sub('enrollment_simulated_','',speaker)
                speaker = re.sub('enrollment_','',speaker)

                enrollment_list.append((enrFile, 0.0, enrDur,[speaker]))

        if opts['target_combinations']: # generate pairings of targets and sum enrollment audio
            if not os.path.exists(os.path.join(sesspath, opts['targets_dir'], 'combinations')):
                os.makedirs(os.path.join(sesspath, opts['targets_dir'], 'combinations'))
            found_enrFiles = [f for f in os.listdir(os.path.join(sesspath,opts['targets_dir'])) if f.endswith('.wav')]
            print('generating combination enrollment audio...')
            for f1, f2 in  [(f1, f2) for f1 in enrollment_list for f2 in enrollment_list if f1 != f2]:
                enrAudio1 = AudioSegment.from_file( f1[0])
                enrAudio2 = AudioSegment.from_file( f2[0])
                enrDur = min(enrAudio1.duration_seconds, enrAudio2.duration_seconds)
                enrAudioCombined = effects.normalize(effects.normalize(enrAudio1[0:enrDur*1000]).overlay(effects.normalize(enrAudio2[0:enrDur*1000])))
                speaker = f1[3] + f2[3] # speaker is a list

                enrFile = os.path.join(sesspath,opts['targets_dir'],'combinations', f'{"_+_".join(speaker)}.wav')        
                enrAudioCombined.export(enrFile ,format='wav')

                enrollment_list.append((enrFile, 0.0, enrDur,speaker))

        # append to all-session list        
        enrollment_list_all+=enrollment_list
        sample_list_all+=sample_list
        
        ## pair up within-session 
        if not opts['cross_session']:

            if opts['sampleVsample']:
                # pair all samples/enrolments with one another (gives more tests)
                for s1 in (enrollment_list+sample_list):
                    for s2 in (enrollment_list+sample_list):
                        if not ((s1[3]=='_UNKNOWN') & (s2[3]=='_UNKNOWN')):
                            if not (s1==s2): # don't pair identical samples 
                                if not (s1[0] == s2[0]) & (get_overlap(s1[1], s1[2], s2[1], s2[2]) > 0.0): # don't pair overlapping samples
                                    test_cfg.append(s1+s2)
                # prune test list
                if not (opts['density'] ==1.0):
                    test_cfg = random.sample(test_cfg, int(len(test_cfg)*opts['density']))

            if not opts['sampleVsample']:
                # prune sample list - select subset of samples to test each enrollment against
                if not (opts['density'] ==1.0):
                    sample_list = random.sample(sample_list, int(len(sample_list)*opts['density']))

                # just pair all enrollments with samples (as in TAD)
                for e in enrollment_list:
                    for s in sample_list: 
                        test_cfg.append(e+s)



    # pair up cross-sessions TODO
    # TODO deal w duplicate speakerID across sessions that aren't actually the same person e.g. TargetedTeacher1

    test_cfg_df = pd.DataFrame(test_cfg, columns=['x1path','x1start_s','x1end_s','x1speaker','x2path','x2start_s','x2end_s','x2speaker'])

    # which pairings match? 
    # if opts['label_type'] == 'multi' :
    #     test_cfg_df['match'] = [any_label_match(*args) for args in tuple(zip(test_cfg_df['x1speaker'], test_cfg_df['x2speaker'])) ]

    # elif opts['label_type'] == 'best':
    #     test_cfg_df['match'] = test_cfg_df['x1speaker']==test_cfg_df['x2speaker']
    test_cfg_df['match'] = [any_label_match(*args) for args in tuple(zip(test_cfg_df['x1speaker'], test_cfg_df['x2speaker'])) ]

    print(f'Generated speaker verification test config for {opts["verstr"]}')
    print(f'...containing {len(test_cfg)} comparisons')
    print(f'...of which {len(test_cfg_df[test_cfg_df["match"]])} are matched speakers')

    return test_cfg_df

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
    # print(f'#{row.name}: {row["x1speaker"]} vs {row["x2speaker"]}. Verification score: {score.item()}')
    row['score'] = score.item()
    return row

def run_spkrecTest(testpairs_df,model_type='xvect', precompute_targets = True):
    global speechbrain_dir
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
        target_files = list(set(testpairs_df['x1path']))
        target_embeddings = {}
        print('Precomputing target embeddings...')
        for t in target_files:
            signal, fs = torchaudio.load(t)
            if not fs == 16000:
                # fs must be 16000 
                to16k = torchaudio.transforms.Resample(fs, 16000)
                signal = to16k(signal)
            target_embeddings[t] = encoder.encode_batch(signal)
    
    print(f'Computing verification scores for {len(testpairs_df)} pairs...')

    # iterate over test pairings
    result = testpairs_df.apply(df_spkrVerification,
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

    return result, result_EER ,result_threshold

def eval_spkrec(result, thresh_type='EER', preset_thresh = None): 

    # For complete experiments (all samples tested against all targets, density=1.0):
    # Summarise to give frame-level TAD decisions (target/nontarget) using 
    # (i) EER threshold and (ii) set threshold (default or from retraining)
    # and compare to ground truth (target/nontarget)
    # plot scores over time for all targets plus ground truth target
    # Evaluate TAD performance:
    # - mean duration of predicted and actual target segments 
    # - Proportion of true positive, false positive, true negative, false negative by DURATION
    # - and breakdown of the above by true target

    # get EER threshold over all results
    positive_scores = tensor(result.loc[result.match,'score'].to_list())
    negative_scores = tensor(result.loc[~result.match,'score'].to_list())
    result_EER, result_threshold = EER(positive_scores, negative_scores)
    if thresh_type == 'EER':   
        result['prediction'] = result['score']>result_threshold
    if thresh_type == 'preset':
        result['prediction'] = result['score']>preset_thresh

    # get TP, TN, FP, FN counts for pair-level decisions
    CM = confusion_matrix(result['match'], result['prediction'])
    TN = CM[0][0]
    FN = CM[1][0]
    TP = CM[1][1]
    FP = CM[0][1]
    print(f'TP: {TP}, FP: {FP}, TN: {TN}, FN: {FN}')

    accuracy = accuracy_score(result['match'], result['prediction'])
    print(f'accuracy: {accuracy}')
    precision = precision_score(result['match'], result['prediction'])
    print(f'precision: {precision}')
    recall = recall_score(result['match'], result['prediction'])
    print(f'recall: {recall}')

    metrics={'TP':TP, 'TN':TN, 'FP':FP, 'FN':FN, 'accuracy':accuracy, 'precision':precision, 'recall':recall}
    # # speaker ID is a list, but lists are unhashable - convert to a string
    # #result['x1speaker'] = result['x1speaker'].apply(', '.join)
    # target_names = list(set(result['x1speaker']))

    # #result['x2speaker'] = result['x2speaker'].apply(', '.join)


    # # pivot wider by sample time, separate column for each x1 speaker (target) 
    # result_wide = result.pivot(index=['x2path','x2start_s','x2end_s','x2speaker'],columns = 'x1speaker', values='prediction').reset_index()

    # result_wide['TAD_decision'] = result_wide[target_names].any(axis=1 )
    # result_wide['isTarget_true'] = result_wide['x2speaker'].isin(target_names)

    # # form segments from passed chunks (where TAD_decision = True)
    # pooled_accuracy = accuracy_score(result_wide['TAD_decision'], result_wide['isTarget_true'])
    # print(f'pooled accuracy: {pooled_accuracy}')
    # # TODO decide on dealing with overlaps, smoothing, etc. 

    # evaluate based on total time overlap between ground-truth target timings and passed segment timings
    return metrics

if __name__ == "__main__":

    with open(os.path.join('configs', 'deepSample2.txt')) as ctl: # reads lines without empties
        sesslist = (line.rstrip() for line in ctl) 
        sesslist = list(line for line in sesslist if line)

    print('Generating an example cfgSpkRecTest...')
    
    precompute_targets=True # set to false for tests of sample-sample pairings
    model_type = 'ecapa' # 'ecapa' or 'xvect'
    speechbrain_dir = "/Users/roso8920/Dropbox (Emotive Computing)/iSAT/speechbrain/"

    # options
    opts = {}
    opts['frame_dur_s'] = 1.5
    opts['frame_shift_s'] = 0.5
    opts['sessions'] = sesslist # list of session directories 
    opts['simulate_enrollment'] = True # simulate enrollment by concatenating utterances to use as target
    opts['enrollment_sec'] = 10
    opts['target_combinations'] = False # make additional enrollment samples by combining existing samples
    opts['targets_dir'] = 'targets' # subdir of session directory containing enrollment audio (will create if simulating)
    opts['labels_fname'] = 'utt_labels_{sessname}.csv' # relative to session directory
    opts['cross_session'] = False # TODO If True, pairings between sessions; if False, pairings within session only
    opts['sampleVsample'] = False # if True, pairings between all samples; if False, pairings between enrollment and samples only
    opts['density'] = 0.01 # float. Proportion of samples to use. If <1.0 will randomly sample from density*n pairings
    opts['verstr'] = 'deepSample2_example' # will save the configuration with this filename
    opts['label_type'] = 'multi' # 'multi','best'. multi = list of speaker IDs. 'best' chooses majority speaker

    test_cfg_df = configure_spkrecTest(opts)
    # save test list
    test_cfg_df.to_csv(os.path.join('configs','speaker_verification','tests', f'{opts["verstr"]}_testpairs.csv'),index=False)
    # save configuration options
    with open(os.path.join('configs','speaker_verification','tests', f'{opts["verstr"]}_opts.json'), "w") as dumpfile:
        json.dump(opts, dumpfile)

    test_cfg_file = os.path.join('configs','speaker_verification','tests', f'{opts["verstr"]}_testpairs.csv')
    testpairs_df = pd.read_csv(test_cfg_file, index_col=False)

    result, result_EER, result_threshold = run_spkrecTest(testpairs_df, model_type, precompute_targets)

    print(f'TEST COMPLETE. EER = {result_EER:.3f}, threshold = {result_threshold:.3f}')

    result.to_csv(os.path.join('results','speaker_verification','tests', f'{opts["verstr"]}_{model_type}_result.csv'))

    # write summary to txt file
    resfile = os.path.join('results','speaker_verification','tests', f'{opts["verstr"]}_{model_type}_result.txt')

    with open(resfile,'w') as outfile:
        outfile.write(f'n_pairs = {len(result)}\n')
        outfile.write(f'n_matches = {len(result[result["match"]])}\n')
        outfile.write(f'n_target_present = {len(result[~result["x2speaker"].str.match("_UNKNOWN")])}\n')
        outfile.write(f'n_unique_targetIDs = {len(set(result["x1speaker"]))}\n')
        outfile.write(f'n_unique_testIDs = {len(set(result["x2speaker"]))}\n')
        outfile.write(f'EER = {result_EER:.3f}\n')
        outfile.write(f'EER_threshold = {result_threshold:.3f}\n')



