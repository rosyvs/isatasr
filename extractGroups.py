# extractGroups.py  <wav file, csv file>
# extract audio of interest from full session listed in csv file
# name,url,nsegs,date,rec start hr:min, grp start hr:min, grp end hr:min

import pydub
from pydub import AudioSegment
import sys
import os
import re
import argparse
import csv

# options
channels = 1
sample_width = 2
sample_rate = 48000
bit_depth = 16

datadir = './data/deepSampleFull/' # full length audio is expected to be in session dirs already
outdir_stem = './data/deepSample2/'
extract_timings_csv = './configs/deepSample2_to_extract.csv'

def HHMMSS_to_sec(time_str):
    """Get Seconds from time with milliseconds."""
    if time_str.count(':')==2:
        h, m, s = time_str.split(':')
    else:
        print(f'input string format not supported: {time_str}')
    return int(h) * 3600 + int(m) * 60 + float(s) 

with open(extract_timings_csv, 'r', newline='') as in_file:
    reader = csv.reader(in_file)
    # skip header
    next(reader)

    for rec in reader:
        print(rec)
        sessname,sg_startHMS,sg_endHMS, use = rec


    

        # times in msec rel to start of recording
        sg_start_ms = HHMMSS_to_sec(sg_startHMS) *1000
        sg_end_ms = HHMMSS_to_sec(sg_endHMS) *1000


        sessdir = os.path.join(datadir, sessname)
        outdir = os.path.join(outdir_stem, f'{sessname}_5min')
        if not os.path.exists(outdir):
            os.makedirs(outdir)
        outfile = os.path.join(outdir,f'{sessname}_5min.wav')
        sess_audio = AudioSegment.from_wav(os.path.join(sessdir, f'{sessname}.wav'))
        excerpt = sess_audio[sg_start_ms:sg_end_ms]

        excerpt = excerpt.set_channels(channels)
        excerpt = excerpt.set_frame_rate(sample_rate)
        excerpt.export(outfile, format='wav')
