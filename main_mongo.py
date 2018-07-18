import os
import pprint
pprint=pprint.PrettyPrinter(indent=4).pprint
import pymongo
from pymongo import MongoClient
import sys
import time

from mongo.mongo_operations import MongoOperations
from utils.exporter import Exporter
from utils.new_log_reader import read_log


#sudo killall mongod
#sudo mongod --rest --httpinterface

#For mongo running on localhost:27017 web address: localhost:28017

#Export collection 'moduli' from db 'fem':
# mongoexport --host "localhost:27017" --db fem --collection moduli --out exported.json --verbose


def main(
    log_names=['py_main_log_2018_Jul_16'],
    separator='**********', database_name='fem', collection_name='results',
    csv_separator=' ', csv_name='test.csv', ordered_keys=['fi_real', 'ar', 'tau']):
        MongoOperations().drop_table(database_name, collection_name)
        for log_name in log_names:
            entries_log_dict = read_log(log_name=log_name, separator=separator)
        MongoOperations().insert(entries_log_dict, drop_old_table=True)
        MongoOperations().pprint()
        Exporter().export_json(
            list_to_export=MongoOperations().get_list(),
            json_out_name='test.json'
        )
        return 0


if __name__ == '__main__':
    main()
