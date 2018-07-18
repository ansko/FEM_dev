from utils.json_maker import JsonMaker


def main():
    logs_dev_dir = '/home/anton/AspALL/Projects/FEM_RELEASE_BACKUP/logs_dev/'
    logs_dir = '/home/anton/AspALL/Projects/FEM_RELEASE_BACKUP/logs/'
    logs_ar50_dir = '/home/anton/AspALL/Projects/FEM_RELEASE_BACKUP/logs_ar_50/'
    logs_dev = [logs_dev_dir + fname for fname in [
        'py_main_log_2018_Jul_11',
        'py_main_log_2018_Jul_12',
        'py_main_log_2018_Jul_13',
        'py_main_log_2018_Jul_16'
    ]]
    logs_old = [logs_dir + fname for fname in [
        'py_main_log_2018_Jul_2_232_4_1.5',
        'py_main_log_2018_Jul_3_232_4_1.5',
        'py_main_log_2018_Jul_3_232_4_1.5_n1',
        'py_main_log_2018_Jul_5_232_4_1.5',
        'py_main_log_2018_Jul_6_232_4_1.5',
        'py_main_log_2018_Jul_6_232_4_1.5_n1',
        'py_main_log_2018_Jul_9',
        'py_main_log_2018_Jul_10',
        'py_main_log_2018_Jun_27_232_4_1.5',
        'py_main_log_2018_Jun_27_232_4_1.5_small',
        'py_main_log_2018_Jun_29_232_4_1.5'
    ]]
    logs_ar50 = [logs_ar50_dir + fname for fname in [
        'py_main_log_2018_Jul_9',
        'py_main_log_2018_Jul_10_1',
        'py_main_log_2018_Jul_10_2',
    ]]
    logs_all = [*logs_dev, *logs_old, *logs_ar50]
    """
    JsonMaker().json_from_logs(
        json_name='out.json',
        logs=logs_all,
        log_separator='**********'
    )
    """
    JsonMaker().json_from_logs_only_valuable(
        json_name='shortened.json',
        logs=logs_all,
        log_separator='**********'
    )
    return 0


if __name__ == '__main__':
    main()
