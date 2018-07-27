import math
import os
import paramiko
import pprint
pprint=pprint.PrettyPrinter(indent=4).pprint
import random
import resource
import shutil
import sys
import subprocess
import time

from settings.settings import Settings
from settings.cluster_settings_kiae_me import ClusterSettingsKiaeMe
from tasks.infinite_looping_task import  InfiniteLoopingTask
from utils.moduli_getter import ModuliGetter


############################


############################

class InfiniteLoopingCubicTaskCluster(InfiniteLoopingTask):
    loop_return_values = {
        'ok': 0,
        'bad_task_wd': 1, # task_wd for some reason != remote_working_directory
        'stderr_not_empty': 2, # cluster stderr is not empty
        'exception_caugth': 3, # caught any exception while running task
        'err_not_empty': 4, # task_id.err is not empty
    }
    cluster_white_list = [
        'libs',
        'gen_mesh.x', 'processMesh.x', 'FEManton3.o',
            'materials.txt', 'matrices.txt',
        'tensor.cpp', 'tensor.h',
       '1.geo'
    ]
    files_to_remove = set([
        'input_XX.txt', 'input_YY.txt', 'input_ZZ.txt',
        'test_elas_EXX_results.txt', 'test_elas_EYY_results.txt',
        'test_elas_EZZ_results.txt',
    ])
    steps = [
        'prepare_cluster', 'run_cpp', 'process_cpp_log', 'create_fem_input',
        'copy_files_to_cluster', 'fem_gen', 'wait_fem_gen', 'fem_process',
        'wait_fem_process', 'fem_main_xx', 'wait_fem_main_xx', 'fem_main_yy',
        'wait_fem_main_yy', 'fem_main_zz', 'wait_fem_main_zz',
        'get_files_from_cluster', 'get_moduli', 'log_iteration'
    ]
    print('my pid is', os.getpid(), file=sys.stderr)

    time_str = str(int(time.time()))

    local_working_directory = os.getcwd() + '/'
    remote_parent_directory = '/s/ls2/users/antonsk/'
    remote_wd_short = '{0}_{1}/'.format(os.getcwd().split('/')[-1], time_str)
    remote_working_directory = remote_parent_directory + remote_wd_short
    remote_storage_directory = remote_parent_directory + 'FEM/'

    initial_settings = dict()

    def prepare(self, *args, **kwargs):
        def prepare_local():
            settings = Settings()
            for key in ('ars', 'cpp_polygons_executables', 'L_div_outer_r',
                'disk_thickness', 'vertices_number', 'mixing_steps',
                'max_attempts', 'cpp_settings_fname', 'required_settings',
                'cpp_directory', 'moduli', 'FEMFolder', 'memory',
                'limitation_memory_ratio', 'taus', 'disk_thickness'):
                    self.initial_settings[key] = settings[key]
            wd = '_'.join([self.__class__.__name__, self.remote_wd_short])
            if 'working_directory' in kwargs.keys():
                wd = kwargs['working_directory']
            self.initial_settings['working_directory'] = wd
            self.wd = wd + '/'
            if wd not in os.listdir():
                os.mkdir(wd)
            os.chdir(wd)
            self.initial_settings['task_name'] = kwargs['task_name']
            asc_time = time.asctime().split()
            self.year_month_day = '_'.join([asc_time[4], asc_time[1], asc_time[2]])
            self.py_main_log = 'py_main_log_' + self.year_month_day
            for dirname in ['logs', 'geo', 'files']:
                if dirname not in os.listdir():
                    os.mkdir(dirname)
            self.ssh = paramiko.SSHClient()
            self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            self.ssh.connect(
                ClusterSettingsKiaeMe().host,
                username=ClusterSettingsKiaeMe().user,
                password=ClusterSettingsKiaeMe().pwd,
                key_filename=ClusterSettingsKiaeMe().key
            )
        def prepare_cluster():
            def exception_handler():
                print('caught exception, bye!, pid = {0}, time = {1}'.format(
                        os.getpid(), self.time_str),
                    file=sys.stderr)
                parts = sys.stdout.name.split('/')[1].split('.')[0].split('_')
                shutil.rmtree(self.local_working_directory +
                    '_'.join([parts[0], 'FEM', parts[1]]))
                os.remove(self.local_working_directory +
                sys.stdout.name)
                sys.exit()

            sftp = self.ssh.open_sftp()
            if self.remote_wd_short not in sftp.listdir(
                self.remote_parent_directory):
                    self.ssh.exec_command('cd {0}'.format(
                        self.remote_parent_directory))
                    sftp.mkdir(self.remote_working_directory)
                    for fname in ['gen_mesh.x', 'processMesh.x', 'FEManton3.o',
                        'materials.txt', 'matrices.txt', 'tensor.cpp', 'tensor.h']:
                            path_from = self.remote_storage_directory + fname
                            path_to = self.remote_working_directory + fname
                            try:
                                stdin, stdout, stderr = self.ssh.exec_command(
                                    'cp {0} {1}'.format(path_from, path_to)
                                )
                            except:
                                exception_handler()
                    try:
                        stdin, stdout, stderr = self.ssh.exec_command(
                            'cd {0}; chmod u+x FEManton3.o'.format(
                                self.remote_working_directory)
                        )
                        stdin, stdout, stderr = self.ssh.exec_command(
                            'du -sh {0}/libs'.format(
                                self.remote_storage_directory))
                        initial_libs_size = stdout.readlines()[0].split('\t')[0]
                        self.ssh.exec_command('cp -R {0}/libs {1}/libs'.format(
                            self.remote_storage_directory,
                            self.remote_working_directory)
                        )
                    except:
                        exception_handler()
                    while True: # waiting  until copying is finishes
                        try:
                            stdin, stdout, stderr = self.ssh.exec_command(
                                'du -sh {0}/libs'.format(
                                    self.remote_working_directory))
                            err_lines = stderr.readlines()
                            out_lines = stdout.readlines()
                            if out_lines:
                                libs_folder_size = out_lines[0].split('\t')[0]
                                if libs_folder_size == initial_libs_size:
                                    break
                        except Exception as e:
                            exception_handler()
            self.cluster_home_dir = '/hfs/head2-hfs2/users/antonsk/'
            shebang = '#!/bin/sh'
            chdir = '#SBATCH -D {0}'.format(self.remote_working_directory)
            nodes = '#SBATCH -n 1'
            cpus_8 = '#SBATCH --cpus-per-task 8'
            cpus_1 = '#SBATCH --cpus-per-task 1'
            stdout_line = '#SBATCH -o %j.out'
            stderr_line = '#SBATCH -e %j.err'
            time_limit_max = '#SBATCH -t 71:59:59'
            time_limit_small = '#SBATCH -t 5:59:59'
            queue = '#SBATCH -p hpc2-16g-3d'
            source = '. /usr/share/Modules/init/sh'
            module = 'module load mpi intel-compilers gcc49'
            mpi_run_gen_mesh = ' | '.join([
                '$MPIRUN {0}gen_mesh.x 1.geo 0.15 2 2'.format(
                    self.remote_working_directory),
                'tee {0}mytask.log."$SLURM_JOBID"'.format(
                    self.remote_working_directory)
            ])
            mpi_run_process_mesh = ' | '.join([
                '$MPIRUN {0}processMesh.x'.format(
                    self.remote_working_directory),
                'tee {0}mytask.log."$SLURM_JOBID"'.format(
                    self.remote_working_directory)
            ])
            mpi_run_fem_main_xx = ' | '.join([
                '$MPIRUN {0}FEManton3.o {1}'.format(
                    self.remote_working_directory,
                    'input_XX.txt'),
                'tee {0}mytask.log."$SLURM_JOBID"'.format(
                    self.remote_working_directory)
            ])
            mpi_run_fem_main_yy = ' | '.join([
                '$MPIRUN {0}FEManton3.o {1}'.format(
                    self.remote_working_directory,
                    'input_YY.txt'),
                'tee {0}mytask.log."$SLURM_JOBID"'.format(
                    self.remote_working_directory)
            ])
            mpi_run_fem_main_zz = ' | '.join([
                '$MPIRUN {0}FEManton3.o {1}'.format(
                    self.remote_working_directory,
                    'input_ZZ.txt'),
                'tee {0}mytask.log."$SLURM_JOBID"'.format(
                    self.remote_working_directory)
            ])
            fem_gen_sh = '\n'.join([shebang, chdir, nodes, cpus_8, stdout_line,
                stderr_line, time_limit_max, queue, source, module,
                mpi_run_gen_mesh])
            fem_process_sh = '\n'.join([shebang, chdir, nodes, cpus_1, stdout_line,
                stderr_line, time_limit_small, queue, source, module,
                mpi_run_process_mesh])
            fem_main_sh_xx = '\n'.join([shebang, chdir, nodes, cpus_8, stdout_line,
                stderr_line, time_limit_max, queue, source, module,
                mpi_run_fem_main_xx])
            fem_main_sh_yy = '\n'.join([shebang, chdir, nodes, cpus_8, stdout_line,
                stderr_line, time_limit_max, queue, source, module,
                mpi_run_fem_main_yy])
            fem_main_sh_zz = '\n'.join([shebang, chdir, nodes, cpus_8, stdout_line,
                stderr_line, time_limit_max, queue, source, module,
                mpi_run_fem_main_zz])
            if self.remote_working_directory.endswith('/'):
                dir_name = self.remote_working_directory.split('/')[-2]
            else:
                dir_name = self.remote_working_directory.split('/')[-1]
            self.fem_gen_file_name = dir_name + '_fem_gen.sh'
            self.fem_process_file_name = dir_name + '_fem_process.sh'
            self.fem_main_xx_file_name = dir_name + '_fem_3_anton_xx.sh'
            self.fem_main_yy_file_name = dir_name + '_fem_3_anton_yy.sh'
            self.fem_main_zz_file_name = dir_name + '_fem_3_anton_zz.sh'
            with open(self.fem_gen_file_name, 'w') as f:
                f.write(fem_gen_sh)
            with open(self.fem_process_file_name, 'w') as f:
                f.write(fem_process_sh)
            with open(self.fem_main_xx_file_name, 'w') as f:
                f.write(fem_main_sh_xx)
            with open(self.fem_main_yy_file_name, 'w') as f:
                f.write(fem_main_sh_yy)
            with open(self.fem_main_zz_file_name, 'w') as f:
                f.write(fem_main_sh_zz)
            for cluster_runner_sh in [self.fem_gen_file_name,
                self.fem_process_file_name, self.fem_main_xx_file_name,
                self.fem_main_yy_file_name, self.fem_main_zz_file_name]:
                    sftp.put(
                        self.local_working_directory + self.wd +
                            cluster_runner_sh,
                        self.cluster_home_dir + cluster_runner_sh
                    )
            sftp.close()
        prepare_local()
        prepare_cluster()
        self.initial_settings['ars'] = [50] # !!!


    def print_info(self, *args, **kwargs):
        print('*** cluster ***', time.asctime(), flush=True)
        print('loops={0}/{1}'.format(
            self.successful_loops_performed, self.loops_performed),
            flush=True)

    def set_loop_settings(self, *args, **kwargs):
        self.loop_settings = dict()
        self.last_loop_state = dict()
        self.last_loop_state['seconds'] = str(int(time.time()))
        self.loop_settings['tau'] = random.choice(self.initial_settings['taus'])
        self.loop_settings['ar'] = random.choice(self.initial_settings['ars'])
        ar = self.loop_settings['ar']
        Nmax = int(500 * ar / math.pi * 0.05)
        Nmax = min(100, Nmax)
        self.loop_settings['fi_max_possible'] = math.pi / 500 * Nmax / ar
        self.loop_settings['N'] = random.choice(range(1, Nmax + 1))
        self.loop_settings['outer_radius'] = (
            ar/2 * self.initial_settings['disk_thickness']
        )
        self.loop_settings['Lx'] = (self.loop_settings['outer_radius'] *
            self.initial_settings['L_div_outer_r'])
        self.loop_settings['shell_thickness'] = (
            self.initial_settings['disk_thickness'] * self.loop_settings['tau'])
        self.loop_settings['geo_fname'] = ''.join([
            'geo/',
            '.'.join([
                '_'.join([self.last_loop_state['seconds'],
                    'N', str(self.loop_settings['N']),
                    'tau', str(self.loop_settings['tau']),
                    'Lr', str(self.initial_settings['L_div_outer_r']),
                    'ar', str(self.loop_settings['ar'])]),
                'geo'])])

    def loop(self, *args, **kwargs):
        def create_fem_input():
            print('create fem input...', end=' ', flush=True)
            strains = {
                'XX': '0.01 0 0\n0 0 0\n0 0 0',
                'YY': '0 0 0\n0 0.01 0\n0 0 0',
                'ZZ': '0 0 0\n0 0 0\n0 0 0.01'
            }
            Lx = self.loop_settings['Lx']
            moduli = self.initial_settings['moduli']
            for axe in ['XX', 'YY', 'ZZ']:
                with open('input_{0}.txt'.format(axe), 'w') as fem_input:
                    fem_input.write('\n'.join([
                        'SizeX {0}'.format(Lx),
                        'SizeY {0}'.format(Lx),
                        'SizeZ {0}'.format(Lx),
                        'MeshFileName mesh.xdr',
                        'MaterialsGlobalFileName materials.bin',
                        'TaskName test_elas_E{0}'.format(axe),
                        'G_filler {0}'.format(moduli[0]),
                        'G_interface {0}'.format(moduli[1]),
                        'G_matrix {0}'.format(moduli[2]),
                        'Strain',
                        strains[axe]
                    ]))
            print('done!', flush=True)
            return self.loop_return_values['ok']

        def copy_files_to_cluster():
            print('copy files to cluster...', end=' ', flush=True)
            sftp = self.ssh.open_sftp()
            sftp.put(
                self.local_working_directory + self.wd +
                    self.loop_settings['geo_fname'],
                self.remote_working_directory + '1.geo'
            )
            for fname in ['input_XX.txt', 'input_YY.txt', 'input_ZZ.txt']:
                sftp.put(self.local_working_directory + self.wd + fname,
                    self.remote_working_directory + fname)
            sftp.close()
            print('done!', flush=True)
            return self.loop_return_values['ok']

        def get_files_from_cluster():
            print('get files from cluster...', end=' ', flush=True)
            sftp = self.ssh.open_sftp()
            results_fem_main = [
                'test_elas_EXX_results.txt',
                'test_elas_EYY_results.txt',
                'test_elas_EZZ_results.txt'
            ]
            for fname in results_fem_main:
                if fname not in sftp.listdir(self.remote_working_directory):
                    continue
                sftp.get(
                    self.remote_working_directory + fname,
                    self.local_working_directory + self.wd + fname
                )
                shutil.copyfile(
                    self.local_working_directory + self.wd + fname,
                    self.local_working_directory + self.wd + 'files/' +
                        self.last_loop_state['seconds'] + '_' + fname
                )
            sftp.close()
            print('done!', flush=True)
            return self.loop_return_values['ok']

        def set_task_cluster(task_name):
            print('set task cluster...', end=' ', flush=True)
            print(task_name, file=sys.stderr)
            # equals to 'sbatch task_name.sh'
            if task_name == 'fem_gen':
                commands = [
                    'cd /home/users/antonsk',
                    'export LD_LIBRARY_PATH=libs',
                    'sbatch {0}'.format(self.fem_gen_file_name)
                ]
            elif task_name == 'fem_process':
                commands = [
                    'cd /home/users/antonsk',
                    'export LD_LIBRARY_PATH=libs',
                    'mv {0}/generated.vol {0}/out.mesh'.format(
                        self.remote_working_directory),
                    'sbatch {0}'.format(self.fem_process_file_name)
                ]
            elif task_name == 'fem_3_anton_xx':
                commands = [
                    'cd /home/users/antonsk',
                    'export LD_LIBRARY_PATH=libs',
                    'sbatch {0}'.format(self.fem_main_xx_file_name)
                ]
            elif task_name == 'fem_3_anton_yy':
                commands = [
                    'cd /home/users/antonsk',
                    'export LD_LIBRARY_PATH=libs',
                    'sbatch {0}'.format(self.fem_main_yy_file_name)
                ]
            elif task_name == 'fem_3_anton_zz':
                commands = [
                    'cd /home/users/antonsk',
                    'export LD_LIBRARY_PATH=libs',
                    'sbatch {0}'.format(self.fem_main_zz_file_name)
                ]
            else:
                return 1
            commands_list = '; '.join(commands)
            stdin, stdout, stderr = self.ssh.exec_command(commands_list)
            stdout_lines = stdout.readlines()
            stderr_lines = stderr.readlines()
            self.last_loop_state['last_cluster_task_name'] = int(
                stdout_lines[0][:-1].split()[3])
            print('done!', flush=True)
            return self.loop_return_values['ok']

        def run_cpp():
            def create_cpp_settings():
                print('\tcreate cpp settings...', end=' ', flush=True)
                settings = dict()
                for key in ('vertices_number', 'mixing_steps', 'max_attempts'):
                        settings[key] = self.initial_settings[key]
                for key in ('outer_radius', 'Lx', 'shell_thickness'):
                        settings[key] = self.loop_settings[key]
                # Wrtining settings with changing keys for cpp program
                settings['thickness'] = self.initial_settings['disk_thickness']
                settings['disks_number'] = self.loop_settings['N']
                settings['LOG'] = cpp_out_log_name
                settings['geo_fname'] = (
                    os.getcwd() + '/' + self.loop_settings['geo_fname']
                )
                fname = self.initial_settings['cpp_settings_fname']
                required_settings = (
                    self.initial_settings['required_settings']
                        [self.initial_settings['task_name'].replace(
                            'cluster_', '')]
                )
                for required_setting in required_settings:
                    if not required_setting in settings.keys():
                        print('error: required general setting is not set',
                            flush=True)
                        sys.exit() # because there is no chance that it will be set
                                   # in other loops
                with open(fname, 'w') as f:
                    for (setting_name, setting_value) in settings.items():
                        f.write(' '.join([
                            str(setting_name), str(setting_value), '\n']))
                for key in settings.keys():
                    self.last_loop_state[key] = settings[key]
                print('done!', flush=True)

            create_cpp_settings()
            cpp_start_time = time.time()
            print('\trunning cpp exe...', end=' ', flush=True)
            cpp_returned = subprocess.call(
                [self.initial_settings['cpp_directory'] +
                    self.initial_settings['cpp_polygons_executables']
                        [self.initial_settings['task_name'].replace(
                            'cluster_', '')],
                 self.initial_settings['cpp_settings_fname']],
                stdout=open('logs/cpp_log_{0}'.format(self.year_month_day), 'a'),
                stderr=open('logs/all_errors_{0}'.format(self.year_month_day),
                    'a'))
            print('done!', flush=True)
            return cpp_returned

        def process_cpp_log():
            print('process cpp log...', end=' ', flush=True)
            parsed_log = dict()
            with open(cpp_out_log_name) as f:
                for line in f:
                    value, other = line.split(maxsplit=1)
                    if other == '(algorithm used)\n':
                        parsed_log['algorithm'] = value
                    elif other == '(status of system formation)\n':
                        parsed_log['system_reation_state'] = bool(value)
                    elif other == '(number of fillers prepared)\n':
                        parsed_log['fillers_real_number'] = int(value)
                    elif other == '(possible max attempts number)\n':
                        parsed_log['max attempts'] = int(value)
                    elif other == '(real attempts number)\n':
                        parsed_log['made attempts'] = int(value)
                    elif other == '(flag_testing)\n':
                        parsed_log['flag_testing'] = bool(value)
                    elif other == '(number of intersections in system)\n':
                        parsed_log['intersections_number'] = int(value)
                    elif other == '(percolation flag along x: )\n':
                        parsed_log['percolation_x'] = bool(int(value))
                    elif other == '(percolation flag along y: )\n':
                        parsed_log['percolation_y'] = bool(int(value))
                    elif other == '(percolation flag along z: )\n':
                        parsed_log['percolation_z'] = bool(int(value))
            fi_real = (
                parsed_log['fillers_real_number'] /
                self.loop_settings['N'] *
                self.loop_settings['fi_max_possible']
            )
            self.last_loop_state['fillers_real_number'] = (
                parsed_log['fillers_real_number']
            )
            self.loop_settings['fi_real'] = fi_real
            perc_x_str = ('1' if parsed_log['percolation_x'] else '0')
            perc_y_str = ('1' if parsed_log['percolation_y'] else '0')
            perc_z_str = ('1' if parsed_log['percolation_z'] else '0')
            perc_str = ''.join([perc_x_str, perc_y_str, perc_z_str])
            self.last_loop_state['perc_x'] = perc_x_str
            self.last_loop_state['perc_y'] = perc_y_str
            self.last_loop_state['perc_z'] = perc_z_str
            new_geo_fname = '/'.join([
                *self.loop_settings['geo_fname'].split('/')[:-1],
                '_'.join([perc_str,
                    self.loop_settings['geo_fname'].split('/')[-1]])])
            os.rename('{0}'.format(self.loop_settings['geo_fname']),
                '{0}'.format(new_geo_fname))
            self.loop_settings['geo_fname'] = new_geo_fname
            print('done!', flush=True)
            return self.loop_return_values['ok']

        def prepare_cluster():
            # Tries to remove 1.geo from the cluster
            stdin, stdout, stderr = self.ssh.exec_command('; '.join([
                'cd {0}'.format(self.remote_working_directory),
                'rm 1.geo'
            ]))
            return self.loop_return_values['ok']

        def wait_for_cluster():
            print('wait for cluster...', flush=True)
            while True:
                stdin, stdout, stderr = self.ssh.exec_command(
                    'squeue --user=antonsk -o "%.10i %.50j %.2t %.10M %.50Z"')
                tasks = stdout.readlines()[1:]
                tasks = [task for task in tasks if
                    task.split()[4] == self.remote_working_directory]
                if not tasks:
                    break
                else:
                    for task in tasks:
                        ls = task.split()
                        task_wd = ls[4]
                        if (task_wd != self.remote_working_directory):
                            return self.loop_return_values['bad_task_wd']
                        jobid = ls[0]
                        task_name = ls[1]
                        state = ls[2]
                        time_running = ls[3]
                        fmt = 'number={0}, name={1}, state={2}, time={3}'.format(
                            jobid, task_name, state, time_running)
                        print('\t', fmt, time.asctime(), flush=True)
                        new_line = 'waiting for ' + fmt + ' ' + time.asctime()
                        try:
                            # https://stackoverflow.com/a/5291044:
                            #     "\033[F" - Cursor up one line
                            #     "\033[K" - Clear to the end of line
                            old = self.last_loop_state['last_line_stderr']
                            old_ls = old.split()
                            new_ls = new_line.split()
                            old_id = old_ls[2]
                            old_state = old_ls[4]
                            new_id = new_ls[2]
                            new_state = new_ls[4]
                            if old_id == new_id and old_state == new_state:
                                pass
                                # should look like only update of running time
                                #print(''.join(['\033[F' + '\033[K', new_line]),
                                #    file=sys.stderr, flush=True)
                            else:
                                pass
                                #print(new_line, file=sys.stderr, flush=True)
                        except KeyError:
                            # first check leads here
                            #print('exception key error', file=sys.stderr)
                            #print(new_line, flush=True, file=sys.stderr)
                            pass
                        self.last_loop_state['last_line_stderr'] = new_line
                    print(' *** ', flush=True)
                time.sleep(5)
            err_lines = stderr.readlines()
            if err_lines:
                print('got err_lines: ', err_lines, file=sys.stderr)
                return self.loop_return_values['stderr_not_empty']
            try:
                stdin, stdout, stderr = self.ssh.exec_command(
                    'stat --printf="%s" {0}/{1}.err'.format( # file.err not empy
                        self.remote_working_directory,
                        self.last_loop_state['last_cluster_task_name']))
                count_err_file = int(stdout.readlines()[0])
                if count_err_file > 0:
                    print('got err lines', file=sys.stderr)
                    return self.loop_return_values['err_not_empty']
            except KeyError:
                self.ssh.exec_command('; '.join([
                    'cd /s/ls2/users/antonsk/{0}'.format(
                        self.remote_working_directory),
                    'ls'
            ]))
            except Exception as e:
                print(e, e.__class__.__name__, file=sys.stderr)
                return self.loop_return_values['exception_caugth']
            print('done', flush=True)
            return self.loop_return_values['ok']

        def log_iteration():
            print('log interation...', end=' ', flush=True)
            with open(self.py_main_log, 'a') as main_log:
                main_log.write('\n'.join([
                    '**********',
                    ' '.join(['seconds', self.last_loop_state['seconds']]),
                    ' '.join(['time', time.asctime()]),
                    ' '.join(['task_name', self.initial_settings['task_name']]),
                    ' '.join(['N', str(self.loop_settings['N'])]),
                    ' '.join(['tau', str(self.loop_settings['tau'])]),
                    ' '.join(['ar', str(self.loop_settings['ar'])]),
                    ' '.join(['fi_real', str(self.loop_settings['fi_real'])]),
                    ' '.join(['Ef', str(self.initial_settings['moduli'][0])]),
                    ' '.join(['Ei', str(self.initial_settings['moduli'][1])]),
                    ' '.join(['Em', str(self.initial_settings['moduli'][2])]),
                    ' '.join(['L_div_outer_r',
                        str(self.initial_settings['L_div_outer_r'])]),
                    *['='.join([''.join(['E', str(k)]), str(v)])
                        for k, v in self.last_loop_state['moduli'].items()],
                    'perc_x {0}'.format(self.last_loop_state['perc_x']),
                    'perc_y {0}'.format(self.last_loop_state['perc_y']),
                    'perc_z {0}'.format(self.last_loop_state['perc_z']),
                    'N_real {0}'.format(self.last_loop_state[
                        'fillers_real_number']),
                    ' '.join(['iteration_time',
                        str(time.time() - self.last_loop_state['start_time']),
                    '\n'])
                ]))
            print('done!', flush=True)
            return self.loop_return_values['ok']

        try:
            start_step = kwargs['start_step']
            if start_step not in self.steps:
                start_step = None
        except:
            start_step = None

        try:
            print('start step = {0}'.format(start_step), file=sys.stderr)
            self.last_loop_state['start_time'] = time.time()
            # prepare_cluster
            if start_step in [None, *self.steps[:1]]:
                self.last_loop_state['last_step'] = 'prepare_cluster'
                try:
                    code = prepare_cluster()
                except Exception as e:
                    print(e, e.__class__.__name__, file=sys.stderr)
                    print('cannot start!', file=sys.stderr)
                    print(self.local_working_directory, file=sys.stderr)
                    sys.exit()
                self.last_loop_state['prepare_cluster_return_code'] = code
                print('prepare_cluster', code, file=sys.stderr)
            # run_cpp
            if start_step in [None, *self.steps[:2]]:
                cpp_out_log_name = '_'.join([
                    'py_cpp_log',
                    self.initial_settings['task_name'].replace('cluster_', ''),
                    str(self.last_loop_state['seconds'])
                ])
                self.files_to_remove.add(cpp_out_log_name)
                self.last_loop_state['last_step'] = 'run_cpp'
                code = run_cpp()
                self.last_loop_state['run_cpp_return_code'] = code
                print('prepare_cluster', code, file=sys.stderr)
            if start_step in [None, *self.steps[:3]]:
                self.last_loop_state['last_step'] = 'process_cpp_log'
                code = process_cpp_log()
                self.last_loop_state['process_cpp_log_return_code'] = code
                print('process_spp_log', code, file=sys.stderr)
            if start_step in [None, *self.steps[:4]]:
                self.last_loop_state['last_step'] = 'create_fem_input'
                code = create_fem_input()
                self.last_loop_state['create_fem_input_return_code'] = code
                print('create_fem_input', code, file=sys.stderr)
            if start_step in [None, *self.steps[:5]]:
                self.last_loop_state['last_step'] = 'copy_files_to_cluster'
                code = copy_files_to_cluster()
                self.last_loop_state['copy_files_to_cluster_return_code'] = code
                print('copy_files_to_cluster', code, file=sys.stderr)
            if start_step in [None, *self.steps[:6]]:
                self.last_loop_state['last_step'] = 'set_fem_gen'
                code = set_task_cluster('fem_gen')
                self.last_loop_state['set_fem_gen_return_code'] = code
                print('set_fem_gen', code, file=sys.stderr)
            if start_step in [None, *self.steps[:7]]:
                code = wait_for_cluster()
                self.last_loop_state['wait_fem_gen_return_code'] = code
                print('wait_fem_gen', code, file=sys.stderr)
                if code != 0:
                    return code
            if start_step in [None, *self.steps[:8]]:
                self.last_loop_state['last_step'] = 'fem_process'
                code = set_task_cluster('fem_process')
                self.last_loop_state['set_fem_process_return_code'] = code
                print('set_fem_process', code, file=sys.stderr)
            if start_step in [None, *self.steps[:9]]:
                code = wait_for_cluster()
                self.last_loop_state['wait_fem_process_return_code'] = code
                print('wait_fem_process', code, file=sys.stderr)
                if code != 0:
                    return code
            if start_step in [None, *self.steps[:10]]:
                self.last_loop_state['last_step'] = 'fem_main_xx'
                code = set_task_cluster('fem_3_anton_xx')
                self.last_loop_state['set_fem_main_xx_return_code'] = code
                print('set_fem_main_xx', code, file=sys.stderr)
            if start_step in [None, *self.steps[:11]]:
                code = wait_for_cluster()
                self.last_loop_state['wait_fem_main_xx_return_code'] = code
                print('wait_fem_main_xx', code, file=sys.stderr)
                if code != 0: 
                    return code
            if start_step in [None, *self.steps[:12]]:
                self.last_loop_state['last_step'] = 'fem_main_yy'
                code = set_task_cluster('fem_3_anton_yy')
                self.last_loop_state['set_fem_main_yy_return_code'] = code
                print('set_fem_main_yy', code, file=sys.stderr)
            if start_step in [None, *self.steps[:13]]:
                code = wait_for_cluster()
                self.last_loop_state['wait_fem_main_yy_return_code'] = code
                print('wait_fem_main_yy', code, file=sys.stderr)
                if code != 0:
                    return code
            if start_step in [None, *self.steps[:14]]:
                self.last_loop_state['last_step'] = 'fem_main_zz'
                code = set_task_cluster('fem_3_anton_zz')
                self.last_loop_state['set_fem_main_zz_return_code'] = code
                print('set_fem_main_zz', code, file=sys.stderr)
            if start_step in [None, *self.steps[:15]]:
                code = wait_for_cluster()
                self.last_loop_state['wait_fem_main_zz_return_code'] = code
                print('wait_fem_main_zz', code, file=sys.stderr)
                if code != 0:
                    return code
            if start_step in [None, *self.steps[:16]]:
                self.last_loop_state['last_step'] = 'get_files_from_cluster'
                code = get_files_from_cluster()
                self.last_loop_state['get_files_return_code'] = code
                print('get_files_from_cluster', code, file=sys.stderr)
            if start_step in [None, *self.steps[:17]]:
                self.last_loop_state['last_step'] = 'get_moduli'
                self.last_loop_state['moduli'] = ModuliGetter().get_moduli(
                    fname_template='test_elas_E{0}_results.txt',
                    axis=['XX', 'YY', 'ZZ'])
            if start_step in [None, *self.steps]:
                self.last_loop_state['last_step'] = 'log_iteration'
                log_iteration()
        except TimeoutError:
            # network error - trying solve it by restarting netwok manager
            restart_manager_str = 'sudo service network-manager restart'
            start_wifi_str = 'ifconfig wlan0 down'
            subprocess.call(restart_manager_str.split())
        except OSError:
            # i do not know why it happens excatly
            restart_manager_str = 'sudo service network-manager restart'
            start_wifi_str = 'ifconfig wlan0 down'
            subprocess.call(restart_manager_str.split())
        except Exception as e:
            print('got unexpected exception\n',
                e, e.__class__.__name__,
               'trying to restart network manager and continue looping',
               file=sys.stderr)
            restart_manager_str = 'sudo service network-manager restart'
            start_wifi_str = 'ifconfig wlan0 down'
            subprocess.call(restart_manager_str.split())
        return self.loop_return_values['ok']

    def postprocess(self, *args, **kwargs):
        print('postprocess...', end=' ', flush=True)
        # remote clean
        command = '; '.join([
            'cd {0}'.format(self.remote_working_directory),
            ' '.join(['rm',
                 '*.err *.out *.geo intput_* materials.bin',
                 'mesh.xdr out.mesh mytask.log.* stresses.txt',
                 'test_elas_*'])
            ])
        #print(command, file=sys.stderr)
        stdin, stdout, stderr = self.ssh.exec_command(command)
        err_lines = stdout.readlines()
        #print(err_lines, file=sys.stderr)
        # local clean
        #for fname in self.files_to_remove:
        #    fname_to_remove = '/'.join([os.getcwd(), fname])
        #    try:
        #         #print(fname_to_remove, file=sys.stderr)
        #         os.remove(fname_to_remove)
        #    except:
        #         #print('here', fname_to_remove, file=sys.stderr)
        #         pass
        #for fname in os.listdir(self.local_working_directory):
        #    if fname in [self.py_main_log, 'settings_cpp']:
        #        continue
        #    try:
        #         os.remove(local_working_directory + fname)
        #    except:
        #         #print('here too', fname, file=sys.stderr)
        #         pass
        shutil.move('settings_cpp', 'files/{0}_settings_cpp'.format(
            self.last_loop_state['seconds']))
        print('done!', flush=True)
        return self.loop_return_values['ok']
