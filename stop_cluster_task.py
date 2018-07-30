#!/usr/bin/env python3


"""
This tool should completely stop main_remote:
    - kill all local py scripts and fem exe-s
    - kill all cluster tasks listed in squeue by scancel
No additional results are saved, only those that are already in logs
are kept.

Remote architecture:
main -> (forker -> cluster_task) xN
So killing order is:
    - local kill
        - fokers
        - cluster_tasks
    - remote kill


Something good:
    - local task may be running and it will not be terminated.
"""


import os
import paramiko
import pprint
import psutil

pprint=pprint.PrettyPrinter(indent=4).pprint

from settings.cluster_settings_kiae_me import ClusterSettingsKiaeMe


fem_exes_names = [
    'MC_exfoliation', 'mixed',
    'gen_mesh.x',
    'processMesh.x',
    'FEManton3.o', 'FEManton2.o'
]
cluster_dir_start = 'InfiniteLoopingCubicTaskCluster'


def local_kill():
    # Some local task may be running simultaneously with remote, should keep it
    local_task_related = []
    for proc in psutil.process_iter():
        if proc.name() == 'python3':
            if 'local' in proc.cmdline()[1]:
                local_task_related.append(proc.pid)
    my_pid = os.getpid()
    cwd = os.getcwd()
    forkers = []
    cluster_tasks = []
    # Create lists of forkers' and cluster_tasks' pids.
    for proc in psutil.process_iter():
        if proc.name() == 'python3' and proc.pid != my_pid:
            #  Ignore everuthing related to the running 'main_local_*.py'
            if proc.pid in local_task_related or proc.ppid in local_task_related:
                continue
            if proc.cwd() == cwd:
                forkers.append(proc.pid)
            elif proc.cwd().split('/')[-1].startswith(cluster_dir_start):
                cluster_tasks.append(proc.pid)
            else:
                print(proc.pid, proc.cmdline(), proc.cwd()) # Should not happen
    for pid in forkers:
        print('terminating forker with pid', pid)
        psutil.Process(pid).terminate()
    for pid in cluster_tasks:
        print('terminating cluster task with pid', pid)
        psutil.Process(pid).terminate()
    return 0


def remote_kill():
    """
    squeue --user=antonsk - get my tasks
    scancel task1 task2 ... - kill all tasks by their id

    """
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(
        ClusterSettingsKiaeMe().host,
        username=ClusterSettingsKiaeMe().user,
        password=ClusterSettingsKiaeMe().pwd,
        key_filename=ClusterSettingsKiaeMe().key
    )
    stdin, stdout, stderr = ssh.exec_command('squeue --user=antonsk')
    out_lines = stdout.readlines()[1:]
    task_numbers = [int(line.split()[0]) for line in out_lines]
    task_names = [line.split()[2] for line in out_lines]
    if (len(task_numbers) != len(task_names)):
        print(task_numbers, task_names)
    for idx in range(min(len(task_numbers), len(task_names))):
        print('remote stop', task_names[idx])
        stdin, stdout, stderr = ssh.exec_command('scancel {0}'.format(
            task_numbers[idx]))
    return 0


def main():
    local_kill()
    remote_kill()
    return 0


if __name__ == '__main__':
    main()
