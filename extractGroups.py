from rosy_asr_utils import get_sess_audio
from pydub import AudioSegment
from pathlib import Path
import os
import csv
import subprocess

# options for writing out audio if converting
WAV_CHANNELS = 1
WAV_SAMPLE_WIDTH = 2
WAV_SAMPLE_RATE = 48000
WAV_BIT_DEPTH = 16

# # OPTIONS TO INTEGRATE INTO CLI
# datadir = './data/sess/' # TODO: specify using config.txt
# outdir_stem = './data/wideSample1/'
# extract_timings_csv = './configs/Linux/wideSample1.csv' # this just needs sessname, start, end columns
# OPTIONS TO INTEGRATE INTO CLI
datadir = './data/deepSampleTEST/' # TODO: specify using config.txt
outdir_stem = './data/deepSampleTEST/'
extract_timings_csv = './configs/deepSample2_to_extract.csv' # this just needs sessname, start, end columns

suffix = '5min'
convert = False # converts to preferred file types: WAV for audio, mp4 for video. If false, use input media format

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
        sessname,sg_startHMS,sg_endHMS = rec

        # times in msec rel to start of recording
        sg_start_ms = HHMMSS_to_sec(sg_startHMS) *1000
        sg_end_ms = HHMMSS_to_sec(sg_endHMS) *1000

        sesspath = os.path.join(datadir, sessname)
        if not os.path.exists(sesspath):
            print(f'!!!WARNING: session directory not found: {sesspath}')
            continue
        outdir = os.path.join(outdir_stem, f'{sessname}_{suffix}')
        if not os.path.exists(outdir):
            os.makedirs(outdir)

        media_file = get_sess_audio(sesspath)
        if not media_file:
            print(f'!!!WARNING: no media found for {sessname}')
            continue
        media_type = Path(media_file).suffix
        print(f'Input media: {media_file}')

        # detect if audio or video
        if media_type in ['.MOV', '.mov', '.mp4']: # media is VIDEO
            print('media is VIDEO')
            if convert:
                ext = '.mp4'
            else:
                ext = media_type
            # .MOV causes ELAN compatability issues for annotators on Windows - convert to mp4
            outfile = os.path.join(outdir,f'{sessname}_{suffix}{ext}')            
            subprocess.call(['ffmpeg',
            '-y',
            '-i',
            media_file,
            '-ss',
            sg_startHMS,
            '-to',
            sg_endHMS,
            '-c',
            'copy',
            outfile        
            ],shell=False)

        else: # media is AUDIO
            sess_audio = AudioSegment.from_file(media_file)
            print(f'Full recording duration: {sess_audio.duration_seconds} seconds')
            excerpt = sess_audio[sg_start_ms:sg_end_ms]
            if convert:
                ext = '.wav'
                outfile = os.path.join(outdir,f'{sessname}_{suffix}{ext}')
                excerpt = excerpt.set_channels(WAV_CHANNELS)
                excerpt = excerpt.set_frame_rate(WAV_SAMPLE_RATE)
                excerpt.export(outfile, format='wav')
            else: # keep original media type
                ext = media_type
                outfile = os.path.join(outdir,f'{sessname}_{suffix}{ext}')
                excerpt.export(outfile)                    