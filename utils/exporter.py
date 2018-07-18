class Exporter:
    def list_to_csv(self, list_to_export, csv_name, csv_separator, ordered_keys):
            exported_number = 0
            entries_to_print = []
            if ordered_keys:
                header = csv_separator.join([*ordered_keys, '\n'])
            else:
                keys = set()
                for entry in list_to_export:
                    keys.update(entry.keys())
                try:
                    keys.remove('_id')
                except:
                    pass
                keys = list(keys)
                header = csv_separator.join([*keys, '\n'])
            for entry in list_to_export:
                if 'EXX' in entry.keys():
                    entries_to_print.append({
                        k: v for k, v in entry.items() if k not in ['EYY', 'EZZ']
                    })
                elif 'EYY' in entry.keys():
                    entries_to_print.append({
                        k: v for k, v in entry.items() if k not in ['EXX', 'EZZ']
                    })
                elif 'EZZ' in entry.keys():
                    entries_to_print.append({
                        k: v for k, v in entry.items() if k not in ['EXX', 'EYY']
                    })
            with open(csv_name, 'w') as f:
                f.write(header)
                for entry in entries_to_print:
                    if ordered_keys:
                        f.write(csv_separator.join([
                            *[str(entry[key]) for key in ordered_keys], '\n'
                        ]))
                    else:
                        out_str = ''
                        for key in keys:
                            if key in entry.keys():
                                out_str += ' ' + str(entry[key])
                        f.write(out_str[1:] + '\n')
                    exported_number += 1
            print('exported {0} entries'.format(exported_number))
            return 0


    def export_json(self, list_to_export, json_out_name):
        import json
        json_out_string = ''
        for entry in list_to_export:
            try:
                del entry['_id']
            except:
                pass
            json_out_string += json.dumps(entry, indent=4) + '\n'
        with open(json_out_name, 'w') as f:
            f.write(json_out_string)
        return 0
    """
    def export_xml(self, xml_out_name): # sudo pip3 install dicttoxml
        print('mongo_export_xml xml_name = {0}'.format(xml_out_name))
        from dicttoxml import dicttoxml
        results_dict = mongo_get_dict(key='time')
        xml_out_string = dicttoxml(results_dict, custom_root='test',
            attr_type=False)
        with open(xml_out_name, 'w') as f:
            f.write(xml_out_string.decode("utf-8"))
        return 0

    """
