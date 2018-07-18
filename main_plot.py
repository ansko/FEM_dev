import json
import matplotlib
import matplotlib.pyplot as plt


class PlotterJson:
    def __init__(self, min_points_number):
        self.min_points_number = min_points_number

    def get_data(self, json_fname, ar=None, tau=None, axe=None):
        with open(json_fname) as f:
            return json.load(f)

    def plot_data_entry(self, data_entry, out_fname):
        for value in data:
            csv_names.add(entry['csv_name'])
            ars.add(entry['ar'])
            taus.add(entry['tau'])
            axis.add(entry['axe'])

    def util_plot(x, y, title, legend, figname):
        matplotlib.pyplot.legend([tmp], [legend], loc="upper left")
        print(figname)
        fig.savefig(figname)
        return 0


def main():
        plotter = PlotterJson(min_points_number=3)
        data = plotter.get_data(json_fname='test.json')
        for entry in data:
            out_fname = 'test.jpg'
            plotter.plot_data_entry(entry, out_fname=out_fname)


if __name__ == '__main__':
    main()
