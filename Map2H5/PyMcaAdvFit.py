from PyMca5.PyMcaGui.physics.xrf import McaAdvancedFit
from numpy import loadtxt
from sys import argv

def main(path):
    datax, datay = loadtxt(path, unpack = True)
    app = McaAdvancedFit.qt.QApplication([])
    app.lastWindowClosed.connect(app.quit)
    form = McaAdvancedFit.McaAdvancedFit()
    form.setData(x = datax, y = datay)
    form.show()
    app.exec()


if __name__ == "__main__":
    main(argv[1])
