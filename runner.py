import os
import resource
import shutil
import subprocess


geo_fname = '3.geo'
input_file = 'input_XX.txt'
mem_limit = 8 * 1024**3 * 0.3

fem_env = os.environ
fem_env['LD_LIBRARY_PATH'] = ':'.join(['/home/anton/FEMFolder3/libs',
    '/home/anton/FEMFolder3/my_libs'])


def call_gen():
    code = subprocess.call(['/home/anton/FEMFolder3/gen_mesh.x',
        geo_fname, '0.15', '2', '2'],
        env=fem_env)
    shutil.move('generated.vol', 'out.mesh')


def call_process():
    code = subprocess.call(['/home/anton/FEMFolder3/processMesh.x'],
        env=fem_env, preexec_fn=lambda: resource.setrlimit(resource.RLIMIT_AS,
            (mem_limit, mem_limit)))


def call_main():
    code = subprocess.call(['/home/anton/FEMFolder3/FEManton3.o', input_file],
        env=fem_env)


def clean():
    for fname in ('out.mesh'):
        if fname in os.listdir():
            os.remove(fname)


if __name__ == '__main__':
    functions = {'g': call_gen, 'p': call_process, 'm': call_main, 'clean': clean}
    while True:
        action = input('enter next action: ')
        print(functions[action]())
