import os
import pydub
from pydub import AudioSegment
import pandas as pd
import shutil
import re
# split audio into blocks according to .seg files and start offsets

mic_matching_file = os.path.join('configs', 'mic_matching_r3d4g1am.txt')

with open(mic_matching_file) as ctl: # reads lines without empties
	sesslist = (line.rstrip() for line in ctl) 
	sesslist = list([line.split(',') for line in sesslist if line])

for new_sess, ref_sess, offset in sesslist:
	offset=float(offset)
	ref_sesspath = os.path.join('data','sess',ref_sess)
	new_sesspath = os.path.join('data','sess',new_sess)
	ref_blkMap = pd.read_csv(os.path.join(ref_sesspath,f'{ref_sess}.blkmap'), 
		sep='\s+', header=None, names = ['segments','block'])
	ref_segs = pd.read_csv(os.path.join(ref_sesspath,f'{ref_sess}.seg'), 
		sep='\s+', header=None, index_col=False, 
		dtype={0:'int',1:'float',2:'float'},
		names = ['segment','start_s','end_s'])   

	new_segs = ref_segs.copy()
	new_segs['start_s'] = new_segs['start_s'] - offset
	new_segs['end_s'] = new_segs['end_s'] - offset
	new_audio_file = os.path.join(new_sesspath,f'{new_sess}.wav')
	new_audio = AudioSegment.from_file(new_audio_file)
	print(new_audio.duration_seconds)
	print(f'sampling rate: {new_audio.channels}')
	print(f'n channels: {new_audio.frame_rate}')
	# detect if audio properties are as desired (mono 16k), if not we will rewrite the wav
	if (not (new_audio.frame_rate ==16000 and  new_audio.channels==1) ):
		new_audio = new_audio.set_channels(1)
		new_audio = new_audio.set_frame_rate(16000)
		new_audio.export(new_audio_file, format='wav')



	new_segs = pd.DataFrame([r for i,r in new_segs.iterrows() if r['end_s'] < new_audio.duration_seconds 
		and r['start_s'] >= 0.0]).reset_index()
	min_seg = int(new_segs['segment'].iloc[0])
	max_seg =  int(new_segs['segment'].iloc[-1])
	new_blkMap = ref_blkMap.copy()
	new_blkMap['segment_list'] = [[int(j) for j in i.split(',')] for i in new_blkMap['segments']]
	new_blkMap = pd.DataFrame(r for i,r in new_blkMap.iterrows() if min_seg <= min(r['segment_list']) and 
		max_seg >= max(r['segment_list']))
	new_blkMap.drop(columns='segment_list', inplace=True)

	segDir = os.path.join(new_sesspath, 'segments')
	if not os.path.exists(segDir):
		os.makedirs(segDir)
	for s, row in new_segs.iterrows():
		seg = int(row['segment'])
		start_s = row['start_s']*1000
		end_s = row['end_s']*1000


		seg_audio = new_audio[start_s:end_s]

		seg_audio.export(os.path.join(segDir,f'{new_sess}_{seg}.wav'), format='wav')
 
	new_segs.to_csv( os.path.join(new_sesspath, f'{new_sess}.seg'), header=None, index=None, sep=' ')
	new_blkMap.to_csv( os.path.join(new_sesspath, f'{new_sess}.blkmap'), header=None, index=None, sep=' ')

	# Copy and rename transcrpipt files 
	ref_transcriptDir = os.path.join(ref_sesspath,  'transcripts')
	new_transcriptDir = os.path.join(new_sesspath,  'transcripts')

	if not os.path.exists(ref_transcriptDir):
		print(f'No transcripts for reference mic')
		continue
	else: 
	# loop over transcript files
		tlist = [f for f in os.listdir(ref_transcriptDir) if f.endswith('.txt') and not f.endswith('_diarized.txt')]        
		print(f'will copy {len(tlist)} reference transcripts to new session directory for the comparison mic')
	if not os.path.exists(new_transcriptDir):
		os.makedirs(new_transcriptDir)

	for t in tlist:   
		base = re.sub('.txt', '', t)
		field = base.split('_')
		ix = field[len(field)-1]

		shutil.copyfile(os.path.join(ref_transcriptDir, t), os.path.join(new_transcriptDir, f'{new_sess}_{ix}.txt'))
 