from rosy_asr_utils import * 
from pathlib import Path
from pydub import AudioSegment
import os 
import glob
import subprocess
import csv
import pandas as pd
import numpy as np
from pathlib import Path


video_path_in = './data/fall2021_unsorted/crystalVideoQ2/'
extract_timings_csv = './configs/deepSample2b_to_extract.csv'
outdir= './data/fall2021_unsorted/crystalVideoQ2/deepSample2_video/'

def HHMMSS_to_sec(time_str):
    """Get Seconds from time with milliseconds."""
    if time_str.count(':')==2:
        h, m, s = time_str.split(':')
    else:
        print(f'input string format not supported: {time_str}')
    return int(h) * 3600 + int(m) * 60 + float(s) 

if not os.path.exists(outdir):
    os.makedirs(outdir)

with open(extract_timings_csv, 'r', newline='') as in_file:
    reader = csv.reader(in_file)
    # skip header
    next(reader)

    for rec in reader:
        sessname,sg_startHMS,sg_endHMS, use = rec

        sg_start_ms = HHMMSS_to_sec(sg_startHMS) *1000
        sg_end_ms = HHMMSS_to_sec(sg_endHMS) *1000

        videos = glob.glob(f'{video_path_in}/{sessname}.*')
        print(videos)
        if not videos:
            print(f'{sessname}: no video found')
        else:
            for sess_video_file in videos:
                ext = Path(sess_video_file).suffix

                # .MOV is causing compatability issues for annotators on Windows - convert to mp4
                #ext = '.mp4'
                outfile = os.path.join(outdir,f'{sessname}_5min{ext}')

                if os.path.exists(sess_video_file):
            
                    subprocess.call(['ffmpeg',
                    '-y',
                    '-i',
                    sess_video_file,
                    '-ss',
                    sg_startHMS,
                    '-to',
                    sg_endHMS,
                    '-c',
                    'copy',
                    outfile        
                    ],shell=False)









