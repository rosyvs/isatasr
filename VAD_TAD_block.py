from rosy_asr_utils import * 
from pathlib import Path
from pydub import AudioSegment
import io

# Takes audio from specified subdirectory of sess dir, 
# directory structure is 
# data
# |--sess
#    |--{sessname}
#       |--{sessname}.wav # full session audio
#       |--{sessname}.blk # maps .wav files in blocks dir to full session audio
#       |--blocks
#          |--{sessname}_{block_no}.wav
#       |--sg_excerpts 
#          |--{sessname}_ex{excerpt_no}.wav # excerpted small group audio
#          |--{sessname}_ex{excerpt_no}.blk # maps .wav files in blocks dir to smallgroup audio excerpts
#          |--blocks # or blocks_agg{0,1,2,3} for comparing VAD settings
#             |--{sessname}_ex{}_{block_no}.wav


subdirectory = 'sg_excerpts' # leave blank for full session audio.

args_ctl =os.path.join('configs', 'sesstoREV_2021-10-04.txt') # this is the control file - list of paths to sessname rel to this script

# options
agg = 1
frame_msec = 30
win_size = 300
blksecs = 60
channels = 1
sample_width = 2
sample_rate = 16000
bit_depth = 16

# ctl has list of paths to audio to process
with open(args_ctl) as ctl:
    sesslist = (line.rstrip() for line in ctl) 
    sesslist = list(os.path.normpath(line) for line in sesslist if line)

for sesspath in sesslist: 
    print(f'sesspath: {sesspath}')
    sessname = Path(sesspath).stem
    wavpath = os.path.join(sesspath,subdirectory)

    wavlist = [f for f in os.listdir(wavpath) if f.endswith('.wav')]

    # segDir = os.path.join(wavpath, 'segments')
    # blkDir = os.path.join(wavpath, f'blocks_agg{agg}')
    blkDir = os.path.join(wavpath, f'blocks')

    # if not os.path.exists(segDir):
    #     os.makedirs(segDir)
    if not os.path.exists(blkDir):
        os.makedirs(blkDir)

    for w in wavlist:       
        wbasename = Path(w).stem
        print(f'Processing wav file: {wbasename}')
        audio, sample_rate = read_wave(os.path.join(wavpath,w))
        vad = webrtcvad.Vad(int(agg))
        frames = frame_generator(frame_msec, audio, sample_rate)
        frames = list(frames)
        segment_generator = vad_collector(sample_rate,frame_msec,int(win_size), vad, frames)
#        blkmapFile = os.path.join(wavpath,f'{wbasename}_agg{agg}.blk')
        blkmapFile = os.path.join(wavpath,f'{wbasename}.blk')

        # file = open(segmapFile,"w") # clear file
        # file.close()# clear file
        
        # # WRITE OUT SEGMENTS AND .seg
        # for i, (segment, info) in enumerate(segment_generator):
        #     path = os.path.join(segDir,f'{wbasename}_{i}.wav' )

        #     #print(' Writing %s' % (path,))
        #     write_wave(path, segment, sample_rate)
        #     with open(segmapFile, 'a+') as outfile:
        #         outfile.write('%d %.2f %.2f\n' % (info[0],info[1],info[2]))

        # append segments to make blocks
        blkmap = []
        blknum= 0
        this_block = AudioSegment.empty() # for raw audio data
        curlen = 0.0
        added_segs = 0
        for i, (segment, info) in enumerate(segment_generator):

            snum,beg,end = info
            dur = end - beg
            stream = io.BytesIO(segment)
            seg_audio = AudioSegment.from_raw(stream, sample_width=sample_width, frame_rate=sample_rate, channels=channels)

            # split segments longer than requested block duration
            if dur > blksecs:
                nsplits = int(np.floor(dur/blksecs))
                print(f'VAD segment at block {blknum} is longer than requested block duration, will split into {nsplits+1}')

                for k in range(0,nsplits):
                    beg_trim = k*blksecs
                    end_trim = beg_trim + blksecs
                    print(f'blknum: {blknum}')
                    print(f'dur: {dur}')
                    print(f'beg_trim: {beg_trim}')
                    print(f'end_trim: {end_trim}')
                    print(f'AudioSegment length:{seg_audio.duration_seconds}')

                    segment_trim = seg_audio[np.round(beg_trim*1000):np.round(end_trim*1000)]
                    print(f'trimmed AudioSegment length:{segment_trim.duration_seconds}')

                    blkmap.append( (blknum, added_segs+snum, beg+beg_trim, beg+end_trim)) 
                    blkwavpath = os.path.join(blkDir,f'{wbasename}_{blknum}.wav' )
                    segment_trim.export(blkwavpath, format='wav')
                    # this_block.append(segment_trim._data)
                    
                    added_segs +=1 # will offset all future segment numbers by this count 
                    # start new audio block
                    blknum += 1
                    this_block = AudioSegment.empty()
                    curlen = 0.0
                print(f'END TRIM blknum:{blknum}')
                seg_audio = seg_audio[end_trim*1000: dur*1000] # for final split leave it to append to other segments
                this_block += seg_audio
                curlen += dur-end_trim
                blkmap.append( (blknum, added_segs+snum, beg+end_trim, end) )

            # add segment to current block
            if (curlen + dur) <= blksecs:
                this_block += seg_audio
                blkmap.append( (blknum, added_segs+snum, beg,end) )

                curlen += dur
                continue

            # export audio
            else:
                blkwavpath = os.path.join(blkDir,f'{wbasename}_{blknum}.wav' )
                this_block.export(blkwavpath, format='wav')
                # start new audio block
                blknum += 1
                this_block = AudioSegment.empty()
                curlen = 0.0

        # end of loop over segments: write out any remaining audio to final block
        blkwavpath = os.path.join(blkDir,f'{wbasename}_{blknum}.wav' )
        this_block.export(blkwavpath, format='wav')


        with open(blkmapFile, 'w') as outfile:
            for b in blkmap:
                line = ' '.join(str(x) for x in b)
                outfile.write(line + '\n')
            