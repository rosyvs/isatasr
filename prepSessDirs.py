from rosy_asr_utils import * 
from pathlib import Path
from pydub import AudioSegment
import argparse
import os 
import shutil



def prepSessDirs(filelist, outdir, link_media, convert_to_wav):
    """Create session directories"""
    # WAV options
    CHANNELS = 1
    SAMPLE_RATE = 48000

    with open(filelist) as ctl:
        medialist = (line.rstrip() for line in ctl) 
        medialist = list(os.path.normpath(line) for line in medialist if line)

    for media_path in medialist: 
        print(f'media: {media_path}')
        media_path = media_path.strip()

        sessname = Path(media_path).stem
        # remove extra extensions e.g. .mp4.mp4 that are present in some source media files
        sessname = sessname.split('.')[0]

        sesspath = os.path.join(outdir,sessname)
        print(f'...Creating session directory at {outdir}')

        print(f'...Extracted session name from media file: {sessname}')
        aud_type = Path(media_path).suffix
        print(f'...Input media type: {aud_type}')
        if not aud_type[1:] in ['MOV', 'mov', 'WAV', 'wav', 'mp4', 'mp3', 'm4a', 'aac', 'flac', 'alac', 'ogg']:
            print(f'WARNING: {media_path} with extesion {aud_type} is not a supported media file. No session directory made.')
            continue
        os.makedirs(sesspath,exist_ok=True)

        if link_media:
            with open(os.path.join(sesspath,'LINKED_MEDIA.txt'),'w') as linkfile:
                linkfile.write(media_path)
            print(f'...Made a link to media in LINKED_MEDIA.txt')

        else:
            if convert_to_wav:
                aud = AudioSegment.from_file(media_path)
                wav_path = os.path.join(sesspath,f'{sessname}.wav')

                new_audio = aud.set_channels(CHANNELS)
                new_audio = new_audio.set_frame_rate(SAMPLE_RATE)
                new_audio.export(wav_path, format='wav')
                print(f'...Converted media to .WAV.')
            else: 
                shutil.copyfile(media_path, os.path.join(sesspath,f'{sessname}{aud_type}'))
                print(f'...Copied {aud_type} file without conversion')


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='Create session directory for ASR & copy media')
    parser.add_argument('filelist', nargs='?', default='./configs/EXAMPLEprepSessDirs.txt', help='path to text file containing list of audio file paths')
    parser.add_argument('outdir',nargs='?',  default='./data/EXAMPLE',help='top-level directory in which to make session directories')
    group = parser.add_mutually_exclusive_group()
    group.add_argument('-l','--link_media', action='store_true', help='create link to media without copying to session directory? (default False)')
    group.add_argument('-w','--convert_to_wav', action='store_true', help='copy media to session directory and convert to WAV? (default False)')
    args = parser.parse_args()

    prepSessDirs(filelist = args.filelist, outdir=args.outdir, link_media = args.link_media, convert_to_wav=args.convert_to_wav)