#!/usr/bin/env python3
# playSegs.py  <session path>
# sessions root is dir containing a set of session dirs
# find session with unannotated chucks
# play files in chunks dir for tagging
# input from stdin a label for file after playing
# output to <sess>/chunks.tag

import contextlib
from pydub.utils import db_to_float
from pydub import AudioSegment
from pydub.playback import play
from playsound import playsound
import wave
import time
import operator
import sys
import os
import re
import argparse

parser = argparse.ArgumentParser(description='tag chunk files')
parser.add_argument('ctl')
parser.add_argument('--dur', default='1')
parser.add_argument('--interval', default='1')
args = parser.parse_args()

tags = ['y','n']

def tag_seg():

	while 1:
		print('>', end='', flush=True)
		line = sys.stdin.readline()
		line = line.strip()
		if not line: continue

		if line.startswith('-'):
			break
		elif line.startswith('q'):
			exit(-1)
		else:
			for i in range(len(line)):
				if not line[i] in tags:
					print('unknown code: ',line[i])
					return ''
			break
	return line.lower()


def file_len(fname):
	i = -1
	with open(fname) as f:
		for i, l in enumerate(f):
			pass
	return i + 1

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

def speed_change(sound, speed=1.0):
    # Manually override the frame_rate. This tells the computer how many
    # samples to play per second
    sound_with_altered_frame_rate = sound._spawn(sound.raw_data, overrides={
        "frame_rate": int(sound.frame_rate * speed)
    })

    # convert the sound with altered frame rate to a standard frame rate
    # so that regular playback programs will work right. They often only
    # know how to play audio at standard frame rate (like 44.1k)
    return sound_with_altered_frame_rate.set_frame_rate(sound.frame_rate)

# find first session that isn't done with tagging
for sesspath in open(args.ctl):
	sesspath = sesspath.strip()
	tagfile = os.path.join(sesspath, 'seg.tag')
	segsDir = os.path.join(sesspath, 'segments')

	# get list of segments
	seglist = []
	for file in os.listdir(segsDir):
		if not file.endswith('.wav'): continue
		base = re.sub('.wav', '', file)
		field = base.split('_')
		sg = field[len(field)-1]
		seglist.append( int(sg) )

	# get already tagged files
	count = 0
	if os.path.exists(tagfile):
		count = file_len(tagfile)
		# if all done
		if len(seglist) <= count: continue
	#seglist.sort(key = operator.itemgetter(0, 1))
	seglist.sort()

	tagF = open(tagfile, 'a')
	name = os.path.basename(sesspath)
	
	for s in seglist:
		segwavfile = '%s/%s_%d.wav' % (segsDir,name,s)

		# play alternate samples
		altsamples = ''
		if altsamples:
			# read wav file
			wfi = wave.open(segwavfile, 'rb')
			segaudio = wfi.readframes(wfi.getnframes())
			seg_sh = []
			for i in range(len(segaudio)):
				if (i % 2) == 0: seg_sh.append(segaudio[i])
			segaudio = seg_sh

		# play alternate frames
		altframes = ''
		if altframes:
			# read wav file
			wfi = wave.open(segwavfile, 'rb')
			segaudio = wfi.readframes(wfi.getnframes())

			frames = frame_generator(30, segaudio, 16000)
			frames = list(frames)
			sh_frames = []
			for i in range(len(frames)):
				if (i % 2) == 0: sh_frames.append(frames[i])
			sh_audio = b''.join([f.bytes for f in sh_frames])

			wfo = wave.open('xxtmp', 'wb')
			wfo.setnchannels(1)
			wfo.setsampwidth(2)
			wfo.setframerate(16000)
			wfo.writeframes(sh_audio)
			playsound('xxtmp')


		# play intervals
		intervals = 'y'
		if intervals:
			# set duration and intervals in seconds
			dur = int(args.dur) * 1000
			interval = int(args.interval) * 1000
			segaudio = AudioSegment.from_wav(segwavfile)
			# get length in msec
			seglen = len(segaudio)
			if seglen < (10 * 1000):
				play(segaudio)
			else:
				beg = 0
				while 1:
					end = beg + dur
					if end > seglen: end = seglen
					chunk = segaudio[beg:end]
					#chunk.export('xxtmp', format ="wav")
					play(chunk)
					beg = end + interval
					if beg > seglen: break
			tag = tag_seg()

		tagF.write('%d %s\n' % (s, tag))
	tagF.close()

#play(shaudio)
#fast_sound = speed_change(segaudio, 1.5)
#print('rate:',fast_sound.frame_rate)
#play(fast_sound)
#time.sleep(1.0)

#tag = tag_seg(file)
