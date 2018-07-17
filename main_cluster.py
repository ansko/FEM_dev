from tasks.infinite_looping_cubic_task_cluster import (
    InfiniteLoopingCubicTaskCluster
)


if __name__ == '__main__':
    InfiniteLoopingCubicTaskCluster(
        task_name='cluster_mc',
        start_step='wait_fem_gen'
    )


# start steps name for the task:
#        'prepare_cluster', 'run_cpp', 'process_cpp_log', 'create_fem_input',
#        'copy_files_to_cluster', 'fem_gen', 'wait_fem_gen', 'fem_process',
#        'wait_fem_process', 'fem_main_xx', 'wait_fem_main_xx', 'fem_main_yy',
#        'wait_fem_main_yy', 'fem_main_zz', 'wait_fem_main_zz',
#        'get_files_from_cluster', 'get_moduli', 'log_iteration'
