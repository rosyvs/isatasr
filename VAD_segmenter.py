from rosy_asr_utils import * 
from pathlib import Path
from pydub import AudioSegment
import io
import os
import argparse
import webrtcvad

# ASR pipeline
# 1. prepSessDirs
# 2. VAD_segmenter / TAD_segmenter (uses automated segmentation) OR segFromAnnotation (uses timestamped transcript)
# 3. ASRsegwiseGoogle (or REV, Watson)
# 4. WER_by_speaker (after formatELANtranscripts/formatREVtranscripts)

# Takes .wav audio from session directories with relative path <sesspath> specifed in control file
# - uses VAD to segment audio into utterances
# - concatenates utterances to blocks of maximum duration blksecs (1 minute suggested as 
# most economcial for sending to REV, max duration for synchronous Google ASR)
# - exports segment and block audio in subdirectories (see below)

# session directory structure for a given audio file should be:
#    |--{sessname}
#       |--{sessname}.wav # full session audio
# the following will be generated:
#       |--{sessname}.blk # maps block and segment numbers to times in full session audio; columns block_no, segment_no, start_s, end_s
#       |--blocks
#          |--{sessname}_{block_no}.wav
#       |--segments
#          |--{sessname}_{segment_no}.wav       

def segFromVAD(filelist,
        agg,
        frame_length,
        win_length,
        min_seg_dur,
        export_seg_audio=False,
        file_suffix=''):
    # segmentation options
    BLKSECS = 59 # Max Duration to block segments into. Note: Google ASR has refused some blocks if exactly 60 seconds 
    SPLIT_OVERLAP = 1 # for long segments which require cutting, overlap by this duration in seconds to avoid word splitting
    # .wav audio output options:
    SAMPLE_WIDTH = 2 # bytes per sample, should usually be 2
    SAMPLE_RATE = 16000 # for webrtcvad needs an srate of 8/16/32/48kHz
    CHANNELS = 1 # for webrtcvad needs to be mono

    with open(filelist) as ctl:
        sesslist = (line.rstrip() for line in ctl) 
        sesslist = list(os.path.normpath(line) for line in sesslist if line)

    for sesspath in sesslist: 
        print(f'sesspath: {sesspath}')
        sesspath = sesspath.strip()
        sessname = os.path.basename(sesspath)
        blkmapFile = os.path.join(sesspath, f'VAD_{sessname}.blk')

        if export_seg_audio: 
            print('Exporting segmented audio...')
            segDir = os.path.join(sesspath, f'VADsegments{file_suffix}')
            blkDir = os.path.join(sesspath, f'VADblocks{file_suffix}')
            os.makedirs(segDir, exist_ok=True)
            os.makedirs(blkDir, exist_ok=True)

        audiofile = get_sess_audio(sesspath)
        if not audiofile:
            print('!!! No audio file found! Skipping...')
            continue
        else:
            aud_type = Path(audiofile).suffix
            print(f'Input media type: {aud_type}')


        # load session audio
        sess_audio = AudioSegment.from_file(audiofile)

        # # set sample rate and channels 
        sess_audio = sess_audio.set_channels(CHANNELS).set_sample_width(SAMPLE_WIDTH).set_frame_rate(SAMPLE_RATE)

        # initialise VAD
        vad = webrtcvad.Vad(int(agg))
        frames = frame_generator(frame_length, sess_audio.raw_data, SAMPLE_RATE)
        frames = list(frames)
        segment_generator = vad_collector(SAMPLE_RATE,frame_length,int(win_length), vad, frames, min_seg_dur)

        blkmapFile = os.path.join(sesspath,f'{sessname}{file_suffix}.blk')
        blkmap = []
        b= 0
        this_block = AudioSegment.empty() # for raw audio data
        curlen = 0.0
        added_segs = 0
        for i, (segment, info) in enumerate(segment_generator):

            snum,beg,end = info
            dur = end - beg
            stream = io.BytesIO(segment)
            seg_audio = AudioSegment.from_raw(stream, sample_width=SAMPLE_WIDTH, frame_rate=SAMPLE_RATE, channels=CHANNELS)

            ## Concatenate segments to form blocks - economical/betetr resukt for some ASR providers
            # split segments longer than requested block duration
            if dur > BLKSECS:
                nsplits = int(np.floor((dur-SPLIT_OVERLAP)/(BLKSECS-SPLIT_OVERLAP)))
                print(f'VAD segment at block {b} is longer than requested block duration, will split into {nsplits+1}')

                for k in range(0,nsplits):
                    beg_trim = k*(BLKSECS-SPLIT_OVERLAP)
                    end_trim = beg_trim + BLKSECS
                    segment_trim = seg_audio[np.round(beg_trim*1000):np.round(end_trim*1000)]
                    # print(f'trimmed AudioSegment length:{segment_trim.duration_seconds}')
                    blkmap.append( (b, added_segs+snum, beg+beg_trim, beg+end_trim)) 

                    if export_seg_audio: 

                        blkwavpath = os.path.join(blkDir,f'{sessname}_{b}.wav' )
                        segment_trim.export(blkwavpath, format='wav')
                        
                        segwavpath = os.path.join(segDir,f'{sessname}_{added_segs+snum}.wav' )
                        segment_trim.export(segwavpath, format='wav')
                        this_block = AudioSegment.empty() # start new audio block

                    added_segs +=1 # will offset all future segment numbers by this count 
                    b += 1
                    curlen = 0.0
                
                # for final split leave the block incomplete to append to other segments
                curlen += dur-end_trim
                blkmap.append( (b, added_segs+snum, beg+end_trim, end) )
                if export_seg_audio: 
                    seg_audio = seg_audio[end_trim*1000: dur*1000] 
                    this_block += seg_audio
                    segwavpath = os.path.join(segDir,f'{sessname}_{added_segs+snum}.wav' )
                    seg_audio.export(segwavpath, format='wav') 
                continue 

            # add segment to current block
            if (curlen + dur) <= BLKSECS:
                blkmap.append( (b, added_segs+snum, beg,end) )
                curlen += dur
                if export_seg_audio: 
                    this_block += seg_audio
                    segwavpath = os.path.join(segDir,f'{sessname}_{added_segs+snum}.wav' )
                    seg_audio.export(segwavpath, format='wav') 
                continue

            # block is now complete
            else:
                if export_seg_audio: 

                    # complete block and write audio
                    blkwavpath = os.path.join(blkDir,f'{sessname}_{b}.wav' )
                    this_block.export(blkwavpath, format='wav')

                    # write segment audio
                    segwavpath = os.path.join(segDir,f'{sessname}_{added_segs+snum}.wav' )
                    seg_audio.export(segwavpath, format='wav') 
                    this_block = AudioSegment.empty()
                    this_block += seg_audio
                #  reset/increment counters
                b += 1
                blkmap.append( (b, added_segs+snum, beg,end) )
                curlen = dur

        if export_seg_audio: 
            # end of loop over segments: write out any remaining audio to final block
            blkwavpath = os.path.join(blkDir,f'{sessname}_{b}.wav' )
            this_block.export(blkwavpath, format='wav')

        with open(blkmapFile, 'w') as outfile:
            for segment in blkmap:
                line = ' '.join(str(x) for x in segment)
                outfile.write(line + '\n')

        print(f'VAD split audio into {blkmap[-1][1]} segments, and blocked into {b} blocks.')
        # segment coverage - how much audio remains after VAD filtering. 
        coverage = segment_coverage(blkmapFile, audiofile)
        print(f'SEGMENT COVERAGE: {100*coverage:.2f}% of original audio [{sessname}]')
        if coverage >1:
            print('--coverage greater than 100%% because of overlap between split segments')

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Run VAD')
    parser.add_argument('filelist',nargs='?', default='./configs/EXAMPLE.txt', help='path to text file containing list of file paths to run VAD on')
    parser.add_argument('range_file', nargs='?', default=None, help='Specify time range to extract segments from media, reading from ')
    parser.add_argument('-e','--export_seg_audio',action='store_true',help='export segmented & blocked audio? (default False)')
    parser.add_argument('-a','--agg', default=1,help='aggressiveness of VAD (0-3)')
    parser.add_argument('-l','--frame_length', default=20,help='frame length sent to VAD')
    parser.add_argument('-w','--win_length', default=300,help='window size (ms) for VAD buffer')
    parser.add_argument('-m','--min_seg_dur', default=1000,help='ms. minimum segment duration')
    parser.add_argument('-f','--file_suffix',default='', help='filename suffix for .blk file of segment start and end times')
    args = parser.parse_args()

    segFromVAD(filelist=args.filelist,
        export_seg_audio = args.export_seg_audio,
        agg=args.agg,
        frame_length = args.frame_length,
        win_length = args.win_length,
        min_seg_dur = args.min_seg_dur,
        file_suffix = args.file_suffix)