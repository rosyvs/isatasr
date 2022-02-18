# quick script to get mwtrics on groups
import csv
from collections import Counter

groupFile = '../deepSampleGroups.csv'
with open(groupFile,encoding='utf-8-sig') as in_file:
    reader = csv.reader(in_file, delimiter=",")

    groups=[tuple(g[0].split('\n')) for g in reader]   
    counts = Counter(groups)
    print(f'number of strictly unique groups: {len(counts)}')

    # TODO allow for absences - set containmnet = same group