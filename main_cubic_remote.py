import multiprocessing
import os
import sys
import time


start_step_values_available = set([
    'prepare_cluster', 'run_cpp', 'process_cpp_log', 'create_fem_input',
    'copy_files_to_cluster', 'fem_gen', 'wait_fem_gen', 'fem_process',
    'wait_fem_process', 'fem_main_xx', 'wait_fem_main_xx', 'fem_main_yy',
    'wait_fem_main_yy', 'fem_main_zz', 'wait_fem_main_zz',
    'get_files_from_cluster', 'get_moduli', 'log_iteration'
])


##############################

simultaneous_tasks_number = 15

##############################


def forker():
    from tasks.infinite_looping_cubic_task_cluster import (
        InfiniteLoopingCubicTaskCluster
    )
    if os.fork() != 0:
        return
    multiprocessing.Process(target=lambda : 
        InfiniteLoopingCubicTaskCluster(
            task_name=task_name, start_step=start_step
        )
    ).start()

if __name__ == '__main__':
    task_name='mc_cluster'
    start_step=None

    if len(sys.argv) > 1 and sys.argv[1] in start_step_values_available:
        task_name='cluster_mc'
        start_step=sys.argv[1]
    elif len(sys.argv) == 1:
        task_name='cluster_mc'
        start_step=None
    elif len(sys.argv) < 2:
        print('no start step sepcified')
    elif sys.argv[1] not in start_step_values_available:
        print('unknown start step:', sys.argv[1])
    try:
        os.mkdir('tmp')
    except FileExistsError:
        pass
    processes = []
    for task_number in range(simultaneous_tasks_number):
        processes.append(multiprocessing.Process(target=forker))
        processes[-1].start()
        processes[-1].join()
        time.sleep(3)
    print(len(processes), 'run')
