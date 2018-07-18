class InfiniteLoopingTask:
    successful_loops_performed = 0
    loops_performed = 0
    loop_return_values = dict()
    loop_settings = dict()
    initial_settings = dict()
    last_loop_state = dict()
    def __init__(self, *args, **kwargs):
        self.prepare(*args, **kwargs)
        while True:
            self.print_info(*args, **kwargs) # About current loop settings and
                              # previous loop results.
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
