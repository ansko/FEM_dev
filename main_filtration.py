import json
import os
import pprint
pprint=pprint.PrettyPrinter(indent=4).pprint
import sys

from utils.analyzer import Analyzer


# general settings
ars = [5, 10, 15, 20, 50]
taus = [0.5, 1, 1.5, 2, 2.5, 3]

# special settings
directory = 'gnuplot/data_to_plot/'
deviation_limit = 0.05
fi_limit = 0.1


def approximate_linear(xs, ys):
    # y = b + a*x
    sum_x = 0
    sum_y = 0
    sum_xy = 0
    sum_xx = 0
    n = len(xs)
    if n == 0:
        return (0, 0)
    for i in range(len(xs)):
        sum_x += xs[i]
        sum_y += ys[i]
        sum_xy += xs[i] * ys[i]
        sum_xx += xs[i]**2
    try:
        a = (n * sum_xy - sum_x * sum_y) / (n * sum_xx - sum_x**2)
        b = (sum_y - a * sum_x) / n
    except ZeroDivisionError:
        return (0, 0)
    return (a, b)


def get_slopes(json_name):
    constants = {str(ar): {} for ar in ars}
    data = json.load(open(json_name))
    for ar in ars:
        for tau in taus:
            #data_fname = directory + fname_template.format(ar, tau)
            #if fname_template.format(ar, tau) not in os.listdir(directory):
            #    continue
            xs = [] # fi
            ys = [] # E
            for entry in data:
                if float(ar) != float(entry['ar']):
                    continue
                if float(tau) != float(entry['tau']):
                    continue
                fi = float(entry['fi'])
                if fi > fi_limit:
                    continue
                xs.append(fi)
                ys.append(float(entry['E']))
            constants[str(ar)][str(tau)] = approximate_linear(xs, ys)
    return constants


def find_strange(in_json_name):
    def make_out_name(in_name):
        if (in_name.startswith('filtered_') and not
            in_json_name.startswith('filtered_x')):
                return 'filtered_x2_' + in_name[9:]
        elif in_json_name.startswith('filtered_x'):
            ls = in_name.split('_')
            ls[1] = 'x' + str(int(ls[1][1:]) + 1)
            return '_'.join(ls)
        else:
            return 'filtered_' + in_name
    constants = get_slopes(in_json_name)
    data = json.load(open(in_json_name))
    filtered_data = []
    for entry in data:
        E_fem = float(entry['E'])
        fi = float(entry['fi'])
        if fi > fi_limit:
            continue
        ar_key = str(int(entry['ar']))
        tau_key = str(entry['tau'])
        if tau_key.endswith('0'):
            tau_key = tau_key[:-2]
        try:
            # E = a * fi + b
            a, b = constants[ar_key][tau_key]
            E_approximated = a * fi + b
            deviation = abs(E_fem - E_approximated) / (E_fem + E_approximated) * 2
            if deviation > deviation_limit:
                continue
            print(deviation)
            filtered_data.append(entry)
        except KeyError as e:
            print('non-critical error with key', e)
            continue
    with open(make_out_name(in_json_name), 'w') as f:
        json.dump(filtered_data, f, indent=4)
    return len(filtered_data)


if __name__ == '__main__':
    fname = 'shortened.json'
    a = find_strange(in_json_name=fname)
    print(a)
    b = find_strange(in_json_name='filtered_' + fname)
    print(b)
    if a != b:
        for i in range(2, 10):
            c = find_strange(in_json_name='filtered_x{}_'.format(i) + fname)
            if c == b:
                break
            b = c
            print(c)
