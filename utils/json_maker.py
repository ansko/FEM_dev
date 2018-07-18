import json
import pprint
pprint=pprint.PrettyPrinter(indent=4).pprint
import sys


class JsonMaker:
    # same keys for old and new log types
    unified_keys = {
        'Lr': 'L_div_outer_r', 'L_div_outer_r': 'L_div_outer_r',
        'Ei': 'Ei', 'Em': 'Em', 'Ef': 'Ef',
        'geo_fname': 'geo_fname',
        'cpp': 'cpp_execution_time',
        'cpp_directory': 'cpp_directory',
        'FEMFolder': 'FEMFolder',
        'cpp_settings_fname': 'cpp_settings_fname',
        'gen_mesh': 'gen_mesh_execution_time',
        'process_mesh': 'process_mesh_execution_time',
        'fem_x': 'fem_x_execution_time',
        'fem_y': 'fem_y_execution_time',
        'fem_z': 'fem_z_execution_time',
        'all': 'loop_time', 'iteration_time': 'loop_time',
        'seconds': 'start_time',
        'percolation_x': 'perc_x', 'perc_x': 'perc_x',
        'percolation_y': 'perc_y', 'perc_y': 'perc_y',
        'percolation_z': 'perc_z', 'perc_z': 'perc_z',
        'E_XX': 'Exx', 'EXX': 'Exx', 'XX': 'Exx',
        'E_YY': 'Eyy', 'EYY': 'Eyy', 'YY': 'Eyy',
        'E_ZZ': 'Ezz', 'EZZ': 'Ezz', 'ZZ': 'Ezz',
        'system_creation_state': 'system_creation_state',
        'shell_thickness': 'shell_thickness',
        'outer_radius': 'outer_radius',
        'thickness': 'thickness', 'disk_thickness': 'thickness',
        'intersections_number': 'intersections_number',
        'Lx': 'Lx',
        'fillers_real_number': 'N_real', 'N_real': 'N_real',
            'disks_number': 'N_real',
        'algorithm': 'task_name', 'task_name': 'task_name',
        'mixing_steps': 'mixing_steps',
        'vertices_number': 'vertices_number',
        'max_attempts': 'max_attempts',
        'tau': 'tau',
        'LOG': 'cpp_log',
        'time': 'time',
        'ar': 'ar',
        'fi_real': 'fi_real',
        'N': 'N',
        'gen_mesh_exe': 'gen_mesh_exe',
        'process_mesh_exe': 'process_mesh_exe',
        'fem_main_exe': 'fem_main_exe',
        'limitation_memory_ratio': 'limitation_memory_ratio',
        'shape': 'shape',
        # i do not remember what does it mean
        # or it does not mean anything useful
        'fi': 'thrash_for_now', 'made': 'thrash_for_now',
        'max': 'thrash_for_now', 'LD_LIBRARY_PATH': 'thrash_for_now',
        'required_settings': 'thrash_for_now', 'memory': 'memory',
    }
    special_cases_keys = set([
        'moduli', 'cpp_polygons_executables', 'taus', 'ars', 'XX:',
    ])

    def list_from_log(self, **kwargs):
        def dict_from_single_entry(entry):
            entry_as_dict = {}
            lines = entry.split('\n')
            for line in lines:
                if not line.split():
                    continue
                else:
                    key = line.split()[0]
                    if '=' in key:
                        value = key.split('=')[1]
                        key = key.split('=')[0]
                    else:
                        value = line.split()[1:]
                        if len(value) == 1:
                            value = value[0]
                    try:
                        value = int(value)
                    except ValueError:
                        try:
                             value = float(value)
                        except:
                             pass
                    except TypeError: # some string usually having many words
                        value = ' '.join(value)
                    if key in self.special_cases_keys:
                        if key == 'moduli':
                            entry_as_dict['Ef'] = value[0]
                            entry_as_dict['Ei'] = value[1]
                            entry_as_dict['Em'] = value[2]
                        elif key in ['taus', 'ars']:
                            entry_as_dict['all_' + key] = value
                        elif key == 'cpp_polygons_executables':
                            pass
                        elif key == 'XX:':
                            entry_as_dict['Exx'] = float(value.split()[0][:-1])
                            entry_as_dict['Eyy'] = float(value.split()[2][:-1])
                            entry_as_dict['Ezz'] = float(value.split()[4][:-1])
                        else:
                            print(key, value)
                    else:
                        try:
                            entry_as_dict[self.unified_keys[key]] = value
                        except KeyError:
                            print('got key error with key', key)
            return entry_as_dict

        def list_from_new_log(log, log_separator):
            entries_as_list = []
            with open(log) as f:
                log_content = f.read()
                if '#'*50 in log_content:
                    raise TypeError('log type is not correct (not new)')
                entries = log_content.split(log_separator)
                for entry in entries:
                    entry_as_dict = dict_from_single_entry(entry)
                    if entry_as_dict.keys():
                        entries_as_list.append(entry_as_dict)
            return entries_as_list

        def list_from_old_log(log):
            entries_as_list = []
            with open(log) as f:
                log_content = f.read()
                if '*'*9 in log_content:
                    raise TypeError('log type is not correct (not old)')
                entry_lines = []
                for line in log_content.split('\n'):
                    if line.startswith('#') and not line[:-1].endswith('#'):
                        continue
                        #algo_name, N_real, tau, ar = [
                        #        line.split()[1],
                        #        int(line.split()[3],
                        #        float(line.split()[5],
                        #        float(line.split()[7],
                        #    ]
                    if line.endswith('#####'):
                        entry_as_dict = dict_from_single_entry(
                            '\n'.join(entry_lines))
                        if entry_as_dict.keys():
                            entries_as_list.append(entry_as_dict)
                        entry_lines = []
                    else:
                        new_line = line.replace('!', '').replace('took ', '')
                        new_line = new_line.strip()
                        # fixing errors:
                        new_line = new_line.replace(
                            'system_reation_state', 'system_creation_state')
                        entry_lines.append(new_line)
            return entries_as_list

        try:
            log_separator = kwargs['log_separator']
            json_name = kwargs['json_name']
            log = kwargs['log']
        except KeyError:
            print('not enough argument in JsonMaker.list_from_new_log')
            return []
        try:
            return list_from_new_log(log, log_separator)
        except TypeError:
            try:
                return list_from_old_log(log)
            except Exception as e:
                print('error in log')
                print(log)
                print(type(e).__name__, e)
                return []
        except Exception as ee:
            print(type(ee).__name__)

    def json_from_logs(self, **kwargs):
        all_logs_content = []
        try:
            for log in kwargs['logs']:
                try:
                    all_logs_content.extend(
                        self.list_from_log(
                            json_name=kwargs['json_name'],
                            log_separator=kwargs['log_separator'],
                            log=log)
                    )
                except FileNotFoundError:
                    print(log, 'not found')
        except KeyError:
            print('not enough argument in JsonMaker.json_from_logs')
            return 0
        try:
            with open(kwargs['json_name'], 'w') as f:
                json.dump(all_logs_content, f, indent=4)
            print(len(all_logs_content), 'entries were written to',
                kwargs['json_name'])
        except KeyError:
            print('not enough argument in JsonMaker.json_from_logs')
            return 0

    def json_from_logs_only_valuable(self, **kwargs):
        valuable_params = set(['fi', 'ar', 'tau', 'L_div_outer_r'])
        moduli =set(['EXX', 'EYY', 'EZZ'])
        select = {'Ef': 232, 'Ei': 4, 'Em': 1.5}
        def special_list_from_single_log(log_name):
            def process_new_log_format(log_content):
                log_as_list = []
                entries = log_content.split('**********')
                for entry in entries:
                    entry_as_dict = dict()
                    lines = entry.split('\n')
                    for line in lines:
                        for key in valuable_params:
                            if line.startswith(key):
                                entry_as_dict[line.split()[0]] = (
                                    float(line.split()[1])
                                )
                    flag_select_satisfied = True
                    for line in lines:
                        for key in select.keys():
                            if (line.startswith(key) and
                                float(line.split()[1]) != float(select[key])):
                                    flag_select_satisfied = False
                                    break
                    if not flag_select_satisfied:
                        continue
                    for line in lines:
                        for key in moduli:
                            if line.startswith(key):
                                new_entry_as_dict = entry_as_dict
                                new_entry_as_dict['axe'] = key[1:]
                                new_entry_as_dict['E'] = float(line.split('=')[1])
                                log_as_list.append(new_entry_as_dict)
                    if 'fi_real' in entry_as_dict.keys():
                        entry_as_dict['fi'] = entry_as_dict['fi_real']
                        del entry_as_dict['fi_real']
                return log_as_list

            def process_old_log_format(log_content):
                def get_dict_from_lines_list(lines_list):
                    entries_list = []
                    entry_as_dict = dict()
                    for line in lines_list:
                        line = line.strip()
                        if line.startswith('!fi'):
                            entry_as_dict['fi'] = float(line.split()[1])
                        elif line.startswith('#') and not line.endswith('#####'):
                            ls = line.split()
                            if len(ls) < 8:
                                ls = line.split('tau')[1].split()
                                entry_as_dict['ar'] = float(ls[2])
                                entry_as_dict['tau'] = float(ls[0])
                            else:
                                entry_as_dict['ar'] = float(ls[7])
                                entry_as_dict['tau'] = float(ls[5])
                        elif line.startswith('L_div_outer_r'):
                            entry_as_dict['L_div_outer_r'] = float(line.split()[1])
                        elif line.startswith('!Lr'):
                            entry_as_dict['L_div_outer_r'] = float(line.split()[1])
                        # select
                        elif line.startswith('!Ef'):
                            if float(line.split()[1]) != float(select['Ef']):
                                return []
                        elif line.startswith('!Ei'):
                            if float(line.split()[1]) != float(select['Ei']):
                                return []
                        elif line.startswith('!Em'):
                            if float(line.split()[1]) != float(select['Em']):
                                return []
                    flag_all_valuable_params_set = True
                    for key in valuable_params:
                        if key not in entry_as_dict.keys():
                            flag_all_valuable_params_set = False
                            print(key)
                    if not flag_all_valuable_params_set:
                        print('not all')
                        return []
                    for line in lines_list:
                        line = line.strip()
                        if (line.startswith('E_XX') or
                            line.startswith('E_YY') or
                            line.startswith('E_ZZ')):
                                modulus = line.split()[1]
                                if modulus == 'None':
                                    continue
                                new_entry_as_dict = entry_as_dict
                                new_entry_as_dict['axe'] = line.split()[0][2:]
                                new_entry_as_dict['E'] = float(modulus)
                                entries_list.append(new_entry_as_dict)
                    return entries_list

                log_as_list = []
                lines_list = []
                for line in log_content.split('\n'):
                    if line.endswith('#######'):
                        if lines_list:
                            log_as_list.extend(
                                get_dict_from_lines_list(lines_list))
                        lines_list = []
                    else:
                        lines_list.append(line)

                return log_as_list

            with open(log_name) as f:
                log_content = f.read()
                if log_content.startswith('**********'):
                    return process_new_log_format(log_content)
                elif log_content.split('\n')[0].endswith('#########'):
                    return process_old_log_format(log_content)
                else:
                    print('unknown log format', log)
                    return []

        all_logs_content = []
        for log in kwargs['logs']:
            got_from_log = special_list_from_single_log(log)
            print(log.split('/')[-1], len(got_from_log))
            all_logs_content.extend(got_from_log)
        with open(kwargs['json_name'], 'w') as f:
            json.dump(all_logs_content, f, indent=4)
        print(len(all_logs_content), 'entries were written to',
            kwargs['json_name'])
