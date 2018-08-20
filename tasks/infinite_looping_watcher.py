import os
import psutil
import signal
import sys
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
        'killed_FEManton3.o': 4, # x
        'killed_FEManton3.o': 5, # y
        'killed_FEManton3.o': 6, # z
        'waiting_MC_exfoliation': 7,
        'waiting_gen_mesh.x': 8,
        'waiting_processMesh.x': 9,
        'waiting_FEManton3.o_x': 10,
        'waiting_FEManton3.o_y': 11,
        'waiting_FEManton3.o_z': 12,
    }
    last_loop_state = {}

    def prepare(self, *args, **kwargs):
        print('watcher', sys.stdout.name, file=sys.stderr)
        self.pid = os.getpid()
        if 'just_watch' in kwargs.keys():
            self.just_watch = kwargs['just_watch']
        else:
            self.just_watch = True
        settings = Settings()
        self.tracked_names = settings['time_limits'].keys()
        self.limits = settings['time_limits']
        self.period = settings['period']
        print('watcher with pid={0}'.format(self.pid),
            'just_watch={0}'.format(self.just_watch),
            'period={0} sucessfully started at {1}'.format(
                self.period, time.asctime()),
            flush=True)

    def last_loop_state_string(self):
        try:
            for k, v in self.loop_return_values.items():
                if v == self.last_loop_state['return_code']:
                    return k
        except KeyError:
            return 'first loop is being performed now'


    def print_info(self):
        try:
            print(time.asctime(),
                'last_loop_state={0} ({1})'.format(
                self.last_loop_state['return_code'],
                self.last_loop_state_string()),
                flush=True)
        except KeyError:
            print(time.asctime(),
                'first loop of watcher is being performed',
                flush=True)
        return 0


    def set_loop_settings(self, *args, **kwargs):
        pass

    def loop(self):
        time.sleep(self.period)
        for proc in psutil.process_iter():
            if proc.name() not in self.tracked_names:
                continue
            current_process = proc.name()
            pid = proc.pid
            running_time = int(time.time() - proc.create_time())
            cmdline = proc.cmdline()
            self.last_loop_state['last_pid_tracked'] = pid
            self.last_loop_state['last_process_tracked'] = current_process
            self.last_loop_state['last_cmdline_tracked'] = cmdline
            self.last_loop_state['last_running_time_tracked'] = running_time
            break
        try:
            if running_time > self.limits[current_process]:
                print('killing', current_process,
                    'with pid', pid,
                    'running for', running_time, 'seconds',
                    flush=True)
                os.kill(pid, signal.SIGKILL)
                for key in ['last_pid_tracked', 'last_process_tracked',
                    'last_running_time_tracked']:
                        del self.last_loop_state[key]
                return self.loop_return_values['killed_' + current_process]
        except UnboundLocalError:
            return self.loop_return_values['processes_not_found']
        key = 'waiting_' + current_process
        if self.last_loop_state['last_process_tracked'] == 'FEManton3.o':
            axe = self.last_loop_state[
                'last_cmdline_tracked'][1].split('.')[0][-2:]
            if axe == 'XX':
                key += '_x'
            elif axe == 'YY':
                key += '_y'
            elif axe == 'ZZ':
                key += '_z'
        try:
            return self.loop_return_values[key]
        except:
            pass

    def postprocess(self):
        pass
