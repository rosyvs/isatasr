import os
import pandas as pd
from rosy_asr_utils import eval_segmentation, get_sess_audio, exportSegAudio

filelist = './configs/deepSample2.txt'
ref_blk = '{sessname}.blk'
hyp_blk = 'TAD_{sessname}.blk'
results_dir = os.path.join('results','TAD', 'deepSample2')
os.makedirs(results_dir, exist_ok = True)

with open(filelist) as ctl: # reads lines without empties
    sesslist = (line.rstrip() for line in ctl) 
    sesslist = list(line for line in sesslist if line)

all_results=[]
for sesspath in sesslist:
    sesspath = sesspath.strip()
    sessname = os.path.basename(sesspath)
    audiofile = get_sess_audio(sesspath)
    result=eval_segmentation(os.path.join(sesspath,ref_blk.format(**locals())), 
    os.path.join(sesspath,hyp_blk.format(**locals())), 
    audiofile)
    # store in df: add row
    all_results.append(result)

    # export segment audio
    exportSegAudio(os.path.join(sesspath,hyp_blk.format(**locals())), audio_file=audiofile, segDir='TAD_segments')

    # write out some FP and FN segments audio


# write dataframe of results
all_results = pd.DataFrame(all_results)
all_results.to_csv(os.path.join(results_dir, 'sesswise.csv'),float_format='%.3f')
agg_results = all_results.mean()
agg_results.to_csv(os.path.join(results_dir, 'mean.csv'),float_format='%.3f')

