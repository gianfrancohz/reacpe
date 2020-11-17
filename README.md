# REACPE (Reactimeter)

`REACPE` is a program that shows measured current from a ionization chamber
and calculates reactivity on real time.
This software is part of a system whith includes a ionization chamber CNEA
model CIC-41, a Keithley 6517B electrometer.

![Interfaz de la aplicación](https://github.com/6ianco/reacpe/tree/main/icon/interfaz.png)

Dependencies:

- Qt Designer: Herramienta que facilita la implementación de la interfaz
gráfica usando componentes de Qt.
- [PyQt4](https://wiki.python.org/moin/PyQt4): PyQt es un binding de la biblioteca gráfica Qt para el lenguaje
de programación Python.
- [PyQtGraph](http://pyqtgraph.org/): Biblioteca para el manejo de gráficos.
- [SciPy](https://www.scipy.org/): Biblioteca de herramientas y algoritmos
matemáticos para python.
- [PySerial](https://pyserial.readthedocs.io/en/latest/index.html): Biblioteca
para establecer comunicación serial.

Permisos para uso en GNU/Linux con cable serial (RS232-USB) TRENDNET:

![ll /dev/ttyUSB0](https://github.com/6ianco/reacpe/tree/main/icon/lsttyUSB0.png)

```bash
sudo usermod -a -G tty gianfranco
sudo usermod -a -G dialout gianfranco
reboot
```

# Cuaderno de bitacora
Este proyecto lleva mucho tiempo en desarrollo. Empezó a inicios del 2017 cuando
me contrataron por vez primera en el IPEN. La idea era contar con un sistema de
medición de reactividad en tiempo real y que agilizase las tareas de medición.
Posteriormente el desarrollo lo continuó Juan Suica llevando el desarrollo a su
primera version 1.0.0. La idea de este cuaderno de bitácora es dejar registro
del desarrollo, ideas que van ocurriendo, mejoras, y así dejar registro de las
decisiones tomadas en el desarrollo.

## 07 Oct 2020
El reactor RP10 cuenta con reflectores de berilio, los cuales representan una
fuente extra de neutrones (fotonuetrones debido a reacciones gamma). El análisis
demuestra que agregar 9 grupos más a las ecuaciones de cinética puntual no
es suficiente, sino que además es necesario incorporar un término de fuente
constante. Entonces, necesitamos de un reactímetro capaz de medir en subcrítico
con fuente. La interfaz girará entorno a este nuevo requerimiento.

## 17 Nov 2020
- Corregí un error en el cálculo de fuente por el programa.
- Agregué algunos parámetros más en la interfaz de ajuste lineal (r_value y
  rho2).
