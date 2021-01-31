# REACPE (Reactimeter)

`REACPE` is a program developed in Python3
that shows measured current from a ionization chamber
and calculates reactivity in real time using inverse kinetic method.
The software also allows source estimation according to
![Hoogenboom 1988](https://doi.org/10.1016/0306-4549(88)90059-X)
for reactivity measurements on subcritical states.
This software is part of a system which includes a compesated ionization chamber
and a Keithley 6517B electrometer.


![Interfaz de la aplicación](https://github.com/6ianco/reacpe/blob/main/icon/interfaz.png)

Dependencies:

- [PyQt5](https://www.riverbankcomputing.com/static/Docs/PyQt5/)
- [PyQtGraph](http://pyqtgraph.org/)
- [SciPy](https://www.scipy.org/)
- [PySerial](https://pyserial.readthedocs.io/en/latest/index.html)


User and group permission on GNU/Linux for RS232-USB TREDNET cable:
![ll /dev/ttyUSB0](https://github.com/6ianco/reacpe/blob/main/icon/lsttyUSB0.png)

```bash
sudo usermod -a -G tty gianfranco
sudo usermod -a -G dialout gianfranco
reboot
```
