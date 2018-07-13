#!/usr/bin/env python3


import datetime
import multiprocessing
import os
import pprint
pprint=pprint.PrettyPrinter(indent=4).pprint
import psutil
import shutil
import signal
import sys
import time

from utils.cubic_task import CubicTask


def long_task(**kwargs):
    print('starting long task')
    time.sleep(3)
    print('finished long task')
    return 0


class ProcessesManager:
    processes = []

    def run_process(self, task, *args, **kwargs):
        p = multiprocessing.Process(target=task, args=args, kwargs=kwargs)
        p.start()
        self.processes.append(p)

    def perform_action_on_process(self, action, *args, **kwargs):
        actions = {
            'kill': os.kill, #os.kill(pid, signal.SIGKILL)
        }
        process_methods = {
            'join': process.join,
            'terminate': process.termintate
        }

    def intercept_fem_task(self, **kwargs):
        def kill_py_task(py_task):
            if py_task is None:
                print('py task has been killed earlier')
                return 0
            os.kill(py_task['pid'], signal.SIGKILL)
            print('py script killed')
            return 0

        def wait_fem_task(fem_task):
            print('waiting for', fem_task['name'], 'to complete')
            while fem_task['pid'] in [proc.pid for proc in psutil.process_iter()]:
                pass
            print(fem_task['name'], 'completed')
            return 0

        def save_main_log(py_task, logs_dir):
            if py_task is None:
                print('nothing to save, py task has been killed earlier')
                return 0
            year_month4_date = datetime.datetime.fromtimestamp(
                py_task['create_time']).strftime("%Y_%B_%d")
            year_month3_date = '_'.join([year_month4_date.split('_')[0],
                year_month4_date.split('_')[1][0:3],
                year_month4_date.split('_')[2]])
            possible_log_name = 'py_main_log_' + year_month3_date
            destination_log_name = possible_log_name
            if destination_log_name in os.listdir(logs_dir):
                log_num_same_date = 0
                tmp = '_'.join([destination_log_name, ''.join(
                    ['n', str(log_num_same_date)])])
                while tmp in os.listdir(logs_dir):
                        log_num_same_date += 1
                        tmp = '_'.join([destination_log_name, ''.join(
                             ['n', str(log_num_same_date)])])
                destination_log_name = tmp
            if possible_log_name in os.listdir(py_task['wd']):
                shutil.copyfile('/'.join([py_task['wd'], possible_log_name]),
                    '/'.join([logs_dir, destination_log_name]))
            print('log saved as', destination_log_name)
            return 0

        def get_tasks_info():
            fem_task = dict()
            py_task = dict()
            for proc in psutil.process_iter():
                if proc.name() in kwargs['tracked_names']:
                    fem_task = {
                        'name': proc.name(),
                        'pid': proc.pid,
                        'create_time': proc.create_time(),
                        'wd': proc.cwd(),
                        'cmdline': proc.cmdline()
                    }
                    if proc.ppid() == 1: # py script has been killed earlier
                        return fem_task, None
                    py_task = {
                        'name': proc.parent().name(),
                        'pid': proc.parent().pid,
                        'create_time': proc.parent().create_time(),
                        'wd': proc.parent().cwd(),
                        'cmdline': proc.parent().cmdline()
                    }
                    return fem_task, py_task

        print('started intercepting fem task')
        try:
            fem_task, py_task = get_tasks_info()
        except TypeError: # got None during 'fem_task, py_task = get_tasks_info()'
            print('nothing is running')
            return 0
        kill_py_task(py_task)
        wait_fem_task(fem_task)
        try:
            save_main_log(py_task, kwargs['logs_dir'])
        except KeyError:
            print('not enouth arguments')
            return 0
        print('task has been completely removed from other')
        return 0


def main():
    logs_dir = '/home/anton/AspALL/Projects/FEM_RELEASE_BACKUP/logs_dev'
    tracked_names = ['gen_mesh.x', 'processMesh.x', 'FEManton3.o']

    a = ProcessesManager()
    a.intercept_fem_task(cpp_task_name='mc', logs_dir=logs_dir,
        tracked_names=tracked_names)

    return 0


if __name__ == '__main__':
    main()
