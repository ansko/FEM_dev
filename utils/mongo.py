# python3 mongo_test.py

import os
import pprint
pprint=pprint.PrettyPrinter(indent=4).pprint
import pymongo
from pymongo import MongoClient
import sys
import time

from log_reader import read_log


"""
 --- Commands ---
    sudo mongod - start mongo
        --rest - Enables the simple REST API.
            --httpinterface
        --shutdown

    sudo service mongod stop
    sudo killall mongod


 --- Settings ---
    For mongo running on localhost:27017 
        web address: localhost:28017
        export collection 'moduli' from db 'fem':
            mongoexport --host "localhost:27017" --db fem --collection moduli --out exported.json --verbose

"""

mongo_address = 'localhost'
mongo_port = 27017
db_fem_name = 'fem'
collection_moduli_name = 'moduli'

Ei = '30'
Em = '4'
""" ---------------- """

"""
log_name = '_'.join(['py_main_log', time.asctime().split()[4],
    time.asctime().split()[1], time.asctime().split()[2]])
"""
log_name = 'py_main_log_2018_Jun_27'
csv_name = 'one.csv'


def mongo_drop_table(db_name, collection_name):
    print('mongo_drop_table db = {0} coll={1}'.format(db_name, collection_name))
    client = MongoClient(mongo_address, mongo_port)
    db_from = client[db_name]
    db_from.drop_collection(collection_name)
    return 0


def mongo_insert(entries, drop_old_table=False):
    print('mongo_insert {0}'.format(len(entries)))
    if drop_old_table:
        mongo_drop_table(db_fem_name, 'results')
    client = MongoClient(mongo_address, mongo_port)
    db_fem = client[db_fem_name]
    results = db_fem.results
    for key, entry in entries.items():
        entry['time'] = key
        result_id = results.insert_one(entry).inserted_id
    return 0


def mongo_pprint():
    print('mongo_pprint')
    results_dict = mongo_get_dict('time')
    pprint(results_dict)
    print('\nnumber of entries: {0}'.format(results_dict))
    return 0


def mongo_export_json(json_out_name):
    print('mongo_export_json json_name = {0}'.format(json_out_name))
    import json
    results_dict = mongo_get_dict(key='time')
    json_out_string = json.dumps(results_dict, indent=4)
    with open(json_out_name, 'w') as f:
        f.write(json_out_string)
    return 0


def mongo_export_xml(xml_out_name): # sudo pip3 install dicttoxml
    print('mongo_export_xml xml_name = {0}'.format(xml_out_name))
    from dicttoxml import dicttoxml
    results_dict = mongo_get_dict(key='time')
    xml_out_string = dicttoxml(results_dict, custom_root='test', attr_type=False)
    with open(xml_out_name, 'w') as f:
        f.write(xml_out_string.decode("utf-8"))
    return 0


def mongo_get_dict(key='time'):
    print('mongo_get_dict, key={0}'.format(key))
    client = MongoClient(mongo_address, mongo_port)
    db_fem = client[db_fem_name]
    results = db_fem.results
    results_dict = dict()
    for result in results.find():
        current_result_dict = dict(result)
        """
            '_id': ObjectId('5b337b50e389a23b2916754a') changes into
            '_id':  '5b337b50e389a23b2916754a' by making str() of it
        """
        current_result_dict['_id'] = str(current_result_dict['_id'])
        results_dict[key + '_' + result[key]] = current_result_dict
    return results_dict


def mongo_export_raws():
    """
        Create a seria of logs with names rawdata_PARAM1NAME_PARAM1VALUE_...
    """
    print('mongo_export_raws')
    valuable_params=['tau', 'ar'] # only 2!
    valuable_params_values = {param: set() for param in valuable_params}
    results_dict = mongo_get_dict(key='time')
    for value in results_dict.values():
        for key in valuable_params:
            valuable_params_values[key].add(value[key])
    #pprint(valuable_params_values)

    for one in valuable_params_values[valuable_params[0]]:
        for two in valuable_params_values[valuable_params[1]]:
            name = '_'.join(['rawdata', valuable_params[0], str(one),
                                        valuable_params[1], str(two)])
            all_values = dict() # fi: [E, perc]
            for entry in results_dict.values():
                if (entry[valuable_params[0]] == one and
                    entry[valuable_params[1]] == two):
                        fi = entry['fi_calc']
                        Exx = entry['moduli'][0]
                        pxx = 1 if entry['percolation_x'] == 'True' else 0
                        Eyy = entry['moduli'][1]
                        pyy = 1 if entry['percolation_x'] == 'True' else 0
                        all_values[fi] = [
                            [Exx, pxx],
                            [Eyy, pyy]
                        ]
                        if len(entry['moduli']) == 3:
                            all_values[fi].append([
                                entry['moduli'][0],
                                1 if entry['percolation_x'] == 'True' else 0
                            ])
            with open(name, 'w') as f:
                f.write('fi E_axe perc_along_axe\n')
                for key in sorted(all_values.keys()):
                    for value in all_values[key]:
                        f.write(' '.join([str(key), 
                                          str(value[0]), str(value[1]),
                                          '\n']))
    return 0


def mongo_export_csv(results_dict, csv_name, sep=' '):
    print('mongo_export_csv csv_name = {0}, sep = "{1}"'.format(csv_name, sep))
    #results_dict = mongo_get_dict(key='time')
    axis = ['XX', 'YY', 'ZZ']
    exported_number = 0
    with open(csv_name, 'w') as f:
        for time, value in results_dict.items():
            fi = str(value['fi_calc'])
            ar = str(value['ar'])
            moduli = value['moduli']
            percolations = [
                value['percolation_x'], value['percolation_y'],
                value['percolation_z']
            ]
            tau = str(value['tau'])
            for idx in range(len(moduli)):
                exported_number += 1
                f.write(sep.join(['time', time, 'fi', fi, 'ar', ar, 'tau', tau,
                                  axis[idx], str(moduli[idx]),
                                  str(percolations[idx]), '\n']))
    print('exported {0} entries'.format(exported_number))
    return 0
        

def main():
    """
    if log_name not in os.listdir():
        print('no log with specified name in folder!')
        print(log_name)
        print('candidates are:')
        for fname in os.listdir():
            if 'py_main' in fname:
                print(fname)
        return 0
    """
#
    tmp_log_name = '/home/anton/AspALL/Projects/FEM_RELEASE_BACKUP/logs/'
    tmp_log_name += 'py_main_log_2018_Jun_27_232_4_1.5'

    if len(sys.argv) > 1:
        log_name = sys.argv[1]
    if len(sys.argv) > 2:
        csv_name = sys.argv[2]
#

    entries_log_dict = read_log('py_main_log_2018_Jul_3') # log_name
    #entries_mongo_dict = mongo_get_dict()
    #pprint(entries_mongo_dict)
    #mongo_insert(entries_log_dict, drop_old_table=True)
    #mongo_pprint()
    #mongo_export_json('example.json')
    #mongo_export_xml('example.xml')
#    mongo_export_raws()
    mongo_export_csv(entries_log_dict, 'jul4.csv') # csv_name
    return 0


if __name__ == '__main__':
    main()

"""
mongo
>show dbs
>use test_database
"""
