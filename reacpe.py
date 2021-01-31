import sys
from datetime import datetime
from PyQt5 import QtCore, QtGui, uic

import time
import pyqtgraph as pg
import serial
import serial.tools.list_ports as lports
import numpy as np
import glob
import os

from scipy import stats
from scipy.integrate import simps
import scipy.optimize


# DECISIONES DE DISEÑO:
# No se conoce eficiencia de fotones para producir fotoneutrones retardados
# Se decide no agregar 9 grupos adicionales por ahora
# Se modelan: neutrones prontos, retardados y fuente.
# Término fuente se calcula según Hoogeboom1998
# Estudiar la forma lineal y exponencial para la aproximación, hay diferencia?
# 
# Desde conectar con el Keithley se empieza a calcular reactividad!


class helpDialog(QtGui.QDialog):
    """
    This is a window pop-up that helps with the Keithley configuration.
    """
    def __init__(self):
        QtGui.QDialog.__init__(self)
        self.dialog = QtGui.QDialog()
        self.setup_ui(self.dialog)
        self.dialog.show()

    def setup_ui(self, dialog):
        """
        This function designs the view of the window help
        """
        dialog.setWindowTitle("How to configure the Keithley")
        dialog.resize(265,172)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap("icon/help1.png"), QtGui.QIcon.Normal,
                QtGui.QIcon.Off)
        dialog.setWindowIcon(icon)
        gridLayout = QtGui.QGridLayout(dialog)
        plainTextEdit = QtGui.QLabel(dialog)
        plainTextEdit.setText("Bauda rate: 8400")
        gridLayout.addWidget(plainTextEdit,0,0,1,1)

        #QtCore.QMetaObject.connectSlotsByName(dialog)

class sourceDialog(QtGui.QDialog):
    """
    Window pop-up to calculate source using Hoogenboom1988 experiment.
    Source is determined via linear regression in the g-P plane.
    Delayed photoneutrons are not considered for this purpose,
    they can be neglected in the RP-10 reactor.
    """
    def __init__(self):
        QtGui.QDialog.__init__(self)
        self.dialog = QtGui.QDialog()
        self.setup_ui(self.dialog)
        self.dialog.show()

    def setup_ui(self, dialog):

        dialog.setWindowTitle("Source Calculation in g-P plane")
        #dialog.resize(880, 552)
        dialog.resize(900, 600)

        gridLayout_all = QtGui.QGridLayout(dialog)

        verticalLayout_left = QtGui.QVBoxLayout()
        verticalLayout_left.setSizeConstraint(
            QtGui.QLayout.SetMinimumSize)
        verticalLayout_right = QtGui.QVBoxLayout()
        verticalLayout_right.setSpacing(0)

        # Parameters from linear regression
        groupBox_param = QtGui.QGroupBox(dialog)
        groupBox_param.setTitle("Linear Regression")
        gridLayout_param = QtGui.QGridLayout(groupBox_param)
        
        label1 = QtGui.QLabel(dialog)
        label2 = QtGui.QLabel(dialog)
        label3 = QtGui.QLabel(dialog)
        label4 = QtGui.QLabel(dialog)
        label5 = QtGui.QLabel(dialog)
        label6 = QtGui.QLabel(dialog)
        label7 = QtGui.QLabel(dialog)
        self.label_t1 = QtGui.QLabel(dialog)
        self.label_t2 = QtGui.QLabel(dialog)
        self.labelA = QtGui.QLabel(dialog)
        self.labelB = QtGui.QLabel(dialog)
        self.label_r = QtGui.QLabel(dialog)
        self.label_rho2 = QtGui.QLabel(dialog)

        label1.setText("g = A*P + B")
        label2.setText("t1: ")
        label3.setText("t2: ")
        self.label_t1.setText("---")
        self.label_t2.setText("---")
        label4.setText("A: ")
        label5.setText("B: ")
        self.labelA.setText("---")
        self.labelB.setText("---")
        label6.setText("r value: ")
        label7.setText("rho2: ")
        self.label_r.setText("---")
        self.label_rho2.setText("---")

        self.pushButton_update = QtGui.QPushButton(groupBox_param)
        self.pushButton_update.setText("Update")
        self.pushButton_save = QtGui.QPushButton(groupBox_param)
        self.pushButton_save.setText("Save on file")

        gridLayout_param.addWidget(label1,0,0,1,1)
        gridLayout_param.addWidget(label2,1,0,1,1)
        gridLayout_param.addWidget(label3,2,0,1,1)
        gridLayout_param.addWidget(label4,3,0,1,1)
        gridLayout_param.addWidget(label5,4,0,1,1)
        gridLayout_param.addWidget(label6,5,0,1,1)
        gridLayout_param.addWidget(label7,6,0,1,1)

        gridLayout_param.addWidget(self.label_t1,1,1,1,1)
        gridLayout_param.addWidget(self.label_t2,2,1,1,1)
        gridLayout_param.addWidget(self.labelA,3,1,1,1)
        gridLayout_param.addWidget(self.labelB,4,1,1,1)
        gridLayout_param.addWidget(self.label_r,5,1,1,1)
        gridLayout_param.addWidget(self.label_rho2,6,1,1,1)

        gridLayout_param.addWidget(self.pushButton_update,7,0,1,1)
        gridLayout_param.addWidget(self.pushButton_save,8,0,1,1)

        verticalLayout_left.addWidget(groupBox_param)

        self.graphicsView_Pt = pg.PlotWidget(dialog)
        #self.graphicsView_Pt.setGeometry(QtCore.QRect(290,10,581,391))
        self.graphicsView_gP = pg.PlotWidget(dialog)
        #self.graphicsView_gP.setGeometry(QtCore.QRect(290,400,581,111))

        verticalLayout_right.addWidget(self.graphicsView_Pt)
        verticalLayout_right.addWidget(self.graphicsView_gP)

        gridLayout_all.addLayout(verticalLayout_left,0,0,1,1)
        gridLayout_all.addLayout(verticalLayout_right,0,1,1,1)



