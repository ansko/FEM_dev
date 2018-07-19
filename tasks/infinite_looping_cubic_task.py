import math
import os
import pprint
pprint=pprint.PrettyPrinter(indent=4).pprint
import random
import resource
import shutil
import sys
import subprocess
import time

from settings.settings import Settings
from tasks.infinite_looping_task import  InfiniteLoopingTask
from utils.moduli_getter import ModuliGetter


class InfiniteLoopingCubicTask(InfiniteLoopingTask):
    loop_return_values = {
    }
    files_to_remove = set([
        'input_XX.txt', 'input_YY.txt', 'input_ZZ.txt', 'out.mesh', 'mesh.xdr',
        'test_elas_EXX_log.txt', 'test_elas_EYY_log.txt', 'test_elas_EZZ_log.txt',
        'test_elas_EXX_results.txt', 'test_elas_EYY_results.txt',
        'test_elas_EZZ_results.txt', 'stresses.txt'
    ])

    def prepare(self, *args, **kwargs):
        # All settings that are stored in the settings.py, not all of them
        # are required in this task, so only relevant will be kept.
        settings = Settings()
        for key in ('ars', 'cpp_polygons_executables', 'L_div_outer_r',
            'disk_thickness', 'vertices_number', 'mixing_steps', 'max_attempts',
            'cpp_settings_fname', 'required_settings', 'cpp_directory', 'moduli',
            'FEMFolder', 'memory', 'limitation_memory_ratio', 'taus',
            'disk_thickness'):
                self.initial_settings[key] = settings[key]
        print('cubic', sys.stdout.name, file=sys.stderr)
        self.initial_settings['ars'] = [10]#self.initial_settings['ars']
        wd = 'cubic'
        if 'working_directory' in kwargs.keys():
            wd = kwargs['working_directory']
        self.initial_settings['working_directory'] = wd
        self.wd =wd+ '/'
        self.initial_settings['LD_LIBRARY_PATH'] = (
            self.initial_settings['FEMFolder'] + 'libs:' +
            self.initial_settings['FEMFolder'] + 'my_libs'
        )
        for key in ('gen_mesh_exe', 'process_mesh_exe', 'fem_main_exe'):
            self.initial_settings[key] = (
                self.initial_settings['FEMFolder'] + settings[key]
            )
        if wd not in os.listdir():
            os.mkdir(wd)
        os.chdir(wd)
        try:
            self.initial_settings['task_name'] = kwargs['task_name']
            asc_time = time.asctime().split()
            self.year_month_day = '_'.join([asc_time[4], asc_time[1], asc_time[2]])
            self.py_main_log = 'py_main_log_' + self.year_month_day
            for dirname in ['logs', 'geo', 'files']:
                if dirname not in os.listdir():
                    os.mkdir(dirname)
        except Exception as e: # Something that should never happen
            print('******', e)

    def print_info(self, *args, **kwargs):
        print('***', time.asctime())
        print('loops={0}/{1}'.format(
            self.successful_loops_performed, self.loops_performed
        ))

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
        pprint(self.loop_settings)


    def loop(self, *args, **kwargs):
        def run_cpp():
            def create_cpp_settings():
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
                        [self.initial_settings['task_name']]
                )
                for required_setting in required_settings:
                    if not required_setting in settings.keys():
                        print('error: required general setting is not set')
                        return 0
                with open(fname, 'w') as f:
                    for (setting_name, setting_value) in settings.items():
                        f.write(' '.join([
                            str(setting_name), str(setting_value), '\n']))
                for key in settings.keys():
                    self.last_loop_state[key] = settings[key]

            create_cpp_settings()
            cpp_start_time = time.time()
            cpp_returned = subprocess.call(
                [self.initial_settings['cpp_directory'] +
                    self.initial_settings['cpp_polygons_executables']
                        [self.initial_settings['task_name']],
                 self.initial_settings['cpp_settings_fname']],
                stdout=open('logs/cpp_log_{0}'.format(self.year_month_day), 'a'),
                stderr=open('logs/all_errors_{0}'.format(self.year_month_day),
                    'a'))
            return cpp_returned

        def log_iteration():
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
                    '\n'.join([
                        ' '.join([key, str(self.last_loop_state[key])])
                            for key in self.last_loop_state.keys()]),
                    '\n'])
                ]))
            return 0

        def run_fem():
            def create_fem_input():
                strains = {
                    'XX': '0.01 0 0\n0 0 0\n0 0 0',
                    'YY': '0 0 0\n0 0.01 0\n0 0 0',
                    'ZZ': '0 0 0\n0 0 0\n0 0 0.01'
                }
                Lx = self.loop_settings['Lx']
                moduli = self.initial_settings['moduli']
                for axe in ['XX', 'YY', 'ZZ']:
                    fname = 'input_{0}.txt'.format(axe)
                    with open(fname, 'w') as fem_input:
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
                return 0

            def run_gen_mesh():
                gen_mesh_start_time = time.time()
                gen_mesh_returned = subprocess.call(
                    [self.initial_settings['gen_mesh_exe'],
                        self.loop_settings['geo_fname'], '0.15', '2', '2'],
                    env=fem_env,
                    stdout=open('logs/gen_mesh_log_{0}'.format(
                        self.year_month_day), 'a'),
                    stderr=open('logs/all_errors_{0}'.format(
                        self.year_month_day), 'a'))
                if gen_mesh_returned == 0:
                    shutil.move('generated.vol', 'out.mesh')
                else:
                    print('\tgen_mesh_returned', gen_mesh_returned)
                return gen_mesh_returned

            def run_process_mesh():
                # process_mesh_exe eats all RAM avaliable,
                # so it should be constrained
                previous_limits = resource.getrlimit(resource.RLIMIT_AS)
                my_all_memory = self.initial_settings['memory']
                limitation = (self.initial_settings['limitation_memory_ratio'] *
                    my_all_memory)
                resource.setrlimit(resource.RLIMIT_AS, (limitation, limitation))
                process_mesh_start_time = time.time()
                # usually returns 0 (ok) or
                # 2 (out of memory(?!) for some absolutely unknown reason)
                processMesh_returned = subprocess.call(
                    self.initial_settings['process_mesh_exe'], env=fem_env,
                    preexec_fn=lambda: resource.setrlimit(resource.RLIMIT_AS,
                        (limitation, limitation)),
                    stdout=open('logs/process_mesh_log_{0}'.format(
                        self.year_month_day), 'a'),
                    stderr=open('logs/all_errors_{0}'.format(
                        self.year_month_day), 'a'))
                if processMesh_returned not in [0, 2]:
                    print('\tprocessMesh_returned', processMesh_returned)
                return processMesh_returned

            def run_fem_main(axe):
                fem_main_start_time = time.time()
                FEMmain_returned = subprocess.call(
                    [self.initial_settings['fem_main_exe'],
                        'input_{}.txt'.format(axe)],
                    env=fem_env,
                    stdout=open('logs/fem_main_log_{0}'.format(
                        self.year_month_day),'a'),
                    stderr=open('logs/all_errors_{0}'.format(
                        self.year_month_day), 'a'))
                if FEMmain_returned != 0:
                    print('\tFEMmain_returned along {}'.format(axe),
                        FEMmain_returned)
                return FEMmain_returned

            for task in [create_fem_input, run_gen_mesh, run_process_mesh]:
                code = task()
                print(task.__name__, code)
                if code not in [0, 2]:
                    return code
            for axe in ['XX', 'YY', 'ZZ']:
                code = run_fem_main(axe)
                print('fem_main', axe, code)
            for fname in [
                'test_elas_EXX_results.txt',
                'test_elas_EYY_results.txt',
                'test_elas_EZZ_results.txt'
                ]:
                    shutil.copyfile(fname, 'files/' +
                        self.last_loop_state['seconds'] + '_' + fname)
            self.last_loop_state['moduli'] = ModuliGetter().get_moduli(
                fname_template='test_elas_E{0}_results.txt',
                axis=['XX', 'YY', 'ZZ'])
            return 0

        def process_cpp_log():
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
            fi_real = (parsed_log['fillers_real_number'] /
                self.loop_settings['N'] * self.loop_settings['fi_max_possible'])
            self.loop_settings['fi_real'] = fi_real
            perc_str = ''
            perc_str += ('1' if parsed_log['percolation_x'] else '0')
            perc_str += ('1' if parsed_log['percolation_y'] else '0')
            perc_str += ('1' if parsed_log['percolation_z'] else '0')
            self.last_loop_state['perc_x'] = parsed_log['percolation_x']
            self.last_loop_state['perc_y'] = parsed_log['percolation_y']
            self.last_loop_state['perc_z'] = parsed_log['percolation_z']
            self.last_loop_state['fillers_real_number'] = (
                parsed_log['fillers_real_number']
            )
            new_geo_fname = '/'.join([
                *self.loop_settings['geo_fname'].split('/')[:-1],
                '_'.join([perc_str,
                     self.loop_settings['geo_fname'].split('/')[-1]])])
            os.rename('{0}'.format(self.loop_settings['geo_fname']),
                '{0}'.format(new_geo_fname))
            self.loop_settings['geo_fname'] = new_geo_fname
            return 0

        self.last_loop_state['start_time'] = time.time()
        cpp_out_log_name = '_'.join(['py_cpp_log',
            self.initial_settings['task_name'],
            str(self.last_loop_state['seconds'])])
        self.files_to_remove.add(cpp_out_log_name)
        fem_env = os.environ
        fem_env['LD_LIBRARY_PATH'] = self.initial_settings['LD_LIBRARY_PATH']

        for sub_task in [run_cpp, process_cpp_log, run_fem, log_iteration]:
            print('running', sub_task.__name__, end='... ', flush=True)
            code = sub_task()
            print('done!', sub_task.__name__, code)
            if code not in [0, 2]:
                return code

        iteration_time = time.time() - self.last_loop_state['start_time']
        print('\tfi', self.loop_settings['fi_real'])
        print('\titeration took', iteration_time)
        return 0

    def postprocess(self, *args, **kwargs):
        shutil.move('settings_cpp', 'files/{0}_settings_cpp'.format(
            self.last_loop_state['seconds']))
        for fname in self.files_to_remove:
            if fname in os.listdir():
                os.remove(fname)
