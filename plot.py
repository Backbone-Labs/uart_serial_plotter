import pyqtgraph as pg
import numpy as np
from PyQt5.QtWidgets import QGraphicsView


class Plot(object):
    def __init__(self, header=None, data=None):

        self.traces = dict()
        self.data = dict()
        self.trace_names = []
        self.canvas = pg.PlotWidget()
        self.plot = None
        self.canvas.showGrid(x=True, y=True)
        self.canvas.getAxis('left').setTextPen('w')
        self.canvas.getAxis('bottom').setTextPen('w')
        self.plot_item = self.canvas.getPlotItem()

        if header:
            self.set_header(header)
        if data:
            self.set_data(data)

        self.legend = self.canvas.addLegend()

    def get_pen(self, index):
        COLORS = [
            # white
            (255, 255, 255),
            # red salsa
            (255, 53, 78),
            # Neon Green
            (31, 255, 15),
            # Picton Blue
            (68, 204, 255),
            # Neon yellow
            (255, 240, 31),
            # Neon Pink
            (255, 68, 204),
            # Neon orange
            (247, 149, 72),
        ]

        return pg.mkPen(index, len(self.trace_names))
        # return pg.mkPen(COLORS[index % len(COLORS)])

    def set_header(self, header_names):
        self.legend.clear()
        self.trace_names = header_names
        for i, name in enumerate(self.trace_names):
            if name in self.traces:
                pass
            else:
                self.traces[name] = self.canvas.plot(
                    pen=self.get_pen(i),
                    # (i, len(self.trace_names)), 
                    name=name
                )

    def update_data(self, data):
        for name in self.trace_names:
            # initialize the data for this trace
            if name not in self.data:
                self.data[name] = {"x": [0], "y": [0]}

        for row in data:
            time = row[0]
            # skip the first value (since we assume it is time)
            for i in range(1, len(self.trace_names)):
                self.data[self.trace_names[i]]["x"].append(time)
                self.data[self.trace_names[i]]["y"].append(row[i])

        # now actually plot the data
        for i, name in enumerate(self.trace_names[1:]):
            self.set_plotdata(name, self.data[name]["x"], self.data[name]["y"])

    def set_plotdata(self, name, data_x, data_y):
        if name in self.traces:
            self.traces[name].setData(data_x, data_y)
        else:
            self.traces[name] = self.canvas.plot(
                pen=self.get_pen(len(self.trace_names)),
                # pen=(len(self.trace_names), len(self.trace_names)), 
                name=name
            )
