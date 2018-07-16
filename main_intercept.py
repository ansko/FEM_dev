from tasks.process_manager import ProcessesManager


if __name__ == '__main__':
    ProcessesManager().intercept_fem_task(
        cpp_task_name='mc',
        logs_dir='/home/anton/AspALL/Projects/FEM_RELEASE_BACKUP/logs_dev',
        tracked_names=['gen_mesh.x', 'processMesh.x', 'FEManton3.o'],
        task_name='mc')
