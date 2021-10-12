#!/usr/bin/env python3
# vad_wav.py <wav file>
#infile segment file into voiced segments

# This code is a slightly modified version of py-webrtcvad
# The MIT License (MIT)
# 
# Copyright (c) 2016 John Wiseman
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.

import collections
import contextlib
import re
import sys
import wave
import webrtcvad
import os
import argparse

parser = argparse.ArgumentParser(description='segment session files')
parser.add_argument('wav')
parser.add_argument('--agg', default='1')
parser.add_argument('--win_size', default='300',help='window size in msec')
parser.add_argument('--segdir', default='segments')
args = parser.parse_args()


# Read .wav file, and return (PCM audio data, sample rate)
def read_wave(path):
    with contextlib.closing(wave.open(path, 'rb')) as wf:
        num_channels = wf.getnchannels()
        assert num_channels == 1
        sample_width = wf.getsampwidth()
        assert sample_width == 2
        sample_rate = wf.getframerate()
        assert sample_rate in (8000, 16000, 32000)
        pcm_data = wf.readframes(wf.getnframes())
        return pcm_data, sample_rate

# write .wav file
def write_wave(path, audio, sample_rate):
    with contextlib.closing(wave.open(path, 'wb')) as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(audio)

# frame of audio data
class Frame(object):
    def __init__(self, bytes, timestamp, duration):
        self.bytes = bytes
        self.timestamp = timestamp
        self.duration = duration

# generates frames of requested duration from audio data
def frame_generator(frame_duration_ms, audio, sample_rate):
    n = int(sample_rate * (frame_duration_ms / 1000.0) * 2)
    offset = 0
    timestamp = 0.0
    duration = (float(n) / sample_rate) / 2.0
    while offset + n < len(audio):
        yield Frame(audio[offset:offset + n], timestamp, duration)
        timestamp += duration
        offset += n

# Filter out non-voiced audio frames.
# Uses a padded sliding window (rind buffer) over the audio frames.
# Trigger when more than 90% of the frames in the window are voiced
# Detrigger when 90% of the frames in the window are unvoiced
# pads with small amount of silence at start and end
# Arguments:
# sample_rate - The audio sample rate, in Hz.
# frame_duration_ms - The frame duration in milliseconds.
# padding_duration_ms - The amount to pad the window, in milliseconds.
# vad - An instance of webrtcvad.Vad.
# frames - a source of audio frames (sequence or generator).

def vad_collector(sample_rate, frame_duration_ms,
                  padding_duration_ms, vad, frames, max_segment_dur = 60000):
    num_padding_frames = int(padding_duration_ms / frame_duration_ms)

    # use a deque for sliding window/ring buffer.
    ring_buffer = collections.deque(maxlen=num_padding_frames)

    #  start in the NOTTRIGGERED state.
    triggered = False

    # for segment map
    seg_start = ''
    seg_end = ''
    numseg = 0

    voiced_frames = []
    for frame in frames:
        is_speech = vad.is_speech(frame.bytes, sample_rate)

        if not triggered:
            ring_buffer.append((frame, is_speech))
            num_voiced = len([f for f, speech in ring_buffer if speech])

            # If more than 90% of the frames in buffer are voiced, TRIGGER
            num_voiced = len([f for f, speech in ring_buffer if speech])
            if num_voiced > 0.9 * ring_buffer.maxlen:
                triggered = True
                #sys.stdout.write('+(%s)' % (ring_buffer[0].timestamp,))
                #sys.stdout.write('+(%s)' % (ring_buffer[0][0].timestamp,))

                # yield all audio from now until NOTTRIGGERED
		# start with audio already in the ring buffer.
                for f, s in ring_buffer:
                    voiced_frames.append(f)
                seg_start = ring_buffer[0][0].timestamp
                ring_buffer.clear()
        else:
            # in the TRIGGERED state, add data to ring buffer.
            voiced_frames.append(frame)
            ring_buffer.append((frame, is_speech))
            num_unvoiced = len([f for f, speech in ring_buffer if not speech])
            # If more than 90% of the frames in the ring buffer are
            # unvoiced, then enter NOTTRIGGERED and yield whatever
            # audio we've collected.
            if num_unvoiced > 0.9 * ring_buffer.maxlen: # TODO or segment is getting too long
                #sys.stdout.write('-(%s)' % (frame.timestamp + frame.duration))
                triggered = False

                seg_end = frame.timestamp
                segs.append( (numseg, seg_start, seg_end) )
                numseg += 1

                yield b''.join([f.bytes for f in voiced_frames])
                ring_buffer.clear()
                voiced_frames = []
    #if triggered:
        #sys.stdout.write('-(%s)' % (frame.timestamp + frame.duration))
    #sys.stdout.write('\n')

    # If we have any leftover voiced audio when we run out of input,
    # yield it.
    if voiced_frames:
        yield b''.join([f.bytes for f in voiced_frames])
        seg_end = frame.timestamp
        segs.append( (numseg, seg_start, seg_end) )
        numseg += 1

frame_msec = 30
segs = []
sessDir = os.path.dirname(args.wav)
basename = os.path.basename(sessDir)
segDir = '%s/%s' % (sessDir, args.segdir)
if not os.path.exists(segDir):
    os.makedirs(segDir)

audio, sample_rate = read_wave(args.wav)
vad = webrtcvad.Vad(int(args.agg))
frames = frame_generator(frame_msec, audio, sample_rate)
frames = list(frames)
segments = vad_collector(sample_rate,frame_msec,int(args.win_size), vad, frames)

for i, (segment, info) in enumerate(segments):
	#path = 'chunk-%002d.wav' % (i,)
	path = '%s/%s_%d.wav' % (segDir,basename,i)
	#print(' Writing %s' % (path,))
	write_wave(path, segment, sample_rate)

# write out segmap
segmapFile = re.sub('.wav','.seg',args.wav)
with open(segmapFile, 'w') as outfile:
        for s in segs:
                outfile.write('%d %.2f %.2f\n' % (s[0],s[1],s[2]))
