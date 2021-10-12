# tad_gold < session path>
# filter chunks for target speech using human chunk annotation 

import collections
import contextlib
import re
import sys
import wave
import webrtcvad # implements VAD used for generating segments
import os
import argparse

parser = argparse.ArgumentParser(description='segment session files')
parser.add_argument('sess')
parser.add_argument('--min_seg', default='350')
parser.add_argument('--min_sil', default='0.9')
args = parser.parse_args()


def read_wave(path):
    """Reads a .wav file.
    Takes the path, and returns (PCM audio data, sample rate).
    """
    with contextlib.closing(wave.open(path, 'rb')) as wf:
        num_channels = wf.getnchannels()
        assert num_channels == 1
        sample_width = wf.getsampwidth()
        assert sample_width == 2
        sample_rate = wf.getframerate()
        assert sample_rate in (8000, 16000, 32000, 48000)
        pcm_data = wf.readframes(wf.getnframes())
        return pcm_data, sample_rate


def write_wave(path, audio, sample_rate):
    """Writes a .wav file.
    Takes path, PCM audio data, and sample rate.
    """
    with contextlib.closing(wave.open(path, 'wb')) as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(audio)


class Frame(object):
    """Represents a "frame" of audio data."""
    def __init__(self, bytes, timestamp, duration):
        self.bytes = bytes
        self.timestamp = timestamp
        self.duration = duration


def frame_generator(frame_duration_ms, audio, sample_rate):
    """Generates audio frames from PCM audio data.
    Takes the desired frame duration in milliseconds, the PCM data, and
    the sample rate.
    Yields Frames of the requested duration.
    """
    n = int(sample_rate * (frame_duration_ms / 1000.0) * 2)
    offset = 0
    timestamp = 0.0
    duration = (float(n) / sample_rate) / 2.0
    while offset + n < len(audio):
        yield Frame(audio[offset:offset + n], timestamp, duration)
        timestamp += duration
        offset += n


# use session name as basename
basename = os.path.basename(args.sess)
cnkfile = os.path.join(args.sess,'%s.cnk' % basename)
gldfile = os.path.join(args.sess,'%s.gld' % basename)

# use a deque for sliding window/ring buffer.
buflen = 3
ring_buffer = collections.deque(maxlen=3)

triggered = False
target_segments = []
target_frames = []
# read ground truth label for each chunk and label segment using threshold
for line in open(cnkfile):
	line = line.strip()
	file,tag = line.split()
	if tag.find('t') != -1:
		is_target = 1
	else:
		is_target = 0

	if not triggered:
		ring_buffer.append((file, is_target))

		num_targ = len([f for f, targ in ring_buffer if targ])
		if num_targ > 0.6 * ring_buffer.maxlen:
			triggered = True
			for f, s in ring_buffer:
				target_frames.append(f)
			ring_buffer.clear()
	else:
		target_frames.append(file)
		ring_buffer.append((file, is_target))

		num_nottarget = len([f for f, targ in ring_buffer if not targ])
		if num_nottarget > 0.6 * ring_buffer.maxlen:
			triggered = False
			target_segments.append(target_frames)
			ring_buffer.clear()
			target_frames = []
if target_frames: # should this and line below be within the for loop? 
	target_segments.append(target_frames)

with open(gldfile,'w') as outfile:
	for seg in target_segments:
		csv = ','.join([i for i in seg])
		outfile.write(csv + '\n')
