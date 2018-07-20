import sys


from tasks.infinite_looping_cubic_task_cluster import (
    InfiniteLoopingCubicTaskCluster
)


start_step_values_available = set([
    'prepare_cluster', 'run_cpp', 'process_cpp_log', 'create_fem_input',
    'copy_files_to_cluster', 'fem_gen', 'wait_fem_gen', 'fem_process',
    'wait_fem_process', 'fem_main_xx', 'wait_fem_main_xx', 'fem_main_yy',
    'wait_fem_main_yy', 'fem_main_zz', 'wait_fem_main_zz',
    'get_files_from_cluster', 'get_moduli', 'log_iteration'
])


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] in start_step_values_available:
        print('ok, starting from', sys.argv[1])
        InfiniteLoopingCubicTaskCluster(
            task_name='cluster_mc',
            start_step=sys.argv[1]
        )
    elif len(sys.argv) == 1:
        print('ok, starting from the beginning')
        InfiniteLoopingCubicTaskCluster(
            task_name='cluster_mc',
            start_step=None
        )
    elif len(sys.argv) < 2:
        print('no start step sepcified')
    elif sys.argv[1] not in start_step_values_available:
        print('unknown start step:', sys.argv[1])
    sys.exit()
