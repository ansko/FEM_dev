import multiprocessing
import os
import psutil
import signal
import sys
import time

from settings.settings import Settings


class Watcher:
    check_return_values = {
        'processes_not_found': 0, # tracked tasks are not running, exit
        'killed_MC_exfoliation': 1,
        'killed_gen_mesh.x': 2,
        'killed_processMesh.x': 3,
        'killed_FEManton3.o_x': 4,
        'killed_FEManton3.o_y': 5,
        'killed_FEManton3.o_z': 6,
        'waiting_MC_exfoliation': 7,
        'waiting_gen_mesh.x': 8,
        'waiting_processMesh.x': 9,
        'waiting_FEManton3.o_x': 10,
        'waiting_FEManton3.o_y': 11,
        'waiting_FEManton3.o_z': 12,
    }

    def __init__(self, just_watch=True):
        self.pid = os.getpid()
        self.just_watch = just_watch
        settings = Settings()
        self.tracked_names = settings['time_limits'].keys()
        self.period = settings['period']
        print('started watching, self pid={0}'.format(self.pid),
              ', just_watch={0}'.format(self.just_watch),
              ', period = {0}'.format(self.period))
        print('tracked names', *self.tracked_names)
        while True:
            value = self.check_for_long_processes()
            if value in self.check_return_values.values():
                for k, v in self.check_return_values.items():
                    if v == value:
                        print(k)
                    if k == 'processes_not_found':
                        print('exiting due to the absence of the tracked',
                              'processes')
                        sys.exit()
            else:
                print('error: unknown return code of check_for_long_processes')
                print(value)
                sys.exit()
            time.sleep(self.period)


    def check_for_long_processes(self):
        current_process = None
        pid = None
        running_time = None
        for proc in psutil.process_iter():
            if proc.name() not in self.tracked_names:
                continue
            current_process = proc.name()
            pid = proc.pid
            running_time = int(time.time() - proc.create_time())
        if current_process is None:
            return self.check_return_values['processes_not_found']
        if running_time > limits[current_process]:
            print('killing', current_process, 'with pid', pid,
                'running for', running_time, 'seconds')
            os.kill(pid, signal.SIGKILL)
            return self.check_return_values['killed_' + current_process]
        print('waiting for', current_process, 'with pid', pid,
            'that is running for', running_time, 'of max', limits[current_process])
        return self.check_return_values['waiting_' + current_process]
