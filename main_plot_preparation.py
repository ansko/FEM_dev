from utils.plot_data_getter import PlotDataGetter


def main_no_perc(json_name, ar, tau, out_fname):
    """
    PlotDataGetter().special_from_json(
        json_name='out.json',
        x_keys=['fi_real'],
        y_keys=['Exx', 'Eyy', 'Ezz'],
        select={
            'ar': ar,
            'tau': tau
        },
        to_ignore={
            'perc_x': 'True',
            'perc_y': 'True',
            'perc_z': 'True'},
        out_fname=out_fname,
        ar=ar,
    )
    """
    #PlotDataGetter().very_special_e_fi(json_name='out.json', ar=ar, tau = tau)
    PlotDataGetter().shortened_e_fi(
        json_name=json_name, ar=ar, tau = tau, out_fname=out_fname)
    return 0


if __name__ == '__main__':
    taus = ['0.5', '1', '1.5', '2', '2.5', '3']
    ars = ['5', '10', '15', '20', '25', '50']
    for tau in taus:#['1']:
        for ar in ars:#['5']:
            main_no_perc(json_name='filtered_x7_shortened.json', ar=ar, tau=tau,
                out_fname='gnuplot/data_to_plot/ar_{0}_tau_{1}'.format(ar, tau))
