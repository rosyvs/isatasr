# target activity detection
# tad.py <path to wav file>
# generate list of segments containing target speakers
#     generate inital set of segments using vad
#     trim segments to remove portions not containing a target speaker
#     targets/ dir must be in same dir as wav file
#     creates segments/ dir in same dir as wav file
#     output:
#       seg_map - segnum, start_ms, end_ms
#       cnk_labels - cnk_name_seg#_cnk#, 0/1     1 = contains target
#       segments/*.wav         output trimmed wav files

from speechbrain.pretrained import VAD
from speechbrain.pretrained import SpeakerRecognition
from pathlib import Path
from pydub import AudioSegment
from pydub.utils import make_chunks
import os
import argparse

parser = argparse.ArgumentParser(description='segment session files')
parser.add_argument('wav', help='path to wav file')
parser.add_argument('--chunk_len_msec', default='1000',help='chunk len msec')
args = parser.parse_args()

# paths
sess_dir = os.path.dirname(args.wav)               # sess dir
basename = Path(args.wav).stem                     # sess name
chunks_dir = os.path.join(sess_dir,'chunks')       # temporary chunk files
targets_dir = os.path.join(sess_dir,'targets')     # target files
segments_dir = os.path.join(sess_dir,'segments')   # output segment files

# initialize VAD
VAD = VAD.from_hparams(source="speechbrain/vad-crdnn-libriparty",
        savedir="pretrained_models/vad-crdnn-libriparty")

# generate list of vocalized segments
segments = VAD.get_speech_segments(args.wav)

######### VAD.get_speech_segments() consists of following steps
# compute frame-level posteriors
#audio_file = 'pretrained_model_checkpoints/example_vad.wav'
#prob_chunks = VAD.get_speech_prob_file(audio_file)

# apply a threshold on top of the posteriors
#prob_th = VAD.apply_threshold(prob_chunks).float()

# derive the candidate speech segments
#boundaries = VAD.get_boundaries(prob_th)

# Apply energy VAD within each candidate speech segment (optional)
#boundaries = VAD.energy_VAD(audio_file,boundaries)

# Merge segments that are too close
#boundaries = VAD.merge_close_segments(boundaries, close_th=0.250)

# Remove segments that are too short
#boundaries = VAD.remove_short_segments(boundaries, len_th=0.250)

# Double-check speech segments (optional).
#boundaries = VAD.double_check_speech_segments(boundaries, audio_file,  speech_th=0.5)
############


# Print the output
#VAD.save_boundaries(segments)
# save to file
#VAD.save_boundaries(segments, save_path='VAD_file.txt')

# read wav file
audio = AudioSegment.from_file(args.wav , "wav") 

# initialize verification model
verification = SpeakerRecognition.from_hparams(\
    source="speechbrain/spkrec-ecapa-voxceleb", \
    savedir="pretrained_models/spkrec-ecapa-voxceleb")

if not os.path.exists(chunks_dir):
    os.makedirs(chunks_dir)
if not os.path.exists(segments_dir):
    os.makedirs(segments_dir)
# open seg_map file for write
seg_map_file = os.path.join(sess_dir, 'seg_map')
segmapF = open(seg_map_file, 'w')

# chunk each segment
# classify each chunk as target/not target
# filter non-target chunks from each segment
cnklist = []
for sn, seg in enumerate(segments):
    # get audio slice for segment
    start_msec = int(1000 * float(seg[0]))
    end_msec = int(1000 * float(seg[1]))
    seg_audio = audio[start_msec:end_msec]

    # write out segment timings
    segmapF.write('%d %d %d\n' % (sn,start_msec, end_msec))

    # make list of chunks for segment
    chunk_length_ms = int(args.chunk_len_msec)
    chunks = make_chunks(seg_audio, chunk_length_ms) # pydub make_chunks

    first = 1
    # output segments containing only target chunks
    for cn, chunk in enumerate(chunks):
        # Export chunk as wav files
        chunk_name = '%s/%s_%d.wav' % (chunks_dir, sn, cn)
        chunk.export(chunk_name, format="wav")

        # classify chunk using targets
        is_target = 0
        # for each target file in dir
        for trg in os.listdir(targets_dir):
            trgfile = os.path.join(targets_dir, trg)

            # classify chunk as target/nontarget
            score, prediction = verification.verify_files(chunk_name,trgfile)
            if prediction.item() == True:
                is_target = 1
                break

        # save classification for chunk
        cnklist.append((chunk_name,is_target))

        # include in trimmed segment if target
        if is_target:
            if first:
                newseg_audio = AudioSegment.from_wav(chunk_name)
                first = 0
            else:
                new = AudioSegment.from_wav(chunk_name)
                newseg_audio += new
    
    # write trimmed segment
    segname = os.path.join(segments_dir, '%d.wav' % sn)
    newseg_audio.export(segname, format='wav')

# write chunk map
cnk_labels = os.path.join(sess_dir, 'cnk_labels')
with open(cnk_labels,'w') as outfile:
    for cnk in cnklist:
        outfile.write('%s %d\n' % (cnk[0],cnk[1]))
