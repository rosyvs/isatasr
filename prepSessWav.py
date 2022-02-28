from rosy_asr_utils import * 
from pathlib import Path
from pydub import AudioSegment
import argparse
import os 

parser = argparse.ArgumentParser(description='Convert media to WAV and place in session directory for ASR')
parser.add_argument('filelist', help='path to text file containing list of file paths to convert')
parser.add_argument('outdir', default='./data/',help='directory to make session directories')
args = parser.parse_args()

# convert session audio to WAV and place in session directories

# options
channels = 1
sample_width = 2
sample_rate = 48000
bit_depth = 16
sess_base_dir = args.outdir # where to export session subdirectories

# args_ctl has list of paths to sessions to process
with open(args.filelist) as ctl:
    sesslist = (line.rstrip() for line in ctl) 
    sesslist = list(os.path.normpath(line) for line in sesslist if line)

for sess in sesslist: 
    print(f'sess: {sess}')
    sess = sess.strip()

    sessname=sessname.stem # remove extra extensions e.g. .mp4.mp4 that are present in some source media files
    sessname = sessname.split('.')[0]

    sesspath = f'{sess_base_dir}/{sessname}/'

    print(f'...Extracted session name from media file: {sessname}')
    aud_type = Path(sess).suffix
    print(aud_type)
    if not os.path.exists(sesspath):
        os.makedirs(sesspath)

    aud = AudioSegment.from_file(sess)
    wav_path = os.path.join(sesspath,f'{sessname}.wav')

    new_audio = aud.set_channels(channels)
    new_audio = new_audio.set_frame_rate(sample_rate)
    new_audio.export(wav_path, format='wav')
    print(f'...Made session directory and converted media to .WAV.')

