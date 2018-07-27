import os
import sys
import time


class InfiniteLoopingTask:

    successful_loops_performed = 0
    loops_performed = 0

    def __init__(self, *args, **kwargs):
        stdout_fname = 'tmp/{0}_{1}.out'.format(
            self.__class__.__name__, str(int(time.time())))
        sys.stdout = open(stdout_fname, 'w')
        self.prepare(*args, **kwargs)
        while True:
            self.print_info(*args, **kwargs)
            self.last_loop_state = dict()
            self.set_loop_settings(*args, **kwargs)
            if self.loops_performed == 0:
                self.last_loop_state['return_code'] = self.loop(*args, **kwargs)
            else:
                self.last_loop_state['return_code'] = self.loop()
            if self.last_loop_state['return_code'] == 0:
                self.successful_loops_performed += 1
            self.loops_performed += 1
            self.postprocess(*args, **kwargs)
