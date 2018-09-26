# CTMR list scanning application
A small GUI wrapper over an SQLite3-backed list scanning tool.

## Dependencies
It is recommended to create a conda environment with pip installed,
and then use pip to install pyforms and dependencies. Below are the main
dependencies and their tested versions listed.

- pyforms (3.0.0)
- pandas (0.23.4)
- xlrd (1.1.0)
- pyqt5 (5.11.2)
- opencv-python (3.4.3.18)

### Manjaro Linux
The following commands have been tested to work well on Manjaro Linux:
```
$ conda create -n list_scanner python=3.7 pip pandas xlrd
$ conda activate list_scanner
[list_scanner]$ pip install pyforms opencv-python
[list_scanner]$ ./scan_lists.py
```

## Running
The main program file is `list_scanner.py`, which will open a GUI with some basic
instructions.  Note that both the Enter and Tab keys have been configured to
trigger a search for whatever item is currently entered in the Scanning field.
You thus have to use the mouse to navigate the GUI.

The program can optionally read scans from a FluidX CSV file containing scanned
tubes. Select how to read scans using the dropdown list above all other controls.
