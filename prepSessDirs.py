from rosy_asr_utils import * 
from pathlib import Path
from pydub import AudioSegment
import os 
import shutil

args_ctl =os.path.join('configs', 'sess2wav_5SGcodecs.txt')
# take "loose" WAVs from a single dir and place in session directories


sess_base_dir = './data/comparison_codecs/' # where to export session subdirectories

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

    # aud = AudioSegment.from_file(sess)
    wav_path = os.path.join(sesspath,f'{sessname}.wav')

    # new_audio.export(wav_path, format='wav')

    shutil.copyfile(sess, wav_path)


