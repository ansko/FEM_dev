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
        valuable_params = set(['fi', 'ar', 'tau', 'L_div_outer_r', 'E'])
        all_logs_content = []
        for log in kwargs['logs']:
            current_log_content = self.list_from_log(
                json_name=kwargs['json_name'],
                log_separator=kwargs['log_separator'],
                log=log)
            for entry in current_log_content:
                flag = True
                short_entry = dict()
                # fi
                if 'fi_real' in entry.keys():
                    short_entry['fi'] = entry['fi_real']
                else:
                    pprint(entry)
                    print('---', log)
                    sys.exit()
                for param in valuable_params:
                    if param not in short_entry.keys():
                        flag = False
                        break
                if flag:
                    all_log_content.append(short_entry)
        with open(kwargs['json_name'], 'w') as f:
            json.dump(all_logs_content, f, indent=4)
        print(len(all_logs_content), 'entries were written to',
            kwargs['json_name'])
