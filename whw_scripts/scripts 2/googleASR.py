#!/usr/bin/env python3
# googleASR.py  <ctl file>
# send files to google cloud text-to-speech
# export GOOGLE_APPLICATION_CREDENTIALS=<path to credentials>


from google.cloud import speech
import io
import os
import re
import argparse

parser = argparse.ArgumentParser(description='run google_recognizer')
parser.add_argument('ctl')
args = parser.parse_args()

def transcribe_file(speech_file):
	"""Transcribe the given audio file."""
	client = speech.SpeechClient()

	# read audio file
	with io.open(speech_file, "rb") as audio_file:
		content = audio_file.read()

	# specify parms and content for transcribe request
	audio = speech.RecognitionAudio(content=content)
	config = speech.RecognitionConfig(
		encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
		sample_rate_hertz=16000,
		language_code="en-US",
		model="video",
	)

	# transcribe
	response = client.recognize(config=config, audio=audio)

	# Each result is for a consecutive portion of the audio. Iterate through
	# them to get the transcripts for the entire audio file.
	trans = ''
	for result in response.results:
		# The first alternative is the most likely one for this portion.
		#print(u"Transcript: {}".format(result.alternatives[0].transcript))
		trans += result.alternatives[0].transcript
	trans = re.sub(' $','\n',trans)
	print(os.path.basename(speech_file),  trans)
	filename = re.sub('.wav','.asr',os.path.basename(speech_file))
	with open(os.path.join(asrDir,filename),'w') as outfile:
		outfile.write(trans)



# ctl has list of paths to sessions to process
# recognize each segment separately
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
	asrDir = os.path.join(sesspath,'asr')
	if not os.path.exists(asrDir):
		os.makedirs(asrDir)
	
	for b in seglist:
		segwavfile = '%s/%s_%d.wav' % (segsDir,name,b)

		fbytes = os.stat(segwavfile).st_size -44
		nsec = float(fbytes)/32000.0
		if nsec > 61.0: continue
		print('transcribe',b)

		transcribe_file(segwavfile)
