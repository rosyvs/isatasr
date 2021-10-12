#!/usr/bin/env python3
# asrBlks.py  <ctl file of session paths>

import speech_recognition as sr
import os
import re
import argparse

parser = argparse.ArgumentParser(description='run google_recognizer')
parser.add_argument('ctl')
args = parser.parse_args()


# ctl has list of paths to sessions to process
for sesspath in open(args.ctl):
	sesspath = sesspath.strip()
	tagfile = os.path.join(sesspath, 'seg.tag')
	blksDir = os.path.join(sesspath, 'blocks')

	# get list of blocks
	blklist = []
	for file in os.listdir(blksDir):
		if not file.endswith('.wav'): continue
		base = re.sub('.wav', '', file)
		field = base.split('_')
		sg = field[len(field)-1]
		blklist.append( int(sg) )
	blklist.sort()

	name = os.path.basename(sesspath)

	asrDir = os.path.join(sesspath,'asr')
	if not os.path.exists(asrDir):
		os.makedirs(asrDir)
	
	for b in blklist:
		blkwavfile = '%s/%s_%d.wav' % (blksDir,name,b)

		# Initialize the recognizer
		r = sr.Recognizer()
 
		# Traverse the audio file and listen to the audio
		with sr.AudioFile(blkwavfile) as source:
			audio_listened = r.listen(source)
 
		# Try to recognize the listened audio
		# And catch expections.
		try:    
			rec = r.recognize_google(audio_listened)
 
			print('%s_%d' % (name,b), rec)
			asrfile = os.path.join(asrDir,'%s_%d.asr' % \
				(name,b))
			with open(asrfile,'w') as outfile:
				outfile.write(rec + '\n')
			#fh.write(rec+" ")
 
		# If google could not understand the audio
		except sr.UnknownValueError:
			print("Could not understand audio")
 
		# If the results cannot be requested from Google.
		# Probably an internet connection error.
		except sr.RequestError as e:
			print("Could not request results.")
