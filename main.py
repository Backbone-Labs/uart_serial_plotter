#!/usr/bin/python
import sys

from multiprocessing import Process, Queue

from main_window import MainWindow
from PyQt5.QtWidgets import QApplication
from PyQt5 import QtCore
from PyQt5 import QtGui

import re
from ansi2html import Ansi2HTMLConverter


def escape_ansi(line):
    ansi_escape = re.compile(r"(?:\x1B[@-_]|[\x80-\x9F])[0-?]*[ -/]*[@-~]")
    return ansi_escape.sub("", str(line))


import signal
import serial

signal.signal(signal.SIGINT, signal.SIG_DFL)

serial_port = None
current_port = None
current_baudrate = None

app = QApplication(sys.argv)
window = None


def reopen_serial_port():
    global serial_port
    global current_port
    global current_baudrate
    global window

    # Close if already open
    if serial_port:
        serial_port.close()

    # Open serial_port
    serial_port = serial.Serial()
    serial_port.port = current_port
    serial_port.baudrate = current_baudrate
    # Disable hardware flow control
    serial_port.setRTS(False)
    serial_port.setDTR(False)
    serial_port.open()

    window.statusBar.setStyleSheet(
        "QStatusBar { background-color: rgb(12,12,12); color: rgb(0,255,0); font-weight:bold; }"
    )
    window.statusBar.showMessage("Connected: " + str(current_port))


def on_port_changed_callback(port):
    global current_port
    current_port = port
    reopen_serial_port()


def on_baudrate_changed_callback(baudrate):
    global current_port
    global current_baudrate
    current_baudrate = baudrate
    if current_port:
        reopen_serial_port()


def on_reset_device_callback():
    global serial_port
    global current_port
    global current_baudrate
    global window

    window.statusBar.setStyleSheet(
        "QStatusBar { background-color: rgb(12,12,12); color: yellow; font-weight:bold; }"
    )
    window.statusBar.showMessage("Resetting Device...")

    # Close if already open
    if serial_port:
        serial_port.close()

    # Reset the device by re-opening Serial port
    # with DTR and RTS enabled
    #
    # These are enabled by default
    serial_port = serial.Serial(current_port, current_baudrate)

    reopen_serial_port()


window = MainWindow(
    on_port_changed_callback, on_baudrate_changed_callback, on_reset_device_callback
)

# Open serial comms
current_port = window.port
current_baudrate = window.baudrate
if current_port:
    reopen_serial_port()


def main():
    def update():
        global header
        global serial_port
        global window

        if not serial_port:
            return

        try:
            if serial_port.inWaiting() == 0:
                return  # do nothing
        except:
            return

        # read a line from serial port
        strdata = serial_port.readline()

        # and decode it
        if sys.version_info >= (3, 0):
            strdata = strdata.decode("utf-8", "backslashreplace")

        conv = Ansi2HTMLConverter()
        html = conv.convert(strdata)

        # Append received data to GUI output window
        cursor = window.text_edit.textCursor()
        cursor.movePosition(QtGui.QTextCursor.End)
        cursor.insertHtml("<b>" + html.replace("\n", "") + "</b>")
        window.text_edit.setTextCursor(cursor)
        window.text_edit.ensureCursorVisible()

        strdata = escape_ansi(strdata)
        strdata = strdata.strip()

        arrdata = strdata.split(",")
        print(arrdata)

        # return if there was not a comma
        if len(arrdata) < 5:
            return

        # determine if this line is a header or not (first value is string data)
        is_header = False
        try:
            dummy = float(arrdata[0])
        except ValueError:
            is_header = True

        if is_header:
            # an array of strings
            window.plot_page.plot.set_header(arrdata)
        else:
            # an array of numbers
            datapoint = [float(x.strip()) for x in arrdata]

            if len(window.plot_page.plot.trace_names) == 0:
                # Header not set
                # Maybe we didn't receive it over UART
                # Set the Header to be: "Time","Signal_1", "Signal_2",...
                header = ["Time"]
                header.extend(["Signal_" + str(i) for i in range(len(datapoint))])
                window.plot_page.plot.set_header(header)

            window.plot_page.plot.update_data([datapoint])

    timer = QtCore.QTimer(timerType=0)  # Qt.PreciseTimer
    timer.timeout.connect(update)
    timer.start(20)
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
