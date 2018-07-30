#!/usr/bin/env python3


"""
Calculates number of log entries in every InfiniteLoopingCubicTaskCluster*
folder.
This just helps to monitor progress of the cluster task.
"""


import json
import os


completed = 0
for dirname in os.listdir():
    if dirname.startswith('InfiniteLoopingCubicTaskCluster'):
        tmp_dir = '/'.join([os.getcwd(), dirname])
        for fname in os.listdir(tmp_dir):
            if fname.startswith('py_main_log'):
                count = len(json.load(open('/'.join([tmp_dir, fname]))))
                completed += count
                print(dirname.split('_')[-1], count)
print('sum:', completed)
