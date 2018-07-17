import ast
from functools import reduce
import pprint
pprint=pprint.PrettyPrinter(indent=4).pprint
import sys


class PlotDataGetter:
    def special_from_json(self, **kwargs):
        import json
        data_to_write = {}
        try:
            data = json.load(open(kwargs['json_name']))
            for entry in data:
                flag_to_write = True
                for key in kwargs['to_ignore'].keys():
                    if entry[key] == kwargs['to_ignore'][key]:
                        flag_to_write = False
                        break
                for key in kwargs['select'].keys():
                    try:
                        if entry[key] != kwargs['select'][key]:
                            flag_to_write = False
                            break
                    except:
                        continue
                if flag_to_write:
                    x_value = None
                    y_value = []
                    if 'fi_real' in entry.keys():
                        x_value = entry['fi_real']
                    elif ('outer_radius' in entry.keys() and
                        'thickness' in entry.keys()):
                            Lx = entry['Lx']
                            try:
                                Ly = entry['Ly']
                            except:
                                Ly = Lx
                            try:
                                Lz = entry['Lz']
                            except:
                                Lz = Lx
                            x_value = (0.5 * entry['outer_radius']**2 *
                                entry['thickness'] * entry['N_real'] /
                                Lx / Ly / Lz)
                    try:
                        y_value.append(float(entry['Exx']))
                    except (ValueError, KeyError):
                        pass
                    try:
                        y_value.append(float(entry['Eyy']))
                    except (ValueError, KeyError):
                        pass
                    try:
                        y_value.append(float(entry['Ezz']))
                    except (ValueError, KeyError):
                        pass
                    if not None in (x_value, y_value):
                        if x_value in data_to_write.keys():
                            data_to_write[x_value].extend(y_value)
                        else:
                            data_to_write[x_value] = y_value
        except KeyError:
            print('not enough parameters in PlotDataGetter.from_json')
            return 0
        data_to_write = {k: v for k, v in data_to_write.items() if v}
        for key in data_to_write.keys():
            data_to_write[key] = reduce(
                lambda x, y: x + y, data_to_write[key]) / len(data_to_write[key])
        #pprint(data_to_write)
        with open(kwargs['out_fname'], 'w') as f:
            for key in sorted(data_to_write.keys()):
                f.write(str(key) + ' ' + str(data_to_write[key]) + '\n')
        return 0

    def special_from_json_e_fi(self, **kwargs):
        import json
        data_to_write = {}
        data = json.load(open(kwargs['json_name']))
        for entry in data:
            y_value = []
            x_value = None
            try:
                x_value = entry['fi_real']
            except KeyError:
                try:
                    x_value = (0.5 * entry['outer_radius'] * entry['thickness'] *
                        entry['vertices_number'] * entry['N_real'] /
                        entry['Lx']**3)
                except KeyError:
                    try:
                        geo_fname = entry['geo_fname'].split('/')[-1].split('.')[0]
                        entry['tau'] = float(geo_fname.split('_')[4])
                        entry['ar'] = float(geo_fname.split('_')[8])
                        entry['L_div_outer_r'] = float(geo_fname.split('_')[6])
                        Lx = float(entry['Lx'])
                        outer_radius = Lx / L_div_outer_r
                        x_value = (0.5 * outer_radius * entry['thickness'] *
                            entry['vertices_number'] * entry['N_real'] /
                            entry['Lx']**3)
                    except KeyError:
                        pass
            try:
                y_value.append(float(entry['Exx']))
            except (KeyError, ValueError):
                pass
            try:
                y_value.append(float(entry['Eyy']))
            except (KeyError, ValueError):
                pass
            try:
                y_value.append(float(entry['Ezz']))
            except (KeyError, ValueError):
                pass
            try:
                for key in kwargs['select'].keys():
                    assert float(entry[key]) == float(kwargs['select'][key])
            except (KeyError, AssertionError):
                continue
            if x_value is None:
                continue
            try:
                if x_value in data_to_write.keys():
                    data_to_write[x_value].extend(y_value)
                else:
                    data_to_write[x_value] = y_value
            except UnboundLocalError:
                pass
        data_to_write = {k: v for k, v in data_to_write.items() if v}
        for key in data_to_write.keys():
            data_to_write[key] = reduce(
                lambda x, y: x + y, data_to_write[key]) / len(data_to_write[key])
        #print(kwargs['select'])
        pprint(data_to_write)
        #with open(kwargs['out_fname'], 'w') as f:
        #    for key in sorted(data_to_write.keys()):
        #        f.write(str(key) + ' ' + str(data_to_write[key]) + '\n')
        return 0

    def very_special_e_fi(self, json_name, ar, tau):
        import json
        data_to_write = {}
        data = json.load(open(json_name))

        print('***')
        ar_ok = 0
        tau_ok = 0
        fi_ok = 0
        e_ok = 0

        for entry in data:
            if 'ar' in entry.keys():
                if float(ar) != float(entry['ar']):
                    continue
                ar_ok += 1
            elif 'geo_fname' in entry.keys():
                entry_ar = entry['geo_fname'].split('/')[-1].split('.')[0]
                entry_ar = entry_ar.split('_')
                found = False
                for idx, el in enumerate(entry_ar):
                    if el == 'ar':
                        found = True
                        break
                if not found:
                    continue
                entry_ar = entry_ar[idx+1]
                if float(entry_ar) != float(ar):
                    #print('|'.join(['"', str(entry_ar), str(ar), '"']))
                    continue
                ar_ok += 1
            elif len(ast.literal_eval(entry['all_ars'])) == 1:
                if float(ar) != float(ast.literal_eval(entry['all_ars'])[0]):
                    continue
                ar_ok += 1
            else:
                print('can not find ar')
                pprint(entry)
                continue


            if 'tau' in entry.keys():
                if float(tau) != float(entry['tau']):
                    continue
                tau_ok += 1
            elif 'shell_thickness' in entry.keys():
                entry_sh = float(entry['shell_thickness'])
                entry_th = float(entry['thickness'])
                entry_tau = float(str(entry_sh / entry_th)[0:3])
                if float(tau) != float(entry_tau):
                    continue
                tau_ok += 1
            else:
                continue


            fi = None
            es = []
            if 'fi_real' in entry.keys():
                fi = entry['fi_real']
                fi_ok += 1
            elif 'outer_radius' in entry.keys():
                fi = (0.5 * entry['outer_radius']**2 * entry['thickness'] *
                    entry['vertices_number'] * entry['N_real'] / entry['Lx']**3)
                fi_ok += 1
            elif 'L_div_outer_r' in entry.keys() and 'Lx' in entry.keys():
                r = entry['Lx'] / entry['L_div_outer_r']
                fi = (0.5 * r**2 * entry['thickness'] *
                    entry['vertices_number'] * entry['N_real'] / entry['Lx']**3)
                fi_ok += 1
            else:
                continue

            if 'Exx' in entry.keys() and entry['Exx'] != 'None':
                es.append(float(entry['Exx']))
                e_ok += 1
            if 'Eyy' in entry.keys() and entry['Eyy'] != 'None':
                es.append(float(entry['Eyy']))
                e_ok += 1
            if 'Ezz' in entry.keys() and entry['Ezz'] != 'None':
                es.append(float(entry['Ezz']))
                e_ok += 1
            if fi is None:
                continue
            if fi in data_to_write.keys():
                data_to_write[fi].extend(es)
            else:
                data_to_write[fi] = es
        if len(data_to_write) < 3:
            return 0
        data_to_write = {k: v for k, v in data_to_write.items() if v}
        for key in data_to_write.keys():
            data_to_write[key] = reduce(
                lambda x, y: x + y, data_to_write[key]) / len(data_to_write[key])
        with open('data_to_plot/ar_{0}_tau_{1}'.format(ar, tau), 'w') as f:
            for key in sorted(data_to_write.keys()):
                f.write(str(key) + ' ' + str(data_to_write[key]) + '\n')
        return 0
