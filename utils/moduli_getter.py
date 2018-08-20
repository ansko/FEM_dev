class ModuliGetter:
    """
    Class is made to read files produced by FEMmain. It forms file name
    using template string and axe. Return value: {'axe', E_axe for axe in axis}
    """
    def get_moduli(self, fname_template, axis):
        moduli = dict()
        # "Pseudo" moduli, not real Young's moduli: stress_axe / strain_axe ratios
        for axe in axis:
            stress = None
            strain = None
            try:
                with open(fname_template.format(axe)) as f:
                    for idx, line in enumerate(f):
                        if idx == 14:
                            if axe == 'XX':
                                strain = float(line.split()[0])
                                stress = float(line.split()[9])
                            elif axe == 'YY':
                                strain = float(line.split()[4])
                                stress = float(line.split()[13])
                            elif axe == 'ZZ':
                                strain = float(line.split()[8])
                                stress = float(line.split()[17])
                            else:
                                print('error in fem results parsing!')
                                return -1
                moduli[axe] = stress / strain
            except ZeroDivisionError:
                # For some (unknown for me) reason fem task may result
                # in zero results both for strain and stress.
                pass
            except FileNotFoundError:
                # This happens when fem_main.exe terminated with any error
                pass
        return moduli
