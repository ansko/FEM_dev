#!/usr/bin/env python3


import paramiko
import pprint
import psutil

pprint=pprint.PrettyPrinter(indent=4).pprint

from settings.cluster_settings_kiae_me import ClusterSettingsKiaeMe



def local_kill():
    for proc in psutil.process_iter():
        if proc.name() in ['python3', 'MC_exfoliation', 'gen_mesh.x',
            'processMesh.x', 'FEManton3.o', 'FEManton2.o'] and proc.ppid() == 1:
                print('local stop', proc.name())
                psutil.Process(proc.pid).terminate()
    return 0

def remote_kill():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(
        ClusterSettingsKiaeMe().host,
        username=ClusterSettingsKiaeMe().user,
        password=ClusterSettingsKiaeMe().pwd,
        key_filename=ClusterSettingsKiaeMe().key
    )
    stdin, stdout, stderr = ssh.exec_command('squeue --user=antonsk')
    task_numbers = [int(line.split()[0]) for line in stdout.readlines()[1:]]
    task_names = [int(line.split()[1]) for line in stdout.readlines()[1:]]
    for idx, task_number in enumerate(task_numbers):
        print('remote stop', task_names[idx])
        stdin, stdout, stderr = ssh.exec_command('scancel {0}'.format(task_number))
    return 0

def main():
    local_kill()
    remote_kill()
    return 0


if __name__ == '__main__':
    main()
