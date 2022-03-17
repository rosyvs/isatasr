import os
import pandas as pd
from VAD_TAD_block import segFromVAD
from spkrecTest import get_overlap
from tqdm import tqdm
# Run VAD with different settings and use gold standard speaker labelling to evaluate 

aggs = [0, 1, 2, 3]
framelengths = [10, 20, 30]
win_lengths = [100, 200, 300, 500]
min_seg_durs = [1000, 2000, 3000, 5000]
nparams = len(aggs)*len(framelengths)*len(win_lengths)*len(min_seg_durs)
filelist = 'configs/deepSample2.txt'
results_dir = os.path.join('results','VAD', 'deepSample2')
os.makedirs(results_dir, exist_ok = True)

with open(filelist) as ctl: # reads lines without empties
    sesslist = (line.rstrip() for line in ctl) 
    sesslist = list(line for line in sesslist if line)
print(f'Testing VAD parameters: {nparams} combinations * {len(sesslist)} sessions')

all_results=[]
for agg in tqdm(aggs):
    for frame_length in framelengths:
        for win_length in win_lengths:
            for min_seg_dur in min_seg_durs:

                file_suffix = f'_VAD_a{agg}-f{frame_length}-w{win_length}-m{min_seg_dur}'
                print(file_suffix)
                segFromVAD(filelist=filelist, 
                export_seg_audio=False,
                agg=agg,
                frame_length=frame_length,
                win_length=win_length,
                min_seg_dur = min_seg_dur,
                file_suffix=file_suffix)

                # evaluate
                for sesspath in sesslist:
                    sesspath = sesspath.strip()
                    sessname = os.path.basename(sesspath)
                    overlap=0.0
                    # read in VAD .blk
                    VADblkmapFile = os.path.join(sesspath,f'{sessname}{file_suffix}.blk')
                    VADblks = pd.read_table(VADblkmapFile, sep=' ', names =['b','s','start_sec','end_sec'])

                    # read in ground truth labels
                    GOLDblkmapFile = os.path.join(sesspath,f'{sessname}.blk')
                    GOLDblks = pd.read_table(GOLDblkmapFile, sep=' ', names =['b','s','start_sec','end_sec'])

                    # compute overlap
                    for index1, row1 in VADblks.iterrows():
                        overlaps = GOLDblks.apply(lambda row: get_overlap(row['start_sec'],row['end_sec'],row1['start_sec'],row1['end_sec'] ), axis=1)
                        overlap += sum(overlaps)
                    GOLDdurs = GOLDblks['end_sec'] - GOLDblks['start_sec']
                    VADdurs = VADblks['end_sec'] - VADblks['start_sec']

                    mean_gold_dur = GOLDdurs.mean()
                    mean_VAD_dur =VADdurs.mean()
                    recall_prop = overlap / GOLDdurs.sum()
                    precision_prop = overlap / VADdurs.sum()
                    # store in df: add row
                    result = (agg, frame_length, win_length, min_seg_dur, sessname, overlap, recall_prop, precision_prop, mean_VAD_dur, mean_gold_dur)
                    all_results.append(result)

# write dataframe of results
all_results = pd.DataFrame(all_results, columns=['agg', 'frame_length', 'win_length', 'min_seg_dur', 'sessname', 'overlap','recall_prop', 'precision_prop', 'mean_VAD_dur', 'mean_gold_dur'])
all_results['F1'] = all_results['precision_prop'] * all_results['recall_prop']*2 / (all_results['precision_prop']+ all_results['recall_prop'])
all_results.to_csv(os.path.join(results_dir, 'sesswise.csv'))


# 
agg_results = all_results.groupby(['agg', 'frame_length', 'win_length', 'min_seg_dur']).mean()
agg_results.to_csv(os.path.join(results_dir, 'averaged_over_sess.csv'))
params_maxP = dict(zip(['agg', 'frame_length', 'win_length', 'min_seg_dur'],agg_results['precision_prop'].idxmax()))
params_maxR = dict(zip(['agg', 'frame_length', 'win_length', 'min_seg_dur'],agg_results['recall_prop'].idxmax()))
params_maxF1 = dict(zip(['agg', 'frame_length', 'win_length', 'min_seg_dur'],agg_results['F1'].idxmax()))
print(f'best by precision: {params_maxP} \nbest by recall: {params_maxR} \nbest by F1:{params_maxF1}')