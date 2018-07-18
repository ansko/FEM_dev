import os
import psutil
import time

from settings.settings import Settings
from tasks.infinite_looping_task import  InfiniteLoopingTask


class InfiniteLoopingWatcher(InfiniteLoopingTask):
    loop_return_values = {
        'first_loop_not_performed': None,
        'processes_not_found': 0,
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

    def prepare(self, *args, **kwargs):
        self.pid = os.getpid()
        if 'just_watch' in kwargs.keys():
            self.just_watch = kwargs['just_watch']
        else:
            self.just_watch = True
        settings = Settings()
        self.tracked_names = settings['time_limits'].keys()
        self.period = settings['period']

    def print_info(self):
        print('watcher with pid={0}'.format(self.pid),
              'just_watch={0}'.format(self.just_watch),
              'period={0}'.format(self.period),
              'last_loop_state={0} ({1})'.format(self.last_loop_state,
                  {v: k for k, v in self.loop_return_values.items()}
                      [self.last_loop_state]))

    def set_loop_settings(self, args, kwargs):
        pass

    def loop(self):
        time.sleep(self.period)
        for proc in psutil.process_iter():
            if proc.name() not in self.tracked_names:
                continue
            current_process = proc.name()
            pid = proc.pid
            running_time = int(time.time() - proc.create_time())
            break
        try:
            if running_time > limits[current_process]:
                print('killing', current_process,
                    'with pid', pid,
                    'running for', running_time, 'seconds')
                os.kill(pid, signal.SIGKILL)
                return self.loop_return_values['killed_' + current_process]
            print('waiting for', current_process, 'with pid', pid,
                'that is running for', running_time, 'of max',
                 limits[current_process])
        except UnboundLocalError:
            return self.loop_return_values['processes_not_found']
        return self.loop_return_values['waiting_' + current_process]

    def postprocess(self):
        pass
