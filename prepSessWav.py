from rosy_asr_utils import * 
from pathlib import Path
from pydub import AudioSegment
import os 

args_ctl =os.path.join('configs', 'deepSample2_to_sess.txt')
# convert session audio to WAV and place in session directories

# options
channels = 1
sample_width = 2
sample_rate = 48000
bit_depth = 16
sess_base_dir = './data/deepSample2/' # where to export session subdirectories

# args_ctl has list of paths to sessions to process
with open(args_ctl) as ctl:
    sesslist = (line.rstrip() for line in ctl) 
    sesslist = list(os.path.normpath(line) for line in sesslist if line)

for sess in sesslist: 
    print(f'sess: {sess}')
    sess = sess.strip()
    sessname = Path(sess).stem
    sesspath = f'{sess_base_dir}/{sessname}/'

    print(sessname)
    aud_type = Path(sess).suffix
    print(aud_type)
    if not os.path.exists(sesspath):
        os.makedirs(sesspath)

    aud = AudioSegment.from_file(sess)
    wav_path = os.path.join(sesspath,f'{sessname}.wav')

    new_audio = aud.set_channels(channels)
    new_audio = new_audio.set_frame_rate(sample_rate)
    new_audio.export(wav_path, format='wav')

