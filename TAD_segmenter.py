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
        win_length=1500,
        win_slide=250,
        threshold,
        speechbrain_dir='../speechbrain/',
        model_type='ecapa',
        enrollment_dir = 'enrollment',
        export_seg_audio=False,
        file_suffix=''):


    # ~~~~SET SOME CONSTANTS~~~~ #
    # TAD OPTIONS: TODO: decide if we want these as function args or just hard code
    minseg = 500 # minimum active duration (ms) to trigger seg start
    minsil = 500 # minimum inactive duration (ms) to trigger seg end


    # SEGMENT BLOCKING OPTIONS:
    BLKSECS = 59 # Max Duration to block segments into. Note: Google ASR has refused some blocks if exactly 60 seconds 
    SPLIT_OVERLAP = 1 # for long segments which require cutting, overlap by this duration in seconds to avoid word splitting
    # AUDIO OPTIONS:
    SAMPLE_WIDTH = 2 # bytes per sample, should usually be 2
    SAMPLE_RATE = 16000 # for webrtcvad needs an srate of 8/16/32/48kHz
    CHANNELS = 1 # mono

    # initialise encoder and verifier
    if model_type == 'ecapa':
        encoder = EncoderClassifier.from_hparams(source="speechbrain/spkrec-ecapa-voxceleb", 
            savedir=f"{speechbrain_dir}/pretrained_models/spkrec-ecapa-voxceleb")
        verifier = SpeakerRecognition.from_hparams(source="speechbrain/spkrec-ecapa-voxceleb", 
            savedir=f"{speechbrain_dir}/pretrained_models/spkrec-ecapa-voxceleb")
    if model_type == 'xvect':
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

        # load session audio
        # sessAudio = AudioSegment.from_file(audioFile)
        # TODO: can torch even deal with .MOV etc? 
    
        # # # set sample rate and channels 
        # sessAudio = sessAudio.set_channels(CHANNELS).set_sample_width(SAMPLE_WIDTH).set_frame_rate(SAMPLE_RATE)

        # get enrollment audio
        found_enrFiles = [f for f in os.listdir(os.path.join(sesspath,enrollment_dir)) \
            if f.split('.')[-1] in ['MOV', 'mov', 'WAV', 'wav', 'mp4', 'mp3', 'm4a', 'aac', 'flac', 'alac', 'ogg']]
        print(f'found {len(found_enrFiles)} enrollment audio files...')

        target_embeddings = {}
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

            print('Precomputing target embeddings...')
            enr_signal, fs = torchaudio.load(enrFile)
            if not fs == SAMPLE_RATE:
                # fs must be SAMPLE_RATE 
                enr_resampler = torchaudio.transforms.Resample(fs, SAMPLE_RATE)
                enr_signal = enr_resampler(enr_signal)
            target_embeddings[speaker] = encoder.encode_batch(enr_signal)

        # get input file info
        metadata = torchaudio.info(audioFile)
        total_frames = metadata.num_frames  
        sess_fs = metadata.sample_rate
        sess_nchan = metadata.num_channels
        if not metadata.sample_rate == SAMPLE_RATE:
            # fs must be SAMPLE_RATE
            sess_resampler = torchaudio.transforms.Resample(metadata.sample_rate, SAMPLE_RATE)

        WIN_SIZE = SAMPLE_RATE * win_length/1000 # in frames
        last_win_st = total_frames - WIN_SIZE  # start frame for last window

    #~~~~TAD FILTER~~~~#
    state = 'o'   # indicates whether inside or outside segment
    seg_sf = 0 # start frame of first sample in segment
    seg_ef = 0 # start frame of last sample in segment
    # use sliding window of WIN_SIZE frames to generate samples
    # compare each sample to all targets
    # generate start and end times for target segments
    segments = []
    for win_st in range(0,last_win_st,SHIFT_LEN):
        # read next sample of WIN_SIZE frames
        win_signal,fs = torchaudio.load(args.wav, frame_offset=win_st, num_frames=WIN_SIZE)
        if not sess_nchan == 1:
            win_signal = torch.mean(win_signal, =0, keepdim=False)
        xv_samp = encoder.encode_batch(win_signal)
        if not sess_fs == SAMPLE_RATE:
            win_signal = sess_resampler(win_signal)

        # compare sample to each target
        scores = []
        for t in target_embeddings:
            score = verifier.similarity(target_embeddings[t], xv_samp)
            scores.append(score.item())
        frame_score = 0

        # set sample score to 1 if any target score > threshold
        for s in scores:
            if s > threshold: frame_score = 1
        #tim = '%f.1' % (FRAME_DUR * win_st)
        #print(tim, frame_score)

        # if inside segment
        if state == 'i':
            # if sample is target continue inside seg
            if frame_score:
                seg_ef = win_st
                continue

            # sample is not target
            # if seg too short, discard
            if (seg_ef - seg_sf) < minseg:
                state = 'o'
                continue

            # if sil too short, don't terminate seg
            if ((win_st - seg_ef) + WIN_SIZE) < minsil: continue

            # terminate and save segment
            # determine seg boundaries in secs
            # start mid first seg, end mid last seg
            seg_stsec = (seg_sf + (WIN_SIZE/2)) * FRAME_DUR
            seg_edsec = (seg_ef + (WIN_SIZE/2)) * FRAME_DUR
            seg = []
            seg.append(seg_stsec)
            seg.append(seg_edsec)
            seg.append(1)
            for s in scores:
                seg.append(s)
            segments.append(seg)
            state = 'o'

        # if outside segment
        else:
            # if target segment start new seg
            if frame_score:
                seg_sf = win_st
                seg_ef = win_st
                state = 'i'
            # else continue outside

    # with open("out.csv", "w", newline="") as f:
    #     writer = csv.writer(f)
    #     writer.writerows(segments)