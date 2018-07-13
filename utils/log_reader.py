import math
import pprint
pprint=pprint.PrettyPrinter(indent=4).pprint


def read_log(log_name):
    print('read_log log_name = {0}'.format(log_name))
    cell_lengths = []
    moduli = []
    log_entries = {} # {str(seconds): {parameter: value}}
    is_first = True
    with open(log_name) as f:
        for line in f:
            if line.startswith('#') and line.endswith('#\n'): # title of log entry
                if not is_first: # append last read parameters
                    fi_calc = (N * vertices_number * thickness *
                                   0.5 * outer_radius**2 *
                                       math.sin(2*math.pi/vertices_number))
                    fi_calc_circular = N * math.pi * outer_radius**2 * thickness
                    if len(cell_lengths) == 1:
                        fi_calc /= cell_lengths[0]**3
                        fi_calc_circular /= cell_lengths[0]**3
                    elif len(cell_lengths) == 3:
                        fi_calc /= (cell_lengths[0] *
                                    cell_lengths[1] * cell_lengths[2])
                        fi_calc_circular /= (cell_lengths[0] *
                                    cell_lengths[1] * cell_lengths[2])

                    else:
                        print('error in cell lengths!', len(cell_lengths))
                        import sys
                        sys.exit()
                    log_entries[seconds_str] = {
                        'algorithm': algorithm, # mc / mixing
                        'N': N, # real(?) number of particles
                        'tau': tau, # shell_thickness / thickness
                        'ar': ar, # 2 * outer_radius/thickness
                        'fi_log': fi, # fi from title of entry
                        'L_to_R_ratio': L_to_R_ratio, # Lx (Ly, Lz) / outer_radius
                        'shell_thickness': shell_thickness, # should be equal to
                            # thickness * tau
                        'geo_fname': geo_fname, # name of file with structure
                        'disks_number': disks_number, # should be equal to N
                        'LOG': LOG, # cpp log name
                        'max_attempts': max_attempts, # maximum number of attempts
                             # in the mc algorithm
                        'vertices_number': vertices_number, # number of vertices
                             # in the cylinder's base
                        'thickness': thickness, # thickness (height) of a cylinder
                        'mixing_steps': mixing_steps, # number of mixing steps in
                            # mixing algorithm
                        'outer_radius': outer_radius, # radius of outer 
                            # circumference for the cylinder's base polygon
                        'Ls': cell_lengths, # sizes of a cell along x (and y, z)
                        'system_creation_state': system_creation_state, # True if
                            # real particles number equals to the desired number
                        'made_attempts': made_attempts, # real attempts number
                            # (may be less than (max) in mc algorithms
                        'percolation_x': percolation_x, # whether percolation
                            # along x is achieved
                        'percolation_y': percolation_y,     # y
                        'percolation_z': percolation_z,     # z
                        'moduli': moduli, # list of Young's moduli, Ezz may be
                            # corrupted, so its length == (2 or 3)
                        'cpp_time': cpp_time, # performance measurements
                        'gen_mesh_time': gen_mesh_time,         # -||-
                        'process_mesh_time': process_mesh_time, # -||-
                        'fem_main_x_time': fem_main_x_time,     # -||-
                        'fem_main_y_time': fem_main_y_time,     # -||-
                        'fem_main_z_time': fem_main_z_time,     # -||-
                        'fi_calc': fi_calc, # should be about fi_log, but is not...
                        'fi_calc_circular': fi_calc_circular # just a check
                    }
                    cell_lengths = []
                    moduli = []
                else:
                    is_first = False
                seconds_str = line.split()[1]
                seconds = int(seconds_str)
            elif line.startswith('#'):
                algorithm = line.split()[1]
                N = int(line.split()[3])
                tau = float(line.split()[5])
                ar = float(line.split()[7])
            elif line.startswith('!fi'):
                fi = float(line.split()[1])
            elif line.startswith('!Lr'):
                L_to_R_ratio = float(line.split()[1])
            elif line.split()[0] == 'shell_thickness':
                shell_thickness = float(line.split()[1])
            elif line.split()[0] == 'geo_fname':
                geo_fname = line.split()[1]
            elif line.split()[0] == 'disks_number':
                disks_number = int(line.split()[1])
            elif line.split()[0] == 'LOG':
                LOG = line.split()[1]
            elif line.split()[0] == 'max_attempts':
                max_attempts = int(line.split()[1])
            elif line.split()[0] == 'vertices_number':
                vertices_number = int(line.split()[1])
            elif line.split()[0] == 'thickness':
                thickness = float(line.split()[1])
            elif line.split()[0] == 'mixing_steps':
                mixing_steps = int(line.split()[1])
            elif line.split()[0] == 'outer_radius':
                outer_radius = float(line.split()[1])
            elif line.split()[0] == 'Lx':
                cell_lengths.append(float(line.split()[1]))
            elif line.split()[0] == 'Ly':
                cell_lengths.append(float(line.split()[1]))
            elif line.split()[0] == 'Lz':
                cell_lengths.append(float(line.split()[1]))
            elif line.split()[0] == 'system_reation_state': # -> creation
                system_creation_state = bool(line.split()[1])
            elif line.split()[0] == 'made' and line.split()[1] == 'attempts':
                made_attempts = int(line.split()[2])
            elif line.split()[0] == 'percolation_x':
                percolation_x = True if line.split()[1] == 'True' else 'False'
            elif line.split()[0] == 'percolation_y':
                percolation_y = True if line.split()[1] == 'True' else 'False'
            elif line.split()[0] == 'percolation_z':
                percolation_z = True if line.split()[1] == 'True' else 'False'
            elif line.split()[0] == 'E_XX':
                moduli.append((line.split()[1]))
            elif line.split()[0] == 'E_YY':
                moduli.append(float(line.split()[1]))
            elif line.split()[0] == 'E_ZZ' and line.split()[1] != 'None':
                moduli.append(float(line.split()[1]))
            elif line.split()[0] == 'fillers_real_number':
                fillers_real_number = int(line.split()[1])
            elif line.split()[0] == 'max' and line.split()[1] == 'attempts':
                max_attemtps = int(line.split()[2])
            elif line.split()[0] == 'algorithm':
                algorithm_ = line.split()[1]
            elif line.split()[0] == 'intersections_number':
                intersections_number = int(line.split()[1])
            elif line.split()[0] == 'fillers_real_number':
                fillers_real_number = int(line.split()[1])
            elif line.startswith('! all took'):
                loop_time = float(line.split()[3])
            elif line.startswith('!     cpp took '):
                cpp_time = float(line.split()[3])
            elif line.startswith('!     gen_mesh took'):
                gen_mesh_time = float(line.split()[3])
            elif line.startswith('!     process_mesh'):
                process_mesh_time = float(line.split()[3])
            elif line.startswith('!     fem_x'):
                fem_main_x_time = float(line.split()[3])
            elif line.startswith('!     fem_y'):
                fem_main_y_time = float(line.split()[3])
            elif line.startswith('!     fem_z'):
                fem_main_z_time = float(line.split()[3])
    print('read {0} log entries'.format(len(log_entries)))
    return log_entries


if __name__ == '__main__':
    log_name = 'py_main_log_2018_Jun_26'
    log_entries = read_log(log_name)
    pprint(log_entries)
