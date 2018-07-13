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
from utils.cleaner import Cleaner
from utils.get_moduli import ModuliGetter


class CubicTask:
    single_loop_return_values = {
    }
    black_list = set([
        'input_XX.txt', 'input_YY.txt', 'input_ZZ.txt', 'out.mesh', 'mesh.xdr',
        'test_elas_EXX_log.txt', 'test_elas_EYY_log.txt', 'test_elas_EZZ_log.txt',
        'test_elas_EXX_results.txt', 'test_elas_EYY_results.txt',
        'test_elas_EZZ_results.txt', 'stresses.txt'
    ])

    def __init__(self, task_name, start_step=None):
        self.fill_settings()
        if task_name not in self.settings['cpp_polygons_executables'].keys():
            print('error in task.py(line 30): unavailable task')
            sys.exit(0)
        self.task_name = task_name
        asc_time = time.asctime().split()
        self.year_month_day = '_'.join([asc_time[4], asc_time[1], asc_time[2]])
        self.py_main_log = 'py_main_log_' + self.year_month_day
        if 'logs' not in os.listdir():
            os.mkdir('logs')
        if 'geo' not in os.listdir():
            os.mkdir('geo')
        self.productive_runs_made = 0
        self.attempts_made = 0
        self.start_infinite_loop()


    def start_fem_task(self, last_fem_task_performed=None):
        if last_fem_task_performed is None:
            self.start_infinite_loop()
        else:
            new_task_name = None
            new_task_options = set()
            if last_fem_task_performed['name'] == tracked_names[0]:
                new_task_name = tracked_names[1]
            elif last_fem_task_performed['name'] == tracked_names[1]:
                new_task_name = tracked_names[2]
            elif last_fem_task_performed['name'] == tracked_names[2]:
                if last_fem_task_performed['cmdline'][1][6:8] in ['XX', 'YY']:
                    new_task_name = tracked_names[2]
                    new_task_options.add(
                        last_fem_task_performed['cmdline'][1][6:8].replace(
                            'XX', 'YY').replace('YY', 'ZZ'))
                else:
                    new_task_name = tracked_names[0]
            new_task_options = tuple(new_task_options)
            self.run_process(start_task, tuple(new_task_options))
            print('started', new_task_name, 'with parameters',  new_task_options)

    def start_infinite_loop(self, step=None):
        while(True):
            self.fill_loop_settings()
            print('productive_runs', self.productive_runs_made,
                'attempts_made', self.attempts_made,
                'current (N, tau, ar) = (',
                self.loop_settings['N'], self.loop_settings['tau'],
                self.loop_settings['ar'], ')')
            return_code = self.single_loop(step)
            if return_code == 0:
                self.productive_runs_made += 1
            self.attempts_made += 1

    def fill_settings(self):
        global_settings = Settings() # all settings that are stored in the
                                     # settings.py, not all of them are required
                                     # in the task
        self.settings = dict() # settings that will be used in this task
        for key in ('taus', 'ars', 'cpp_polygons_executables', 'L_div_outer_r',
            'disk_thickness', 'vertices_number', 'mixing_steps', 'max_attempts',
            'cpp_settings_fname', 'required_settings', 'cpp_directory', 'moduli',
            'FEMFolder', 'memory', 'limitation_memory_ratio'):
                self.settings[key] = global_settings[key]
        self.settings['LD_LIBRARY_PATH'] = (self.settings['FEMFolder'] + 'libs' +
            ':' + self.settings['FEMFolder'] + 'my_libs')
        # /home/anton/FEMFolder3/libs:/home/anton/FEMFolder3/my_libs
        for key in ('gen_mesh_exe', 'process_mesh_exe', 'fem_main_exe'):
            self.settings[key] = self.settings['FEMFolder'] + global_settings[key]

    def fill_loop_settings(self):
        self.loop_settings = dict()
        self.loop_settings['tau'] = random.choice(self.settings['taus'])
        self.loop_settings['ar'] = random.choice(self.settings['ars'])
        ar = self.loop_settings['ar']
        Nmax = int(500 * ar / math.pi * 0.05)
        Nmax = min(10, Nmax)
        self.loop_settings['fi_max_possible'] = math.pi / 500 * Nmax / ar
        self.loop_settings['N'] = random.choice(range(1, Nmax + 1))
        self.loop_settings['outer_radius'] = ar/2 * self.settings['disk_thickness']
        self.loop_settings['Lx'] = (self.loop_settings['outer_radius'] *
            self.settings['L_div_outer_r'])
        self.loop_settings['shell_thickness'] = (self.settings['disk_thickness'] *
            self.loop_settings['tau'])

    def single_loop(self, step=None):
        Cleaner().clean_black_list(self.black_list)
        loop_start_time = time.time()
        seconds = str(int(time.time()))
        geo_fname = '.'.join(['_'.join([seconds, 'N', str(self.loop_settings['N']),
            'tau', str(self.loop_settings['tau']), 'Lr',
            str(self.settings['L_div_outer_r']), 'ar',
            str(self.loop_settings['ar'])]), 'geo'])
        cpp_out_log_name = '_'.join(['py_cpp_log', str(self.task_name),
            str(seconds)])
        self.black_list.add(cpp_out_log_name)
        settings_to_write = dict()
        for key in ('vertices_number', 'mixing_steps', 'max_attempts'):
            settings_to_write[key] = self.settings[key]
        for key in ('outer_radius', 'Lx', 'shell_thickness'):
            settings_to_write[key] = self.loop_settings[key]
        settings_to_write['thickness'] = self.settings['disk_thickness']
        settings_to_write['disks_number'] = self.loop_settings['N']
        settings_to_write['LOG'] = cpp_out_log_name
        settings_to_write['geo_fname'] = os.getcwd() + '/geo/' + geo_fname
        self.create_cpp_settings(settings_to_write)
        # run my cpp code
        cpp_start_time = time.time()
        cpp_returned = subprocess.call(
            [self.settings['cpp_directory'] +
                self.settings['cpp_polygons_executables'][self.task_name],
             self.settings['cpp_settings_fname']],
            stdout=open('logs/cpp_log_{0}'.format(self.year_month_day), 'a'),
            stderr=open('logs/all_errors_{0}'.format(self.year_month_day), 'a'))
        print('\tcpp_returned', cpp_returned)
        if cpp_returned != 0:
            return cpp_returned
        parsed_log = self.process_cpp_log(cpp_out_log_name)
        fi_real = (parsed_log['fillers_real_number'] / self.loop_settings['N'] *
            self.loop_settings['fi_max_possible'])
        self.loop_settings['fi_real'] = fi_real
        perc_str = ''
        perc_str += ('1' if parsed_log['percolation_x'] else '0')
        perc_str += ('1' if parsed_log['percolation_y'] else '0')
        perc_str += ('1' if parsed_log['percolation_z'] else '0')
        new_geo_fname = '_'.join([perc_str, geo_fname])
        os.rename('geo/{0}'.format(geo_fname), 'geo/{0}'.format(new_geo_fname))
        geo_fname = new_geo_fname
        # run all fem codes
        create_fem_input_returned = self.create_fem_input(self.settings)
        print('\tcreate_fem_input_returned', create_fem_input_returned)
        if create_fem_input_returned != 0:
            return create_fem_input_returned
        fem_env = os.environ
        fem_env['LD_LIBRARY_PATH'] = self.settings['LD_LIBRARY_PATH']
        gen_mesh_start_time = time.time()
        gen_mesh_returned = subprocess.call(
            [self.settings['gen_mesh_exe'], 'geo/' + geo_fname, '0.15', '2', '2'],
            env=fem_env,
            stdout=open('logs/gen_mesh_log_{0}'.format(self.year_month_day), 'a'),
            stderr=open('logs/all_errors_{0}'.format(self.year_month_day), 'a'))
        print('\tgen_mesh_returned', gen_mesh_returned)
        if gen_mesh_returned != 0:
            return gen_mesh_returned
        shutil.move('generated.vol', 'out.mesh')
        # process_mesh_exe eats all RAM avaliable, so it should be constrained
        previous_limits = resource.getrlimit(resource.RLIMIT_AS)
        my_all_memory = self.settings['memory']
        limitation = self.settings['limitation_memory_ratio'] * my_all_memory
        resource.setrlimit(resource.RLIMIT_AS, (limitation, limitation))
        process_mesh_start_time = time.time()
        # usually returns 0 (ok) or
        # 2 (out of memory(?!) for some absolutely unknown reason)
        processMesh_returned = subprocess.call(
            self.settings['process_mesh_exe'], env=fem_env,
            preexec_fn=lambda: resource.setrlimit(resource.RLIMIT_AS,
                (limitation, limitation)),
            stdout=open('logs/process_mesh_log_{0}'.format(self.year_month_day),
                        'a'),
            stderr=open('logs/all_errors_{0}'.format(self.year_month_day), 'a'))
        print('\tprocessMesh_returned', processMesh_returned)
        fem_main_x_start_time = time.time()
        FEMmain_x_returned = subprocess.call(
            [self.settings['fem_main_exe'], 'input_XX.txt'],
            env=fem_env,
            stdout=open('logs/fem_main_log_{0}'.format(self.year_month_day),'a'),
            stderr=open('logs/all_errors_{0}'.format(self.year_month_day), 'a'))
        print('\tFEMmain_x_returned', FEMmain_x_returned)
        if FEMmain_x_returned != 0:
            return FEMmain_x_returned
        fem_main_y_start_time = time.time()
        FEMmain_y_returned = subprocess.call(
            [self.settings['fem_main_exe'], 'input_YY.txt'],
            env=fem_env,
            stdout=open('logs/fem_main_log_{0}'.format(self.year_month_day), 'a'),
            stderr=open('logs/all_errors_{0}'.format(self.year_month_day), 'a'))
        print('\tFEMmain_y_returned', FEMmain_y_returned)
        if FEMmain_y_returned != 0:
            return FEMmain_y_returned
        fem_main_z_start_time = time.time()
        FEMmain_z_returned = subprocess.call(
            [self.settings['fem_main_exe'], 'input_ZZ.txt'],
            env=fem_env,
            stdout=open('logs/fem_main_log_{0}'.format(self.year_month_day), 'a'),
            stderr=open('logs/all_errors_{0}'.format(self.year_month_day), 'a'))
        fem_main_end_time = time.time()
        print('\tFEMmain_z_returned', FEMmain_z_returned)
        if FEMmain_z_returned != 0:
            return FEMmain_z_returned
        moduli = ModuliGetter().get_moduli(
            fname_template='test_elas_E{0}_results.txt',
            axis=['XX', 'YY', 'ZZ'])
        # logging
        with open(self.py_main_log, 'a') as main_log:
            main_log.write('# ' + seconds + ' ' + time.asctime() + '#'*50 + '\n')
            main_log.write('# ' + self.task_name + ' N ' +
                 str(self.loop_settings['N']) + ' tau ' +
                 str(self.loop_settings['tau']) + ' ar ' +
                 str(self.loop_settings['ar']) + '\n')
            main_log.write('!fi {0}\n'.format(self.loop_settings['fi_real']))
            main_log.write('!Ef {0}\n'.format(self.settings['moduli'][0]))
            main_log.write('!Ei {0}\n'.format(self.settings['moduli'][1]))
            main_log.write('!Em {0}\n'.format(self.settings['moduli'][2]))
            main_log.write('!Lr {0}\n'.format(self.settings['L_div_outer_r']))
            for k, v in self.settings.items():
                main_log.write('\t' + str(k) + ' ' + str(v) + '\n')
            for k, v in parsed_log.items():
                main_log.write('\t' + str(k) + ' ' + str(v) + '\n')
            for k, v in moduli.items():
                main_log.write('\tE_' + str(k) + ' ' + str(v) + '\n')
            iteration_time = time.time() - loop_start_time
            main_log.write('! all took {0}\n'.format(iteration_time))
            main_log.write('!     cpp took {0}\n'.format(
                gen_mesh_start_time - cpp_start_time))
            main_log.write('!     gen_mesh took {0}\n'.format(
                process_mesh_start_time - gen_mesh_start_time))
            main_log.write('!     process_mesh took {0}\n'.format(
                fem_main_x_start_time - process_mesh_start_time))
            main_log.write('!     fem_x took {0}\n'.format(
                fem_main_y_start_time - fem_main_x_start_time))
            main_log.write('!     fem_y took {0}\n'.format(
                fem_main_z_start_time - fem_main_y_start_time))
            main_log.write('!     fem_z took {0}\n'.format(
                fem_main_end_time - fem_main_z_start_time))
        print('\tfi', self.loop_settings['fi_real'])
        print('\titeration took', iteration_time)
        Cleaner().clean_black_list(self.black_list)
        return 0

    def create_cpp_settings(self, settings):
        fname = self.settings['cpp_settings_fname']
        required_settings = self.settings['required_settings'][self.task_name]
        with open(fname, 'w') as f:
            for required_setting in required_settings:
                if not required_setting in settings.keys():
                    print('error: required general setting is not set')
                    return 0
            for required_setting in required_settings:
                if not required_setting in settings.keys():
                    print('error: required specific setting is not set')
                    print(required_setting)
                    return 0
            for (setting_name, setting_value) in settings.items():
                f.write(' '.join([str(setting_name), str(setting_value), '\n']))

    def process_cpp_log(self, cpp_out_log_name):
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
        return parsed_log

    def create_fem_input(self, settings):
        Lx = self.loop_settings['Lx']
        for axe in ['XX', 'YY', 'ZZ']:
            with open('input_{0}.txt'.format(axe), 'w') as fem_input:
                fem_input.write('SizeX {0}\nSizeY {0}\nSizeZ {0}\n'.format(Lx))
                fem_input.write('MeshFileName mesh.xdr\n')
                fem_input.write('MaterialsGlobalFileName materials.bin\n')
                fem_input.write('TaskName test_elas_E{0}\n'.format(axe))
                fem_input.write('G_filler {0}\n'.format(settings['moduli'][0]))
                fem_input.write('G_interface {0}\n'.format(settings['moduli'][1]))
                fem_input.write('G_matrix {0}\n'.format(settings['moduli'][2]))
                fem_input.write('Strain\n')
                if axe == 'XX':
                    fem_input.write('0.01 0 0\n0 0 0\n0 0 0\n')
                if axe == 'YY':
                    fem_input.write('0 0 0\n0 0.01 0\n0 0 0\n')
                if axe == 'ZZ':
                    fem_input.write('0 0 0\n0 0 0\n0 0 0.01\n')
                fem_input.write('\n')
        return 0
