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
sample_rate = 16000
bit_depth = 16

datadir = './data/sess/'
outdir_stem = 'sg_excerpts'
csvfile = './configs/sg_to_extract.csv'

with open(csvfile, 'r', newline='') as in_file:
    reader = csv.reader(in_file)
    # skip header
    next(reader)

    for rec in reader:
        print(rec)
        teacher,period,lesson,activity, sessname,excerpt_no, url,date,rec_startHM,sg_startHM,sg_endHM, names_HM,filetype, view, mic_model, mic_no, students, notes = rec
        h,m = rec_startHM.split(':')
        rec_start_min = (int(h) * 60) + int(m)
        h,m = sg_startHM.split(':')
        sg_start_min = (int(h) * 60) + int(m)
        h,m = sg_endHM.split(':')
        sg_end_min = (int(h) * 60) + int(m)

        # times in msec rel to start of recording
        sg_start_ms = (sg_start_min - rec_start_min) * 60000
        sg_end_ms = (sg_end_min - rec_start_min) * 60000


        sessdir = os.path.join(datadir, sessname)
        outdir = os.path.join(outdir_stem, sessdir)
        if not os.path.exists(outdir):
            os.makedirs(outdir)
        outfile = os.path.join(outdir,f'{sessname}_ex{excerpt_no}.wav')
        sess_audio = AudioSegment.from_wav(os.path.join(sessdir, f'{sessname}.wav'))
        excerpt = sess_audio[sg_start_ms:sg_end_ms]

        excerpt = excerpt.set_channels(channels)
        excerpt = excerpt.set_frame_rate(sample_rate)
        excerpt.export(outfile, format='wav')
