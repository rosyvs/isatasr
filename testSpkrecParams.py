import os 
import spkrecTest
spkrecTest.speechbrain_dir =  "/Users/roso8920/Dropbox (Emotive Computing)/iSAT/speechbrain/"

from sklearn.model_selection import KFold
import json
import pandas as pd


# Test different speaker verification parameters: 
# - ecapa vs xvector
# - sample window length
# - enrollment duration
# - combinatorial enrollments

exp_name = 'deepSample2_EvT_10s_realEnrollment'

### List of param vals to tune over
tune_frame_dur = [.25, .5, .75, 1, 1.5, 2, 2.5, 3, 3.5, 4]
###

### Test configuration options stable over all values of parameter
opts = {}
opts['frame_shift_s'] = 0.5
opts['simulate_enrollment'] = False # simulate enrollment by concatenating utterances to use as target
opts['enrollment_sec'] = 10
opts['target_combinations'] = False # make additional enrollment samples by combining existing samples
opts['targets_dir'] = 'enrollment' # subdir of session directory containing enrollment audio (will create if simulating)
opts['labels_fname'] = 'utt_labels_{sessname}.csv' # relative to session directory
opts['cross_session'] = False # TODO If True, pairings between sessions; if False, pairings within session only
opts['sampleVsample'] = False # if True, pairings between all samples; if False, pairings between enrollment and samples only
opts['density'] = 0.1 # float. Proportion of samples to use. If <1.0 will randomly sample from density*n pairings
opts['label_type'] = 'best' # 'multi','best'. multi = list of speaker IDs. 'best' chooses majority speaker
###

model_type = 'ecapa'
precompute_targets = ~opts['sampleVsample'] # only precompute if using target enrollment


# Use "training" split to set EER threshold
# evaluate performance on test split

k = 5 # number of folds 
sessions = os.path.join('configs', 'deepSample2.txt') # txt file list of session paths
cfg_dir = os.path.join('configs','speaker_verification', exp_name)
results_dir = os.path.join('results','speaker_verification', exp_name)
os.makedirs(cfg_dir, exist_ok = True)
os.makedirs(results_dir, exist_ok = True)

with open(sessions) as ctl: # reads lines without empties
    sesslist = (line.rstrip() for line in ctl) 
    sesslist = list(line for line in sesslist if line)

kfolder = KFold(n_splits = k, shuffle = True, random_state = 303)

all_metrics = []
for split, (train_index, test_index)  in enumerate(kfolder.split(sesslist)):
    train_sess = [sesslist[i] for i in train_index]
    test_sess = [sesslist[i] for i in test_index]


    for frame_dur in tune_frame_dur:
        opts['frame_dur_s'] = frame_dur
        print(f'frame length: {frame_dur}, fold: {split}')

        ## Get EER for "train" split
        opts['verstr'] = f'{exp_name}_{frame_dur}_{split}' # will save the configuration with this filename
        opts['sessions'] = train_sess # list of session directories 
        train_pairs_df = spkrecTest.configure_spkrecTest(opts)

        train_pairs_df.to_csv(os.path.join(cfg_dir,\
            opts["verstr"].format(**locals()) + '_train_pairs.csv'),index=False)
        # save configuration options
        with open(os.path.join(cfg_dir,\
            opts["verstr"].format(**locals()) + '_train_opts.json'), "w") as dumpfile:
            json.dump(opts, dumpfile)

        train_result, train_EER, train_threshold = spkrecTest.run_spkrecTest(train_pairs_df, model_type, precompute_targets)
        train_result.to_csv(os.path.join(results_dir, f'{opts["verstr"]}_{model_type}_train_result.csv'))


        ## Evaluate for "test" split
        opts['sessions'] = test_sess # list of session directories 
        test_pairs_df = spkrecTest.configure_spkrecTest(opts)

        test_pairs_df.to_csv(os.path.join(cfg_dir,\
            opts["verstr"].format(**locals()) + '_test_pairs.csv'),index=False)
        # save configuration options
        with open(os.path.join(cfg_dir,\
            opts["verstr"].format(**locals()) + '_test_opts.json'), "w") as dumpfile:
            json.dump(opts, dumpfile)

        test_result, test_EER, test_threshold = spkrecTest.run_spkrecTest(test_pairs_df, model_type, precompute_targets)
        test_result.to_csv(os.path.join(results_dir, f'{opts["verstr"]}_{model_type}_test_result.csv'))

        # Apply train threshold to test partition scores
        metrics = spkrecTest.eval_spkrec(test_result, thresh_type='preset', preset_thresh=train_threshold)
        
        metrics_df = pd.DataFrame(metrics,index=[0])
        metrics_df['frame_dur_s'] = frame_dur
        metrics_df['split'] = split
        metrics_df['train_EER'] = train_EER
        metrics_df['train_thresh'] = train_threshold
        metrics_df['test_EER'] = test_EER
        metrics_df['test_thresh'] = test_threshold
        metrics_df['train_N'] = len(train_pairs_df)
        metrics_df['test_N'] = len(test_pairs_df)
        metrics_df['train_Ntargets'] = len(set([t for s in train_result["x1speaker"] for t in s ]))
        metrics_df['test_Ntargets'] = len(set([t for s in test_result["x1speaker"] for t in s ]))

        # write metrics to txt for monitoring progress
        with open(os.path.join(results_dir,\
            opts["verstr"].format(**locals()) + f'_{model_type}_summary.txt'), "w") as dumpfile:
            for col, val in metrics_df.iteritems(): 
                stri = f'{col}: {val.values.item()}'
                dumpfile.write(stri + '\n')


        all_metrics.append(metrics_df)
all_metrics = pd.concat(all_metrics)
all_metrics.to_csv(os.path.join(results_dir, f'{exp_name}_{model_type}_results.csv'))

grouped = all_metrics.groupby('frame_dur_s',as_index=True).mean().reset_index()
grouped.to_csv(os.path.join(results_dir, f'{exp_name}_{model_type}_results_by_group.csv'))