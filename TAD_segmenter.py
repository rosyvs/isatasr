import torchaudio
from torch import tensor, cat, squeeze, mean
import os
from pathlib import Path
import re
import pandas as pd
import numpy as np
from pydub.audio_segment import AudioSegment, effects
from speechbrain.pretrained import EncoderClassifier, SpeakerRecognition
from speechbrain.utils.metric_stats import EER
from rosy_asr_utils import get_sess_audio
from tqdm import tqdm

# ASR pipeline
# 1. prepSessDirs
# 2. VAD_segmenter / TAD_segmenter (uses automated segmentation) OR segFromAnnotation (uses timestamped transcript)
# 3. ASRsegwiseGoogle (or REV, Watson)
# 4. WER_by_speaker (after formatELANtranscripts/formatREVtranscripts)

# Takes .wav audio from session directories with relative path <sesspath> specifed in control file
# - uses TAD to segment audio into utterances, requires enrollment audio
# - concatenates utterances to blocks of maximum duration blksecs (1 minute suggested as 
# most economcial for sending to REV, max duration for synchronous Google ASR)
# - exports segment and block audio in subdirectories (see below)

# session directory structure for a given audio file should be:
#    |--{sessname}
#       |--{sessname}.wav # full session audio
# the following will be generated:
#       |--TAD_{sessname}.blk # maps block and segment numbers to times in full session audio; columns block_no, segment_no, start_s, end_s
#       |--TADblocks
#          |--{sessname}_{block_no}.wav
#       |--TADsegments
#          |--{sessname}_{segment_no}.wav       

