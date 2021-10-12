#!/usr/bin/env python3
# asr.py  <session path>

from pydub.utils import db_to_float
from pydub import AudioSegment
import speech_recognition as sr
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



# ctl has list of paths to sessions to process
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
	seglist.sort()

	name = os.path.basename(sesspath)
	
	#for s in seglist:
	for s in range(0,1):
		segwavfile = '%s/%s_%d.wav' % (segsDir,name,s)

#		config = types.RecognitionConfig(
#			encoding=enums.RecognitionConfig.AudioEncoding.LINEAR16,
#			language_code='en-US',
#			speech_contexts=[speech.types.SpeechContext(
#			phrases=['health'])]
#		)

		# Initialize the recognizer
		r = sr.Recognizer()
 
		# Traverse the audio file and listen to the audio
		with sr.AudioFile(segwavfile) as source:
			audio_listened = r.listen(source)
 
		# Try to recognize the listened audio
		# And catch expections.
		try:    
			rec = r.recognize_google(audio_listened)
 
			# If recognized, write into the file.
			print(rec)
			#fh.write(rec+" ")
 
		# If google could not understand the audio
		except sr.UnknownValueError:
			print("Could not understand audio")
 
		# If the results cannot be requested from Google.
		# Probably an internet connection error.
		except sr.RequestError as e:
			print("Could not request results.")
