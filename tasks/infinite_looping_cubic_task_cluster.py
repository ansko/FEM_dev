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


class InfiniteLoopingCubicTaskCluster(InfiniteLoopingTask):
    loop_return_values = {
    }
    cluster_white_list = [
        'libs', 'gen_mesh.x', 'processMesh.x', 'FEManton3.o', 'materials.txt',
        'matrices.txt', 'tensor.cpp', 'tensor.h', '1.geo'
    ]
    files_to_remove = set([
        'input_XX.txt', 'input_YY.txt', 'input_ZZ.txt',
        'test_elas_EXX_results.txt', 'test_elas_EYY_results.txt',
        'test_elas_EZZ_results.txt', 'settings_cpp'
    ])
    steps = [
        'prepare_cluster', 'run_cpp', 'process_cpp_log', 'create_fem_input',
        'copy_files_to_cluster', 'fem_gen', 'wait_fem_gen', 'fem_process',
        'wait_fem_process', 'fem_main_xx', 'wait_fem_main_xx', 'fem_main_yy',
        'wait_fem_main_yy', 'fem_main_zz', 'wait_fem_main_zz',
        'get_files_from_cluster', 'get_moduli', 'log_iteration'
    ]
    local_working_directory = '/home/anton/AspALL/Projects/FEM_dev/'
    remote_working_directory = '/s/ls2/users/antonsk/FEM/'

    def prepare(self, *args, **kwargs):
        # All settings that are stored in the settings.py, not all of them
        # are required in this task, so only relevant will be kept.
        print('starting cluster task with', args, kwargs, flush=True)
        print(sys.stdout.name, file=sys.stderr, flush=True)
        settings = Settings()
        for key in ('ars', 'cpp_polygons_executables', 'L_div_outer_r',
            'disk_thickness', 'vertices_number', 'mixing_steps', 'max_attempts',
            'cpp_settings_fname', 'required_settings', 'cpp_directory', 'moduli',
            'FEMFolder', 'memory', 'limitation_memory_ratio', 'taus',
            'disk_thickness'):
                self.initial_settings[key] = settings[key]

        #
        self.initial_settings['ars'] = [50]
        #
        wd = 'cluster_cubic'
        if 'working_directory' in kwargs.keys():
            wd = kwargs['working_directory']
        self.initial_settings['working_directory'] = wd
        self.wd = wd+ '/'
        if wd not in os.listdir():
            os.mkdir(wd)
        os.chdir(wd)
        settings['ars'] = [50]#settings['ars'][-1:]
        try:
            self.initial_settings['task_name'] = kwargs['task_name']
            asc_time = time.asctime().split()
            self.year_month_day = '_'.join([asc_time[4], asc_time[1], asc_time[2]])
            self.py_main_log = 'py_main_log_' + self.year_month_day
            for dirname in ['logs', 'geo', 'files']:
                if dirname not in os.listdir():
                    os.mkdir(dirname)
        except Exception as e: # Something that should never happen
            print('******', e, flush=True)
        self.ssh = paramiko.SSHClient()
        self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.ssh.connect(
            ClusterSettingsKiaeMe().host,
            username=ClusterSettingsKiaeMe().user,
            password=ClusterSettingsKiaeMe().pwd,
            key_filename=ClusterSettingsKiaeMe().key
        )

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
            return 0

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
            return 0

        def get_files_from_cluster():
            print('get files from cluster...', end=' ', flush=True)
            sftp = self.ssh.open_sftp()
            results_fem_main = [
                'test_elas_EXX_results.txt',
                'test_elas_EYY_results.txt',
                'test_elas_EZZ_results.txt'
            ]
            for fname in results_fem_main:
                sftp.get(
                    self.remote_working_directory + fname,
                    self.local_working_directory + self.wd + fname
                )
                shutil.copyfile(
                    self.local_working_directory + self.wd + fname,
                    self.local_working_directory + self.wd +
                        self.last_loop_state['seconds'] + fname
                )
            sftp.close()
            print('done!', flush=True)
            return 0

        def set_task_cluster(task_name):
            print('set task cluster...', end=' ', flush=True)
            # equals to 'sbatch task_name.sh'
            commands = [
                'cd /home/users/antonsk',
                'export LD_LIBRARY_PATH=libs',
                'mv {0}/generated.vol {0}/out.mesh'.format(
                     '/s/ls2/users/antonsk/FEM'),
                'sbatch {0}.sh'.format(task_name)
            ]
            if task_name != 'fem_process':
                commands.pop(2)
            commands_list = '; '.join(commands)
            stdin, stdout, stderr = self.ssh.exec_command(commands_list)
            self.last_loop_state['last_cluster_task_name'] = int(
                stdout.readlines()[0][:-1].split()[3])
            print('done!', flush=True)
            return 0

        def run_cpp():
            print('run cpp...', flush=True)
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
                        return 0
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
            return 0

        def prepare_cluster():
            print('prepare cluster...', end=' ', flush=True)
            stdin, stdout, stderr = self.ssh.exec_command('; '.join([
                'cd /s/ls2/users/antonsk/FEM',
                'rm 1.geo'
            ]))
            print('done', flush=True)
            return 0

        def wait_for_cluster():
            print('wait for cluster...', flush=True)
            while True:
                stdin, stdout, stderr = self.ssh.exec_command(
                    'squeue --user=antonsk') # (-o "%.10i %.15j %.2t %.10M")
                tasks = stdout.readlines()[1:]
                if not tasks:
                    break
                else:
                    print('\t*** tasks on cluster ***', time.asctime(), flush=True)
                    for task in tasks:
                        ls = task.split()
                        print('\tnumber={0}, name={1}, state={2}, time={3}'.format(
                                ls[0], ls[2], ls[4], ls[5]),
                            time.asctime(),
                            flush=True)
                        print('waiting for',
                            'number={0}, name={1}, state={2}, time={3}'.format(
                                ls[0], ls[2], ls[4], ls[5]),
                            time.asctime(),
                            flush=True,
                            file=sys.stderr)
                    print(' *** ', flush=True)
                time.sleep(5)
            if stderr.readlines():
                return 1
            try:
                stdin, stdout, stderr = self.ssh.exec_command(
                    'stat --printf="%s" /s/ls2/users/antonsk/FEM/{0}.err'.format(
                        self.last_loop_state['last_cluster_task_name']))
                if int(stdout.readlines()[0]) > 0:
                    return 1
            except Exception:
                return 1
            print('done', flush=True)
            return 0

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
            return 0


        def get_start_step(start_step):
            print('get start step...', end=' ', flush=True)
            """
            steps = [
                'prepare_cluster', 'run_cpp', 'process_cpp_log',
                'create_fem_input', 'copy_files_to_cluster', 'fem_gen',
                'wait_fem_gen', 'fem_process', 'wait_fem_process', 'fem_main_xx',
                'wait_fem_main_xx', 'fem_main_yy', 'wait_fem_main_yy',
                'fem_main_zz', 'wait_fem_main_zz', 'get_files_from_cluster',
                'get_moduli', 'log_iteration'
            ]
            """
            """
            if start_step == 'prepare_cluster':
                stdin, stdout, stderr = self.ssh.exec_command(
                    'ls /s/ls2/users/antonsk/FEM')
                print(stdout.readlines(), file=sys.stderr)
                if ('1.geo\n' in stdout.readlines() and
                    'test_elas_EXX_results.txt\n' not in stdout.readlines() and
                    'test_elas_EYY_results.txt\n' not in stdout.readlines() and
                    'test_elas_EZZ_results.txt\n' not in stdout.readlines()):
                        pass
                else:
                    print('bad', file=sys.stderr)
            elif start_step in  [
                'run_cpp', 'process_cpp_log',
                'create_fem_input', 'copy_files_to_cluster', 'fem_gen',
                'wait_fem_gen', 'fem_process', 'wait_fem_process', 'fem_main_xx',
                'wait_fem_main_xx', 'fem_main_yy', 'wait_fem_main_yy',
                'fem_main_zz', 'wait_fem_main_zz', 'get_files_from_cluster',
                'get_moduli', 'log_iteration'
                ]:
                    pass
            else:
                print('error, unknown start_step:', start_step, file=sys.stderr)
            """
            print('done!', flush=True)
            return start_step

        try:
            start_step = kwargs['start_step']
            start_step = get_start_step(start_step)
        except:
            start_step = None

        try:

            self.last_loop_state['start_time'] = time.time()
            if start_step in [None, self.steps[0]]:
                self.last_loop_state['last_step'] = 'prepare_cluster'
                self.last_loop_state['prepare_cluster_return_code'] = (
                    prepare_cluster()
                )
            if start_step in [None, self.steps[1]]:
                cpp_out_log_name = '_'.join([
                   'py_cpp_log',
                    self.initial_settings['task_name'].replace('cluster_', ''),
                    str(self.last_loop_state['seconds'])
                ])
                self.files_to_remove.add(cpp_out_log_name)
                self.last_loop_state['last_step'] = 'run_cpp'
                self.last_loop_state['run_cpp_return_code'] = run_cpp()
            if start_step in [None, self.steps[2]]:
                self.last_loop_state['last_step'] = 'process_cpp_log'
                self.last_loop_state['process_cpp_log_return_code'] = (
                    process_cpp_log()
                )
            if start_step in [None, self.steps[3]]:
                self.last_loop_state['last_step'] = 'create_fem_input'
                self.last_loop_state['create_fem_input_return_code'] = (
                    create_fem_input()
                )
            if start_step in [None, self.steps[4]]:
                self.last_loop_state['last_step'] = 'copy_files_to_cluster'
                self.last_loop_state['copy_files_to_cluster_return_code'] = (
                    copy_files_to_cluster()
                )
            if start_step in [None, self.steps[5]]:
                self.last_loop_state['last_step'] = 'fem_gen'
                self.last_loop_state['set_fem_gen_return_code'] = (
                        set_task_cluster('fem_gen')
                )
            if start_step in [None, self.steps[6]]:
                self.last_loop_state['wait_fem_gen_return_code'] = (
                    wait_for_cluster()
                )
                if self.last_loop_state['wait_fem_gen_return_code'] != 0:
                    return self.last_loop_state['wait_fem_gen_return_code']
            if start_step in [None, self.steps[7]]:
                self.last_loop_state['last_step'] = 'fem_process'
                self.last_loop_state['set_fem_process_return_code'] = (
                        set_task_cluster('fem_process')
                )
            if start_step in [None, self.steps[8]]:
                self.last_loop_state['wait_fem_process_return_code'] = (
                    wait_for_cluster()
                )
                if self.last_loop_state['wait_fem_process_return_code'] != 0:
                    return self.last_loop_state['wait_fem_process_return_code']
            if start_step in [None, self.steps[9]]:
                self.last_loop_state['last_step'] = 'fem_main_xx'
                self.last_loop_state['set_fem_main_xx_return_code'] = (
                    set_task_cluster('fem_main_xx')
                )
            if start_step in [None, self.steps[10]]:
                self.last_loop_state['wait_fem_main_xx_return_code'] = (
                    wait_for_cluster())
                if self.last_loop_state['wait_fem_main_xx_return_code'] != 0:
                    return self.last_loop_state['wait_fem_main_xx_return_code']
            if start_step in [None, self.steps[11]]:
                self.last_loop_state['last_step'] = 'fem_main_yy'
                self.last_loop_state['set_fem_main_yy_return_code'] = (
                    set_task_cluster('fem_main_yy')
                )
            if start_step in [None, self.steps[12]]:
                self.last_loop_state['wait_fem_main_yy_return_code'] = (
                    wait_for_cluster())
                if self.last_loop_state['wait_fem_main_yy_return_code'] != 0:
                    return self.last_loop_state['wait_fem_main_yy_return_code']
            if start_step in [None, self.steps[13]]:
                self.last_loop_state['last_step'] = 'fem_main_zz'
                self.last_loop_state['set_fem_main_zz_return_code'] = (
                    set_task_cluster('fem_main_zz')
                )
            if start_step in [None, self.steps[14]]:
                self.last_loop_state['wait_fem_main_zz_return_code'] = (
                    wait_for_cluster())
                if self.last_loop_state['wait_fem_main_zz_return_code'] != 0:
                    return self.last_loop_state['wait_fem_main_zz_return_code']
            if start_step in [None, self.steps[15]]:
                self.last_loop_state['last_step'] = 'get_files_from_cluster'
                self.last_loop_state['get_files_return_code'] = (
                    get_files_from_cluster()
                )
            if start_step in [None, self.steps[16]]:
                self.last_loop_state['last_step'] = 'get_moduli'
                self.last_loop_state['moduli'] = ModuliGetter().get_moduli(
                    fname_template='test_elas_E{0}_results.txt',
                    axis=['XX', 'YY', 'ZZ'])
            if start_step in [None, self.steps[17]]:
                self.last_loop_state['last_step'] = 'log_iteration'
                log_iteration()
        except TimeoutError:
            # network error - trying solve it by restarting netwok manager
            restart_manager_str = 'sudo service network-manager restart'
            start_wifi_str = 'ifconfig wlan0 down'
            subprocess.call(restart_manager_str.split())
        return 0

    def postprocess(self, *args, **kwargs):
        print('postprocess...', end=' ', flush=True)
        stdin, stdout, stderr = self.ssh.exec_command('; '.join([
            'cd /s/ls2/users/antonsk/FEM',
            'ls'
        ]))
        for fname in stdout.readlines():
            if fname[:-1] not in self.cluster_white_list:
                 stdin, stdout, stderr = self.ssh.exec_command('; '.join([
                     'cd /s/ls2/users/antonsk/FEM',
                     'rm {0}'.format(fname) 
                 ]))
        for fname in self.files_to_remove:
            try:
                 os.remove('/'.join([os.getcwd(), fname]))
            except:
                 pass
        print('done!', flush=True)
        return 0