def segFromTAD(filelist,
        threshold=None,
        win_length_s=1.5,
        win_shift_s=.25,
        speechbrain_dir='../speechbrain/',
        model_type='ecapa',
        enrollment_dir = 'enrollment',
        export_seg_audio=False,
        file_suffix=''):


    # ~~~~SET SOME CONSTANTS~~~~ #
    # TAD OPTIONS: TODO: decide if we want these as function args or just hard code
    MINSEG_S = .5 # minimum active duration (s) to trigger seg start
    MINSIL_S = .5 # minimum inactive duration (s) to trigger seg end
    # default thresholds (Determined using cross-validation on iSAT deep sample, optimising for pairwise speaker verification acc)
    DEFAULT_THRESH = {}
    DEFAULT_THRESH['xvect'] = .948
    DEFAULT_THRESH['ecapa'] = .157
    if not threshold: # use default values if not set
        threshold = DEFAULT_THRESH[model_type]
    # TODO: SEGMENT BLOCKING OPTIONS:
    b=0 # just call everything block 0 for now
    BLKSECS = 59 # Max Duration to block segments into. Note: Google ASR has refused some blocks if exactly 60 seconds 
    SPLIT_OVERLAP = 1 # for long segments which require cutting, overlap by this duration in seconds to avoid word splitting
    # AUDIO OPTIONS:
    SAMPLE_WIDTH = 2 # bytes per sample, should usually be 2
    SAMPLE_RATE_TAD = 16000 # for webrtcvad needs an srate of 8/16/32/48kHz
    CHANNELS = 1 # mono
    # ~~~~SET SOME CONSTANTS~~~~ #

    # initialise encoder and verifier
    if model_type == 'ecapa':
        encoder = EncoderClassifier.from_hparams(source="speechbrain/spkrec-ecapa-voxceleb", 
            savedir=f"{speechbrain_dir}/pretrained_models/spkrec-ecapa-voxceleb")
        verifier = SpeakerRecognition.from_hparams(source="speechbrain/spkrec-ecapa-voxceleb", 
            savedir=f"{speechbrain_dir}/pretrained_models/spkrec-ecapa-voxceleb")
    elif model_type == 'xvect':
        encoder = EncoderClassifier.from_hparams(source="speechbrain/spkrec-xvect-voxceleb", 
            savedir=f"{speechbrain_dir}/pretrained_models/spkrec-xvect-voxceleb")
        verifier = SpeakerRecognition.from_hparams(source=f"{speechbrain_dir}/pretrained_models/spkrec-xvect-voxcelebTEST", 
            savedir=f"{speechbrain_dir}/pretrained_models/spkrec-xvect-voxceleb")

    # loop over sessions
    with open(filelist) as ctl:
        sesslist = (line.rstrip() for line in ctl) 
        sesslist = list(os.path.normpath(line) for line in sesslist if line)

    for sesspath in sesslist: 
        print(f'sesspath: {sesspath}')
        sesspath = sesspath.strip()
        sessname = os.path.basename(sesspath)
        blkmapFile = os.path.join(sesspath, f'TAD_{sessname}.blk')
        blkmap=[]
        if export_seg_audio: 
            print('Exporting segmented audio...')
            segDir = os.path.join(sesspath, f'TADsegments{file_suffix}')
            blkDir = os.path.join(sesspath, f'TADblocks{file_suffix}')
            os.makedirs(segDir, exist_ok=True)
            os.makedirs(blkDir, exist_ok=True)

        # get session audio to filter
        audioFile = get_sess_audio(sesspath)
        if not audioFile:
            print('!!! No audio file found! Skipping...')
            continue
        else:
            aud_type = Path(audioFile).suffix
            print(f'Input media type: {aud_type}')

        # get enrollment audio
        found_enrFiles = [f for f in os.listdir(os.path.join(sesspath,enrollment_dir)) \
            if f.split('.')[-1] in ['MOV', 'mov', 'WAV', 'wav', 'mp4', 'mp3', 'm4a', 'aac', 'flac', 'alac', 'ogg']]
        print(f'found {len(found_enrFiles)} enrollment audio files...')

        target_embeddings = {}
        print('Precomputing target embeddings...')

        for f in found_enrFiles:
            enrFile = os.path.join(sesspath, enrollment_dir, f)
            # TODO: load direct into torch or convert
            # enrAudio = AudioSegment.from_file(enrFile)
            # enrDur = enrAudio.duration_seconds
            # # convert as needed
            # enrAudio =enrAudio.set_channels(CHANNELS).set_sample_width(SAMPLE_WIDTH).set_frame_rate(SAMPLE_RATE)
            # strip keyword parts of filename in crude attempt to get target name 
            speaker =  os.path.basename(f)
            speaker = re.sub('enrollment_simulated_','',speaker)
            speaker = re.sub('enrollment_','',speaker)

            enr_signal, enr_fs = torchaudio.load(enrFile)
            if not enr_fs == SAMPLE_RATE_TAD:
                # fs must be SAMPLE_RATE 
                enr_resampler = torchaudio.transforms.Resample(enr_fs, SAMPLE_RATE_TAD)
                enr_signal = enr_resampler(enr_signal)
            target_embeddings[speaker] = encoder.encode_batch(enr_signal)

        # # load session audio
        # sessAudio = AudioSegment.from_file(audioFile)
        # TODO: can torch even deal with .MOV etc? 
        # # set sample rate and channels 
        # sessAudio = sessAudio.set_channels(CHANNELS).set_sample_width(SAMPLE_WIDTH).set_frame_rate(SAMPLE_RATE)

        # get input file info
        metadata = torchaudio.info(audioFile)
        total_samples = metadata.num_frames  
        total_secs = total_samples/metadata.sample_rate
        sess_fs = metadata.sample_rate
        sess_nchan = metadata.num_channels
        print(f'Session audio duration: {total_secs}s')
        if not sess_fs == SAMPLE_RATE_TAD:
            # fs must be SAMPLE_RATE
            print(f'Audio has Fs={sess_fs}, Fs={SAMPLE_RATE_TAD} required for TAD. Will downsample.')
            win_resampler = torchaudio.transforms.Resample(sess_fs, SAMPLE_RATE_TAD)
        torchaudio.info(audioFile)
        WIN_SAMPLES = int(SAMPLE_RATE_TAD * win_length_s) # in frames
        SHIFT_SAMPLES = int(SAMPLE_RATE_TAD*win_shift_s) # in frames
        LAST_WIN_S = total_secs - win_length_s  # start frame for last window
        print(LAST_WIN_S)
        SAMPLE_DUR = 1.0/SAMPLE_RATE_TAD # single audio sample duration in seconds
        MINSEG = SAMPLE_RATE_TAD * MINSEG_S
        MINSIL = SAMPLE_RATE_TAD * MINSIL_S
        #~~~~TAD FILTER~~~~#
        state = 'o'   # indicates whether inside or outside segment
        seg_start_s = 0 # start frame of first sample in segment
        seg_end_s = 0 # start frame of last sample in segment
        seg=0 # segment counter
        # use sliding window of WIN_SIZE frames to generate samples
        # compare each sample to all targets
        # generate start and end times for target segments
        N_WIN=int(total_secs/win_shift_s)
        print(f'Running TAD filter on {N_WIN} windows...')
        # for win_start_s in tqdm(range(0,LAST_WIN_S,win_shift_s)):
        for win in tqdm(range(0,N_WIN)):
            target_detected = 0
            win_start_s = win*win_shift_s
            # read next sample of WIN_SIZE frames
            win_signal,enr_fs = torchaudio.load(audioFile, 
            frame_offset=int(win_start_s*sess_fs), num_frames=int(win_length_s*sess_fs))
            # set to mono and correct sample rate for TAD
            if not sess_nchan == 1:
                win_signal = mean(win_signal, dim=0, keepdim=False)
            if not sess_fs == SAMPLE_RATE_TAD:
                win_signal = win_resampler(win_signal)
            emb_samp = encoder.encode_batch(win_signal)

            # compare sample to each target
            scores = []
            for speaker, emb_tgt in target_embeddings.items():
                score = verifier.similarity(emb_tgt, emb_samp)
                scores.append(score.item())

            # set sample score to 1 if any target score > threshold
            for s in scores:
                if s > threshold: 
                    target_detected = 1
                    continue

            # if inside segment
            if state == 'i':
                # if sample is target continue inside seg
                if target_detected:
                    seg_end_s = win_start_s
                    continue

                # sample is not target
                # if seg too short, discard
                if (seg_end_s - seg_start_s) < MINSEG_S:
                    state = 'o'
                    continue

                # if sil too short, don't terminate previousseg
                if ((win_start_s - seg_end_s) + win_length_s) < MINSIL_S: 
                    continue

                # terminate and save segment
                # determine seg boundaries in secs
                # start mid first seg, end mid last seg # TODO: not sure about this, why not take whole seg
                seg_stsec = seg_start_s + (win_length_s/2) 
                seg_edsec = seg_end_s + (win_length_s/2)
                # seg = []
                # seg.append(seg_stsec)
                # seg.append(seg_edsec)
                # seg.append(1)
                # print(seg)
                blkseg = [b, seg, seg_stsec, seg_edsec] # for blk file

                segscores = [b, seg, seg_stsec, seg_edsec]
                seg+=1

                for s in scores:
                    segscores.append(s)
                blkmap.append(blkseg)
                state = 'o'

            # if outside segment
            else:
                # if target segment start new seg
                if target_detected:
                    seg_start_s = win_start_s
                    seg_end_s = win_start_s # TODO: why both set to win_start? 
                    state = 'i'
                # else continue outside

        print(blkmap)
        # #TODO:if export_seg_audio: 
        #     # end of loop over segments: write out any remaining audio to final block
        #     blkwavpath = os.path.join(blkDir,f'{sessname}_{b}.wav' )
        #     this_block.export(blkwavpath, format='wav')

        with open(blkmapFile, 'w') as outfile:
            for segment in blkmap:
                line = ' '.join(str(x) for x in segment)
                outfile.write(line + '\n')
    # with open("out.csv", "w", newline="") as f:
    #     writer = csv.writer(f)
    #     writer.writerows(segments)