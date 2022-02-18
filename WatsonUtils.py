import json
import requests
import csv

"""
#     parser.add_argument('filepath',
#                         help='Path to audio file to transcribe')
#     parser.add_argument('-c', '--config',
#                         help='Path to config file with IBM Watson STT Credentials',
#                         default='example.config')
#     parser.add_argument('-o', '--output',
#                         help='Path where output JSON file should be written',
#                         default='output.json')
#     parser.add_argument('-s', '--speakerlabels',
#                         help='Use if Watson should attempt to disambiguate speakers',
#                         action="store_true")
#     parser.add_argument('audiotype',
#                         help='Type of audio file (wav or flac)')
"""


def WatsonASR_bytes(bytes, config, audiotype):
    with open(config, 'r') as f:
        config_info = json.load(f)
        config_url = config_info['url']
        username = config_info['username']
        password = config_info['password']
    url = config_url + '/v1/recognize'

    # Sidney said to get all the info we can as we only want to run these once.
    params = {'timestamps': True,
                'inactivity_timeout': -1,
                'max_alternatives': 10,
                'word_alternatives_threshold': 0.01,
                'word_confidence': True,
                'speech_detector_sensitivity': 1 # will use other VAD so no need to use theirs
            }
    r = requests.post(url=url,
                        auth=(username, password),
                        headers={'Content-Type': 'audio/' + audiotype},
                        data=bytes,
                        params=params)
    print(r)
    if r.status_code != 200:
        print("returned a bad response.")
        print(r)
        return None

        # json_response = json.loads(r.text)
        # if 'results' in json_response:
        #     print("Success.")
        #     outfile.write(r.text)
        # else:
        #     print("failed to process.")
        #     print("Json Error Message: ", json_response)

    return r

def JSONtoCSV(jsonpath, csvpath):
    """Converts JSON output file from IBM Watson STT to CSV"""
    with open(jsonpath, 'r') as jsonfile:
        output = json.load(jsonfile)
    with open(csvpath, 'w') as csvfile:
        # Create writer object
        csvwriter = csv.writer(csvfile, delimiter='\t')
        csvwriter.writerow(['start_time', 'end_time', 'transcript', 'confidence'])
        for result in output['results']:
            # Alternatives is a list of alternative transcripts, the first
            #   transcript has the highest confidence (and timestamps)
            # If there are no timestamps, then it seems there was no word in the
            #   utterance with confidence greater than 0.0. Not sure why these are
            #   returned, but I'm skipping them rather than writing them so that
            #   we don't have missing data in the CSV file (and because they don't
            #   seem like meaningful words anyway).
            if len(result['alternatives'][0]['timestamps']) == 0:
                continue
            # Timestamps is a list of words with timestamps, 0 gets first word,
            #   -1 gets last word
            # Each timestamp is a list, format: ['word', start_time, end_time]
            start_time = result['alternatives'][0]['timestamps'][0][1]
            end_time = result['alternatives'][0]['timestamps'][-1][2]
            confidence = result['alternatives'][0]['confidence']
            transcript = result['alternatives'][0]['transcript']
            csvwriter.writerow([start_time, end_time, transcript, confidence])