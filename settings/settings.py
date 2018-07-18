class Settings(dict):
    def __init__(self):
        # hardware
        self['memory'] = 8 * 1024 ** 3 # 8GB
        self['limitation_memory_ratio'] = 0.3
        # general physical parameters
        self['L_div_outer_r'] = 5
        self['moduli'] = [232, 4, 1.5]
        self['taus'] = [0.5, 1, 1.5, 2, 2.5, 3]
        self['ars'] = [5, 10, 15, 20, 25]
        self['disk_thickness'] = 0.1

        # cpp
        self['cpp_directory'] = 'RELEASE_CppPolygons/'
        self['cpp_settings_fname'] = 'settings_cpp'
        self['mixing_steps'] = 1000
        self['max_attempts'] = 1000
        self['vertices_number'] = 6
        self['required_settings'] = {
            'any': {'Lx', 'thickness', 'shell_thickness', 'outer_radius',
                    'vertices_number', 'disks_number', 'LOG'},
            'mc':  {'max_attempts', },
            'mix': {'mixing_steps', }
        }
        default_settings = {
            'mc':{
                'Lx': 5,
                'thickness': 0.1,
                'shell_thickness': 0.1,
                'outer_radius': 0.5,
                'vertices_number': 6,
                'disks_number': 1,
                'LOG': 'from_py',
                'max_attempts': 1000,
                'shape': 'pc'
            },
            'mix': {
                'Lx': 5,
                'thickness': 0.1,
                'shell_thickness': 0.1,
                'outer_radius': 0.5,
                'vertices_number': 6,
                'disks_number': 1,
                'LOG': 'from_py',
                'mixing_steps': 1000,
                'shape': 'pc'
            }
        }
        self['cpp_polygons_executables'] = {
            'mc': 'MC_exfoliation',
            'mix': 'mixing'
        }

        # where FEM exe-s are stored
        self['FEMFolder'] = '/home/anton/FEMFolder/'
        self['gen_mesh_exe'] = 'gen_mesh.x'
        self['process_mesh_exe'] = 'processMesh.x'
        self['fem_main_exe'] = 'FEManton3.o'

        # task watching
        self['period'] = 3
        self['time_limits'] = {
            'MC_exfoliation': 1000,
            'FEManton3.o': 1000,
            'gen_mesh.x': 1000,
            'processMesh.x': 100
        }
