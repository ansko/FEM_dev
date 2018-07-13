import multiprocessing
import os

from utils.watcher import Watcher
from utils.cubic_task import CubicTask


def start_watcher():
    w = Watcher()


def start_task(task_name):
    t = CubicTask(task_name)


def main():
    task_name = 'mc'
    print('main has pid', os.getpid())

    task_process = multiprocessing.Process(target=lambda: start_task(task_name))
    #watcher_process = multiprocessing.Process(target=start_watcher)

    task_process.start()
    #watcher_process.start()

    task_process.join()
    #watcher_process.join()


if __name__ == '__main__':
    main()
