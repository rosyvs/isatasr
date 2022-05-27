from rosy_asr_utils import get_sess_audio
from pydub import AudioSegment
from pathlib import Path
import os
import csv
import subprocess
import argparse
import pandas as pd




def HHMMSS_to_sec(time_str):
    """Get Seconds from time with milliseconds."""
    if time_str.count(':')==2:
        h, m, s = time_str.split(':')
    else:
        print(f'!!!input string format not supported: {time_str}')
    return int(h) * 3600 + int(m) * 60 + float(s) 

def extractSamples(datadir,
                    extract_timings_csv, 
                    outdir_stem, 
                    suffix='_excerpt', 
                    convert=False):
    # options for writing out audio if converting
    WAV_CHANNELS = 1
    WAV_SAMPLE_RATE = 48000
    # with open(extract_timings_csv, 'r', newline='') as in_file:
    #     reader = csv.reader(in_file)
    #     # skip header
    #     next(reader)
    samples_df = pd.read_csv(extract_timings_csv,skip_blank_lines=True, names=['sessname','startHMS','endHMS'], header=0).dropna().sort_values(by='sessname').reset_index()
    # enumerate samples by session and check if there are multiple samples from a given session
    samples_df['count'] = samples_df.groupby('sessname').cumcount()

    for i, rec in samples_df.iterrows():
        _,sessname,startHMS,endHMS, count = rec.values
        suffix_use = f'{suffix}{count}' if count > 0 else suffix # if multiple samples per recording, give a diffrent name          
        # times in msec rel to start of recording
        sg_start_ms = HHMMSS_to_sec(startHMS) *1000
        sg_end_ms = HHMMSS_to_sec(endHMS) *1000

        sesspath = os.path.join(datadir, sessname)
        print('\n')
        print(sesspath)
        if not os.path.exists(sesspath):
            print(f'!!!WARNING: session directory not found: {sesspath}')
            continue
        outdir = os.path.join(outdir_stem, f'{sessname}{suffix_use}')
        if not os.path.exists(outdir):
            os.makedirs(outdir)

        media_file = get_sess_audio(sesspath)
        if not media_file:
            print(f'!!!WARNING: no media found for {sessname}')
            continue
        media_type = Path(media_file).suffix
        print(f'...Input media: {media_file}')

        # detect if audio or video
        if media_type in ['.MOV', '.mov', '.mp4']: # media is VIDEO
            if convert:
                ext = '.mp4'
                print(f'...converting to {ext}')
            else:
                ext = media_type
            # .MOV causes ELAN compatability issues for annotators on Windows - convert to mp4
            outfile = os.path.join(outdir,f'{sessname}{suffix_use}{ext}')
            print('...Using ffmpeg to trim video...')            
            subprocess.call(['ffmpeg',
            '-y',
            '-i',
            media_file,
            '-ss',
            startHMS,
            '-to',
            endHMS,
            '-c',
            'copy',
            outfile,
            '-hide_banner', 
            '-loglevel', 
            'error'        
            ],shell=False)

        else: # media is AUDIO
            sess_audio = AudioSegment.from_file(media_file)
            # print(f'...Full recording duration: {sess_audio.duration_seconds} seconds')
            excerpt = sess_audio[sg_start_ms:sg_end_ms]
            if convert:
                ext = '.wav'
                outfile = os.path.join(outdir,f'{sessname}{suffix_use}{ext}')
                excerpt = excerpt.set_channels(WAV_CHANNELS)
                excerpt = excerpt.set_frame_rate(WAV_SAMPLE_RATE)
                print(f'...converting to {ext}')
                excerpt.export(outfile, format='wav')

            else: # keep original media type
                ext = media_type
                outfile = os.path.join(outdir,f'{sessname}{suffix_use}{ext}')
                excerpt.export(outfile)                    

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Extract samples from media')
    parser.add_argument('datadir', nargs='?', default='./data/deepSampleTEST/', help='root path of session directories')
    parser.add_argument('extract_timings_csv', nargs='?', default='./configs/deepSampleTEST_to_extract.csv', help='csv with columns for sessname, start (sec), end (sec)')
    parser.add_argument('outdir_stem', nargs='?',default= './data/deepSampleTEST/',help='root path of directory to put sample session directories')
    parser.add_argument('suffix', nargs='?', default='_5min', help='suffix for naming sample session')
    parser.add_argument('-c','--convert', action='store_true', help='convert media to preferred formats (wav, mp4) - default False')
    args = parser.parse_args()

    extractSamples(datadir=args.datadir,
    extract_timings_csv=args.extract_timings_csv, 
    outdir_stem=args.outdir_stem, 
    suffix=args.suffix, 
    convert=args.convert)

    # # For debug in interactive: 
    # datadir='./data/deepSampleTEST/'
    # extract_timings_csv='./configs/deepSampleTEST_to_extract.csv'
    # outdir_stem='./data/deepSampleTEST/'
    # suffix='_5min'
    # convert=True