class mainWindow(QtGui.QMainWindow):
    """
    Ventana principal para la acquisición
    """
    def __init__(self):

        buffer_sz = 500
        self.dolar = 0

        # Para iniciar la ventana principal
        QtGui.QMainWindow.__init__(self)
        self.ui = QtGui.QMainWindow()
        #self.ui.closeEvent = self.close_event
        self.setup_ui(self.ui)
        self.ui.show()

        # Close main ui
        self.ui.closeEvent = self.close_event


        # Input parameters set-up
        for reactor in glob.glob('./reactor/*.npy'):
            self.ui.comboBox_reactor.addItem(reactor)
        for consts in glob.glob('./delayed/*.npy'):
            self.ui.comboBox_const.addItem(consts)
        #for phot_consts in glob.glob('./delayphot/*.phot'):
        #    self.ui.comboBox_phot.addItem(phot_consts)
        for sources in glob.glob('./source/*.src'):
            self.ui.comboBox_src.addItem(sources)


        # Establish serial communication
        ports_list = list(lports.comports())
        for portname, description, address in ports_list:
            self.ui.comboBox_ports.addItem(portname)
        self.is_connected = False   # Right now is not connected
        self.ui.pushButton_help.clicked.connect(self.help_dialog)

        # Source calculation
        self.ui.pushButton_srccalcstart.clicked.connect(self.start_src_acquisition)
        

        # For real measurement (no testing)
        # Keithley and Serial communication
        #self.setup_acquisitonfile()
        #self.ui.pushButton_connect.clicked.connect(self.start_serial_talking)
        #self.timer_serial = pg.QtCore.QTimer()
        #self.timer_serial.stop()
        #self.timer_serial.timeout.connect(self.read_from_keithley)

        # Variables
        buffer_sz = 500
        self.t = [0.] * buffer_sz # time vector
        self.n = [0.] * buffer_sz # current
        self.r = [0.] * buffer_sz # reactivity

        self.ALLOW_REACT_CALCULATION = False
        self.SRC_ACQUISITION = False
        self.Ng = 6 
        self.c = [0.] * self.Ng

        # Start reactivity calculation button
        self.ui.pushButton_reacstart.clicked.connect(self.setup2start_reactivitycalculation)
        self.ui.pushButton_reacstats.clicked.connect(self.show_reac_stats)

        # Just for testing
        self.setup_acquisitonfile()
        self.inhour_calculation()
        self.timer_simulate = pg.QtCore.QTimer()
        self.timer_simulate.timeout.connect(self.generar_datos)
        self.timer_simulate.start(100)
        self.t = [-10.]*buffer_sz
        self.n = [1.0]*buffer_sz
        

        self.timer_graph = pg.QtCore.QTimer()
        self.timer_graph.timeout.connect(self.update_plots)
        self.timer_graph.start(2000)

    def setup_ui(self, MainWindow):

        MainWindow.setWindowTitle("Reactimeter v0.0.1")
        MainWindow.resize(991, 642)

        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap("icon/python1.png"), QtGui.QIcon.Normal,
                QtGui.QIcon.Off)
        MainWindow.setWindowIcon(icon)

        self.ui.centralWidget = QtGui.QWidget(MainWindow)
        self.ui.gridLayout_all = QtGui.QGridLayout(self.ui.centralWidget)
        self.ui.verticalLayout_left = QtGui.QVBoxLayout()
        self.ui.verticalLayout_left.setSizeConstraint(
                QtGui.QLayout.SetMinimumSize)
        self.ui.verticalLayout_right = QtGui.QVBoxLayout()
        self.ui.verticalLayout_right.setSpacing(0)

        #    centralWidget design:
        #    _________________________gridLayout_all___________________________
        #   | ____verticalLayout_left___  _______verticalLayout_right_________ |
        #   || ____gridLayout_rs232____ ||                                    ||
        #   |||                        |||                 $                  ||
        #   ||| CONNECT          HELP  |||                                    || 
        #   |||________________________|||  $(t)|                             ||                 
        #   || ____gridLayout_source___ ||      |                             ||
        #   |||                        |||      |                             ||
        #   |||  START           END   |||      |________________________     ||
        #   |||________________________|||                              t     ||
        #   || _____gridLayout_param:__|||____________________________________||
        #   |||                        |||                                    ||
        #   |||                        |||  I(t)|                             || 
        #   |||________________________|||      |                             ||
        #   || _____gridLayout_react __ ||      |                             || 
        #   |||  START         STATS   |||      |________________________     ||
        #   |||________________________|||                              t     ||
        #   ||__________________________||____________________________________||
        #   |__________________________________________________________________|


        # Keithley conecction
        spacerItem_modo = QtGui.QSpacerItem(20, 40, QtGui.QSizePolicy.Minimum,
                QtGui.QSizePolicy.Expanding)
        self.ui.verticalLayout_left.addItem(spacerItem_modo)

        self.ui.groupBox_rs232 = QtGui.QGroupBox(self.ui.centralWidget)
        self.ui.groupBox_rs232.setTitle("Serial connection")
        self.ui.gridLayout_rs232 = QtGui.QGridLayout(self.ui.groupBox_rs232)

        self.ui.pushButton_connect = QtGui.QPushButton(self.ui.groupBox_rs232)
        icon_connect = QtGui.QIcon()
        icon_connect.addPixmap(QtGui.QPixmap("icon/rs232.png"),
            QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.ui.pushButton_connect.setIcon(icon_connect)
        self.ui.pushButton_connect.setText("CONNECT")
        self.ui.gridLayout_rs232.addWidget(self.ui.pushButton_connect,1,0,1,1)

        self.ui.comboBox_ports = QtGui.QComboBox(self.ui.groupBox_rs232)
        self.ui.gridLayout_rs232.addWidget(self.ui.comboBox_ports,0,0,1,2)
        self.ui.pushButton_help = QtGui.QPushButton(self.ui.groupBox_rs232)
        icon_help = QtGui.QIcon()
        icon_help.addPixmap(QtGui.QPixmap("icon/help1.png"), QtGui.QIcon.Normal,
                QtGui.QIcon.Off)
        self.ui.pushButton_help.setIcon(icon_help)
        self.ui.gridLayout_rs232.addWidget(self.ui.pushButton_help,1,1,1,1)

        self.ui.verticalLayout_left.addWidget(self.ui.groupBox_rs232)




        # Parameters & data selection from files
        self.ui.groupBox_param = QtGui.QGroupBox(self.ui.centralWidget)
        self.ui.groupBox_param.setTitle("Input parameters")
        self.ui.gridLayout_param = QtGui.QGridLayout(self.ui.groupBox_param)

        labelReactor = QtGui.QLabel(self.ui.centralWidget)
        labelReactor.setText("Reactor:")
        self.ui.gridLayout_param.addWidget(labelReactor,0,0,1,1)
        self.ui.comboBox_reactor = QtGui.QComboBox(self.ui.groupBox_param)
        self.ui.gridLayout_param.addWidget(self.ui.comboBox_reactor,0,1,1,1)

        labelConst = QtGui.QLabel(self.ui.centralWidget)
        labelConst.setText("Constants:")
        self.ui.gridLayout_param.addWidget(labelConst,1,0,1,1)
        self.ui.comboBox_const = QtGui.QComboBox(self.ui.groupBox_param)
        self.ui.gridLayout_param.addWidget(self.ui.comboBox_const,1,1,1,1)

        # Futura implementación
        #labelPhoton = QtGui.QLabel(self.ui.centralWidget)
        #labelPhoton.setText("Photoneutrons:")
        #self.ui.gridLayout_param.addWidget(labelPhoton,2,0,1,1)
        #self.ui.comboBox_phot = QtGui.QComboBox(self.ui.groupBox_param)
        #self.ui.gridLayout_param.addWidget(self.ui.comboBox_phot,2,1,1,1)

        labelSource = QtGui.QLabel(self.ui.centralWidget)
        labelSource.setText("Source:")
        self.ui.gridLayout_param.addWidget(labelSource,3,0,1,1)
        self.ui.comboBox_src = QtGui.QComboBox(self.ui.groupBox_param)
        self.ui.gridLayout_param.addWidget(self.ui.comboBox_src,3,1,1,1)
        #self.ui.doubleSpinBox_src = QtGui.QDoubleSpinBox(self.ui.groupBox_param)
        #self.ui.doubleSpinBox_src.setValue(2.1e-5)
        #self.ui.gridLayout_param.addWidget(self.ui.doubleSpinBox_src,4,1,1,1)

        self.ui.verticalLayout_left.addWidget(self.ui.groupBox_param)
        #self.ui.mode_use.setEnabled(False)



        # Source calculation (srccalc) using Hoogenboom1998
        groupBox_srccalc = QtGui.QGroupBox(self.ui.centralWidget)
        groupBox_srccalc.setTitle("Source calculation")
        gridLayout_srccalc = QtGui.QGridLayout(groupBox_srccalc)

        self.ui.pushButton_srccalcstart = QtGui.QPushButton(groupBox_srccalc)
        self.ui.pushButton_srccalcstart.setText("START")
        gridLayout_srccalc.addWidget(self.ui.pushButton_srccalcstart,0,0,1,1)

        self.ui.pushButton_srccalcend = QtGui.QPushButton(groupBox_srccalc)
        self.ui.pushButton_srccalcend.setText("END")
        gridLayout_srccalc.addWidget(self.ui.pushButton_srccalcend,0,1,1,1)

        self.ui.verticalLayout_left.addWidget(groupBox_srccalc)
       


        # Reactivity statistics on real time button
        groupBox_react = QtGui.QGroupBox(self.ui.centralWidget)
        groupBox_react.setTitle("Reactivity")
        gridLayout_react = QtGui.QGridLayout(groupBox_react)

        self.ui.pushButton_reacstart = QtGui.QPushButton(groupBox_react)
        self.ui.pushButton_reacstart.setText("START")
        gridLayout_react.addWidget(self.ui.pushButton_reacstart,0,0,1,1)

        self.ui.pushButton_reacstats = QtGui.QPushButton(groupBox_react)
        self.ui.pushButton_reacstats.setText("STATS")
        gridLayout_react.addWidget(self.ui.pushButton_reacstats,1,0,1,1)

        self.ui.verticalLayout_left.addWidget(groupBox_react)




        # Acquisition current from CIC and reactivity calculation
        self.ui.labelDolar = QtGui.QLabel(self.ui.centralWidget)
        self.ui.labelDolar.setText("---")
        self.ui.labelDolar.setAlignment(QtCore.Qt.AlignCenter)
        labelFont = QtGui.QFont()
        labelFont.setPointSize(70)
        labelFont.setBold(True)
        labelFont.setWeight(75)
        self.ui.labelDolar.setFont(labelFont)
        self.ui.labelDolar.setStyleSheet("color: rgb(255,255,255);\n"
                "background-color: rgb(0,0,0)\n")
        self.ui.verticalLayout_right.addWidget(self.ui.labelDolar)

        self.ui.graphicsView_curr = pg.PlotWidget(self.ui.centralWidget)
        self.ui.graphicsView_curr.showGrid(x=1,y=1,alpha=1)
        self.ui.graphicsView_curr.setLabel('left',text="<p><font size='6' \
                color='yellow'>Current", units='A')
        #self.ui.graphicsView_curr.setLabel('bottom',text="<p><font size='3' \
        #        color='orange'>Tiempo", units='s')

        self.ui.graphicsView_reac = pg.PlotWidget(self.ui.centralWidget)
        self.ui.graphicsView_reac.showGrid(x=1,y=1,alpha=1)
        self.ui.graphicsView_reac.setLabel('left',text="<p><font size='6' \
                color='cyan'>Reactivity", units='pcm')
        #self.ui.graphicsView_reac.setLabel('bottom',text="<p><font size='3' \
        #        color='orange'>Tiempo", units='s')

        self.ui.verticalLayout_right.addWidget(self.ui.graphicsView_reac)
        self.ui.verticalLayout_right.addWidget(self.ui.graphicsView_curr)



        self.ui.gridLayout_all.addLayout(self.ui.verticalLayout_left,0,0,1,1)
        self.ui.gridLayout_all.addLayout(self.ui.verticalLayout_right,0,1,1,1)

        MainWindow.setCentralWidget(self.ui.centralWidget)

    def help_dialog(self):
        self.d_help = helpDialog()

    def src_dialog(self):
        self.d_src = sourceDialog()

        self.d_src.graphicsView_Pt.plot(self.src_t, self.src_P, pen='g')
        self.d_src.graphicsView_Pt.plot(self.src_t, self.src_P, symbolBrush=(255,0,0))
        self.d_src.graphicsView_Pt.showGrid(x=1, y=1)
        self.lr = pg.LinearRegionItem([self.src_t[0], self.src_t[-1]])
        self.d_src.graphicsView_Pt.addItem(self.lr)

        self.d_src.pushButton_update.clicked.connect(self.update_src_dialog)
        self.d_src.pushButton_save.clicked.connect(self.save_src_regression_data)
        #self.lr.sigRegionChanged.connect(self.update_src_dialog)
        self.FIRSTPLOT = True

    def update_src_dialog(self):

        # Extraigo los límites de la región seleccionada
        self.left_t, self.right_t = self.lr.getRegion()

        t = np.array(self.src_t)
        P = np.array(self.src_P)

        # Construyo la función g 
        sz = np.size(P)
        I = np.zeros((sz,self.Ng))
        g = np.zeros(sz)
        bl = self.b * self.l
        I[0] = P[0]/self.l
        g[0] = np.dot(I[0], bl)

        for k in range(1, sz):
            dt = t[k]-t[k-1]
            for i in range(0, self.Ng):
                lamidt = self.l[i]*dt
                e = np.exp(-lamidt)
                ee = (1-e)/lamidt
                I[k][i] = I[k-1][i]*e + P[k]*(1.-ee)/self.l[i]-P[k-1]*(e-ee)/self.l[i]
            g[k] = np.dot(I[k], bl)

        # Loops para quedarse solo con datos dentro de la región seleccionada
        #print(P)
        #print(P[0])
        while self.left_t > t[0]:
            t = np.delete(t, 0)
            P = np.delete(P,0)
            g = np.delete(g,0)
        while self.right_t < t[-1]:
            t = np.delete(t, -1)
            P = np.delete(P, -1)
            g = np.delete(g, -1)


        # Regresión lineal
        # slope:        pendiente del ajuste lineal
        # intercept:    constante del ajuste lineal
        # r_value:       Correlación del ajuste
        # p_value:      Ni idea, ver manual de stats (no se usa)
        # std_error:    Error de slope
        self.slope, self.intercept, self.r_value, p_value, std_error = stats.linregress(P,g)

        fit = self.intercept + self.slope*P

        if self.FIRSTPLOT:
            self.p1 = self.d_src.graphicsView_gP.plot(P, g, symbolBrush=(255,0,0))
            self.p2 = self.d_src.graphicsView_gP.plot(P, fit)
            self.FIRSTPLOT = False


        self.p1.setData(P,g)
        self.p2.setData(P,fit)

        self.d_src.labelB.setText(format(self.intercept, ".4E"))
        self.d_src.labelA.setText(format(self.slope, ".4E"))
        self.d_src.label_t1.setText(format(self.left_t, ".2f")+" sec")
        self.d_src.label_t2.setText(format(self.right_t, ".2f")+" sec")
        self.d_src.label_r.setText(format(self.r_value, ".5f"))
        self.d_src.label_rho2.setText(format(1.0-self.slope, ".4f")+" $")

    def save_src_regression_data(self):
        f = open(self.src_datafilename, 'r+')
        content = f.read()
        f.seek(0,0)

        text = "# B (source):" + format(self.intercept, ".4E")+'\n'
        text += "# A: " + format(self.slope, ".4E")+'\n'
        text += "# t1 (sec): " + format(self.left_t, ".2f")+'\n'
        text += "# t2 (sec): " + format(self.right_t, ".2f")+'\n'
        text += "# r value: " + format(self.r_value, ".5f")+'\n'

        f.write(text+content)
        f.close()
        self.d_src.pushButton_save.setText("Saved")
        self.d_src.pushButton_save.setEnabled(False)

    def start_serial_talking(self):
        """
        This function initiates the talking with the Keithley following its
        protocol communication. More information see Keithley manual.
        """
        if self.ui.pushButton_connect.text()=='CONNECT':
            portname = self.ui.comboBox_ports.currentText()
            try:
                self.ser = serial.Serial(str(portname), 38400, timeout=1)
                self.ser.write(b'*IDN?\n') # the prefic b is to enconde in ascii
                line = self.ser.readline()
                self.ui.graphicsView_curr.setTitle("<p><font color='orange'>".
                        format(line))
                self.ser.write(b'*RST\n')
                self.ser.write(b'SENS:CURR:NPLC 1\n')
                self.ser.write(b'CONF:CURR\n') # function mode
                self.ser.write(b'SYST:KEY 23\n') # function mode
                self.ser.write(b'SENS:CURR:DC:NPLC 0.01\n') # time acquisition
                self.ser.write(b'SENS:CURR:DC:DIG 6\n') # resolution configuration
                time.sleep(0.5) # Keithley needs some time to think ... I think
                self.ser.flushInput()
                
                self.ui.comboBox_ports.setEnabled(False)
                self.ui.pushButton_connect.setText('DISCONNECT')

                #self.start_time_acq = str(datetime.now())
                self.timer_serial.start(60) # each 60 mseg

            except (serial.SerialException, ValueError):
                self.ui.labelDolar.setText("<p><font color='red'>Error connection")
        else:
            self.timer_serial.stop()
            self.ser.close()
            self.ui.pushButton_connect.setText('CONNECT')

    def read_from_keithley(self):
        """
        This function
        """
        try:

            self.ser.write(b'READ?\n')
            line = self.ser.readline()
            self.t.append(float(line[19:33]))
            self.n.append(float(line[0:13]))
            self.t.remove(self.t[0]) # remove to append a newone
            self.n.remove(self.n[0])

            if self.ALLOW_REACT_CALCULATION:
                self.r.remove(self.r[0])
                self.reactivity_calculation()
                self.r.append(self.react_pcm)

            text = str(self.t[-1])+'\t'+str(self.n[-1])

            # Saving data if acquisiton for source determination is enabled.
            if self.SRC_ACQUISITION:
                self.src_datafile.write(text+'\n')
                self.src_t.append(self.t[-1])
                self.src_P.append(self.n[-1])

            text += '\t' + str(self.r[-1])+'\n'

            # Saving all data...
            self.datafile.write(text)

        except ValueError:
            # Parece q al inicio al leer desde el keithley hay un error
            # pero que luego se corrige
            #self.ui.labelDolar.setText('<p><font color="RED">READ CONN ERR')
            pass

    def reactivity_calculation(self):

        # This condition is TRUE only once and its to know the initial
        # precursors concentration and reactivity state.
        if self.INIT:
            for i in range(0,6):
                self.c[i] = self.n[-1] * self.b[i] / (self.l[i] * self.Lx)
            # Initial condition about reactivity in stationary reactor
            if self.Sx == 0.0:
                self.react_dolar = 0.0
            else:
                self.react_dolar = -self.Sx/self.n[-1]
            self.INIT = False

        else:
            h = self.t[-1] - self.t[-2]
            for i in range(0,6):
                self.c[i] = ( self.c[i] + self.b[i]*h*self.n[-1]/self.Lx) / (1. + self.l[i]*h)
            # Sx is obtained from linear regression
            self.react_dolar = 1.0 + self.Lx*(1 - self.n[-2]/self.n[-1])/h - self.Sx/self.n[-1]
            for i in range(0,6):
                self.react_dolar += -self.l[i]*self.Lx*self.c[i]/self.n[-1]

        self.react_pcm = self.react_dolar * self.beta_eff * 1e5
        self.react_pcm_sum += self.react_pcm 
        self.display_counter += 1

        if self.STATS_ACTIVATED:
            self.reac_to_stats = np.append(self.reac_to_stats, self.react_pcm)


        # I show on display an average value
        if self.display_counter == self.DISPLAY_COUNTER_MAX:

            if self.SHOW_REAL_TIME:
                react_pcm_avrg = self.react_pcm_sum/self.display_counter
                temp = "{:.0f}".format(react_pcm_avrg)+" pcm"
                self.ui.labelDolar.setText(temp)

            else:
                N = len(self.reac_to_stats)
                temp = "{:.1f}".format(np.mean(self.reac_to_stats)) + " +/- "
                temp += "{:.1f}".format(np.std(self.reac_to_stats)/np.sqrt(N)) + " pcm"
                self.ui.labelDolar.setText(temp)

            self.display_counter = 0
            self.react_pcm_sum = 0.0

    def update_plots(self):
        """
        I think the name explains well
        """
        self.ui.graphicsView_curr.plot(self.t, self.n, pen={'color': 'y',\
                'width':3}, clear=True)

        if self.ALLOW_REACT_CALCULATION:
            self.ui.graphicsView_reac.plot(self.t, self.r, pen={'color': 'c',\
                    'width':3}, clear=True)

        self.ui.graphicsView_curr.enableAutoRange('x')
        self.ui.graphicsView_reac.enableAutoRange('x')

    def setup2start_reactivitycalculation(self):

        self.ALLOW_REACT_CALCULATION = False
        
        self.read_reactorfile()
        self.read_delayedfile()
        self.read_sourcefile()

        self.ALLOW_REACT_CALCULATION = True
        self.INIT = True
        self.display_counter = 0
        self.react_pcm_sum = 0.0
        self.DISPLAY_COUNTER_MAX = 10
        self.SHOW_REAL_TIME = True
        self.STATS_ACTIVATED = False
        self.ui.pushButton_reacstart.setText('RESET')

    def show_reac_stats(self):
        if self.SHOW_REAL_TIME:
            self.SHOW_REAL_TIME = False
            self.STATS_ACTIVATED = True
            self.reac_to_stats = np.array([])
        else:
            self.SHOW_REAL_TIME = True
            self.STATS_ACTIVATED = False

    def read_reactorfile(self):
        constants = np.load(self.ui.comboBox_reactor.currentText())
        self.beta_eff = constants[0]
        self.Lx = constants[1]

    def read_delayedfile(self):
        constants = np.load(self.ui.comboBox_const.currentText(), allow_pickle=True)
        self.b = np.array(constants[1])
        self.l = np.array(constants[2])

    def read_sourcefile(self):
        f = open(self.ui.comboBox_src.currentText(), 'r')
        self.Sx = float(f.readline())
        f.close()

    def inhour_calculation(self):
        """
        This function calculates or simulates neutron population behavior at
        a given reactivity value. This function is used only for testing the
        program in case we dont have the Keithley instrument. 
        """
        # Valores tipicos
        Lx = 0.0070385
        b = [0.033, 0.219, 0.196, 0.395, 0.115, 0.042]
        l = [0.0124, 0.0305, 0.1110, 0.3010, 1.1400, 3.0100]

        # Finds roots of inhour equation.
        def in_hour(x, dolar):
            y = Lx
            for i in range(0,6):
                y += b[i]/(x+l[i])
            y *= x
            y += -dolar
            return y

        # guess es un vector donde se quiere encontrar las raices de la ecuación
        # dada una inserción de reactividad constante. Se sabe que las raices
        # están alrededor de los l[i]
        guess = np.linspace(-0.312, 0.0, 200)
        guess_2 = np.linspace(-1.41, -0.312, 100)
        guess_3 = np.linspace(-3.88, -1.41, 100)
        guess_4 = np.array([1.0, -10.0, -100.0, -500.0, -1000.0, -1500.0])
        guess = np.append(guess, guess_2)
        guess = np.append(guess, guess_3)
        guess = np.append(guess, guess_4)

        # Reactividad a incorporar para la simulacion
        dolar = 0.01

        # Función de Scipy que encuentra las raices de una funcion no lineal, se
        # le pasa como parámetros la función no lineal, guess y el parámetro
        # adicional dolar. sols posee mucha información, las soluciones se
        # encuentran el sols.x
        sols = scipy.optimize.root(in_hour, guess, args=(dolar), method='lm')

        # Se ordena de menor a mayor las soluciones encontradas, habrán muchas
        # repetidad. hay tantas como el tamaño del vector guess
        sols.x.sort()

        # Se convierte a un array numpy para poder manejarlo comodamente.
        sols.x = np.array(sols.x)

        # Solo nos quedamos con cinco decimales
        sols.x = np.round(sols.x, decimals=5)

        # se crean las variables globales dentro de la calse.
        # self.omega serán las raices
        # self.A serán los polos
        self.omega = [sols.x[0]]
        self.A = np.array([])

        # Loop necesario para eliminar todas las soluciones repetidad y
        # quedarnos tan solo con las raíces.
        for w in sols.x:
            if w != self.omega[-1]:
                self.omega.append(w)

        if len(self.omega) == 7:
            # Loop para el cálculo de los polos
            for i in range(0,7):
                suma_1 = 0.0
                suma_2 = 0.0
                for j in range(0,6):
                    suma_1 += b[j]/(self.omega[i]+l[j])
                    suma_2 += b[j]*l[j]/(self.omega[i]+l[j])**2
                self.A = np.append(self.A, (Lx + suma_1)/(Lx + suma_2))

    def generar_datos(self):
        """
        This function is used only for testing the program in case we dont
        have the Keithley instrument
        """
        #print("hola")
        self.t.remove(self.t[0])
        self.n.remove(self.n[0])

        dt = 60e-3 #mseg
        self.t.append(self.t[-1] + dt)

        # La simulación empieza a t = 0 seg
        if self.t[-1] > 0.:
            N = 0.
            for i in range(0,7):
                N += self.A[i] * np.exp(self.omega[i]*self.t[-1])
        else:
            N = 1.

        self.n.append(N)

        if self.ALLOW_REACT_CALCULATION:
            self.r.remove(self.r[0])
            self.reactivity_calculation()
            self.r.append(self.react_pcm)

        text = str(self.t[-1])+'\t'+str(self.n[-1])

        # Saving data if acquisiton for source determination is enabled.
        if self.SRC_ACQUISITION:
            self.src_datafile.write(text+'\n')
            self.src_t.append(self.t[-1])
            self.src_P.append(self.n[-1])

        text += '\t' + str(self.r[-1])+'\n'

        # Saving all data...
        self.datafile.write(text)

    def setup_acquisitonfile(self):
        formato = "./reports/all%d-%m-%Y_%Hh%Mm%S.dat"
        fecha = datetime.now()
        n_fecha = fecha.strftime(formato)
        self.datafile = open(n_fecha, 'wt')

        text = '# t(seg)\t CIC (A)\t Reactivity($)\n'
        self.datafile.write(text)

    def close_event(self, event):
        result = QtGui.QMessageBox.question(self,"Close",str("Are you sure?"),
                    QtGui.QMessageBox.Yes|QtGui.QMessageBox.No)
        if result == QtGui.QMessageBox.Yes:
            try:
                self.datafile.close()
                pass
            except AttributeError:
                pass

            #try:
            #    self.ser.close()
            #    pass
            #except AttributeError:
            #    pass

            event.accept()
        else:
            event.ignore()
            pass

    def start_src_acquisition(self):

        formato = "./reports/src_%d-%m-%Y_%Hh%Mm%S.dat"
        fecha = datetime.now()
        self.src_datafilename = fecha.strftime(formato)
        self.src_datafile = open(self.src_datafilename, 'wt')

        text = "# t(seg)\t CIC(A)\n "
        self.src_datafile.write(text)

        self.src_t = []
        self.src_P = []

        self.read_delayedfile()

        self.SRC_ACQUISITION = True
        self.ui.pushButton_srccalcstart.setEnabled(False)
        self.ui.pushButton_srccalcend.setEnabled(True)
        self.ui.pushButton_srccalcend.clicked.connect(self.stop_src_acquisition)

    def stop_src_acquisition(self):
        
        self.SRC_ACQUISITION = False
        self.src_datafile.close()

        self.ui.pushButton_srccalcstart.setEnabled(True)
        self.ui.pushButton_srccalcend.setEnabled(False)

        self.src_dialog()

def main():
    app = QtGui.QApplication(sys.argv)
    window = mainWindow()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
