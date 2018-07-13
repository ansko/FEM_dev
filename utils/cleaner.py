import os
import shutil


class Cleaner:
    def clean_black_list(self, black_list):
        for fname in black_list:
            if os.path.isdir(fname):
                shutil.rmtree(fname)
            elif fname in os.listdir():
                os.remove(fname)
