import torchaudio
from torch import tensor, cat, squeeze
import os
import pandas as pd
import numpy as np
from speechbrain.utils.metric_stats import EER
from sklearn.metrics import accuracy_score, confusion_matrix, recall_score, precision_score





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
    accuracy = accuracy_score(result['match'], result['prediction'])
    print(f'accuracy: {accuracy}')

    # pivot wider by sample time 
    result_wide = result.pivot(index=['x2path','x2start_s','x2end_s','x2speaker'],columns = 'x1speaker', values='prediction').reset_index()

    target_names = list(set(result['x1speaker']))
    result_wide['TAD_decision'] = result_wide[target_names].any(axis=1 )
    result_wide['isTarget_true'] = result_wide['x2speaker'].isin(target_names)

    # form segments from passed chunks (where TAD_decision = True)

    # TODO decide on dealing with overlaps, smoothing, etc. 

    # evaluate based on total time overlap between ground-truth target timings and passed segment timings

model_type = 'xvect' # 'ecapa' or 'xvect'
thresh_type = 'EER' # {'preset','EER'}
preset_thresh = None 
result = pd.read_csv(os.path.join(
    'results','speaker_verification','tests', 
    f'{verstr}_{model_type}_result.csv'),index_col=False)
