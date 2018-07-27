#!/usr/bin/env python3


import os


completed = 0
for dirname in os.listdir():
    if dirname.startswith('InfiniteLoopingCubicTaskCluster'):
        tmp_dir = '/'.join([os.getcwd(), dirname])
        for fname in os.listdir(tmp_dir):
            if fname.startswith('py_main_log'):
                count = len(open('/'.join([tmp_dir, fname]))
                    .read().split('**********')) - 1
                completed += count
                print(dirname.split('_')[-1], count)

print('sum:', completed)
