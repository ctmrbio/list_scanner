#!/usr/bin/env python3.5
"""CTMR list scanner"""
__author__ = "Fredrik Boulund"
__date__ = "2018"

from datetime import datetime
import sys

from fbs_runtime.application_context import ApplicationContext, cached_property
from PyQt5 import QtCore
from PyQt5.QtWidgets import (
    QWidget, QGridLayout, QGroupBox, QFormLayout, QVBoxLayout, QHBoxLayout,
    QPushButton, QFileDialog, QLineEdit,
    QProgressBar, QLabel, QCheckBox, 
    QTextEdit, QRadioButton,
    QComboBox
)

from sample_list import SampleList, ScannedSampleDB


class AppContext(ApplicationContext):           # 1. Subclass ApplicationContext
    def run(self):                              # 2. Implement run()
        self.window.show()
        return self.app.exec_()                 # 3. End run() with this line
    
    @cached_property
    def window(self):
        return MainWindow()

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.keyPressEvent = self._keypress_event_action
        self.focusNextPrevChild = lambda x: False  # Disable Qt intercepting TAB keypress event

        self.fluidx = ""
        self.search_list = ""

        info_text = QLabel('\n'.join([
            "CTMR item scanning application.",
            "Instructions:",
            " 1. Load a list file (Excel, CSV, TSV, or white-space separated text).",
            "    List files can have several columns and optionally a header line on top.",
            " 2. Focus in the scanning field and start scanning.",
            " 3. Select an output file.",
            " 4. Press 'Save and exit' to save a record of the current session and exit.",
            " NOTE: The TAB and ENTER keys have been hardcoded to submit a scanned item,",
            "       you thus need to use the mouse to activate GUI buttons and focus on fields.",
            ])
        )

        self.scantype_combo = QComboBox()
        self.scantype_combo.addItems([
            "Search: Manual scan (one by one)",
            "Search: FluidX scans (CSV)",
            "Register: Manual scan (one by one)",
            "Register: FluidX scans (CSV)",
        ])
        self.scantype_combo.currentTextChanged.connect(self.select_scantype)

        # Search: select and load lists
        self._input_search_list_button = QPushButton("Select search list")
        self._input_search_list_button.clicked.connect(self.select_search_list)
        headers_checkbox = QCheckBox("List columns have headers")
        load_search_list_button = QPushButton("Load search list")
        
        search_layout = QFormLayout()
        list_headers_hbox = QHBoxLayout()
        list_headers_hbox.addWidget(self._input_search_list_button)
        list_headers_hbox.addWidget(headers_checkbox)
        #search_layout.addRow(self._input_search_list_button, 0, 0, 1, 2)
        #search_layout.addRow(headers_checkbox, 1, 0)
        search_layout.addRow("1. Select list:", list_headers_hbox)
        search_layout.addRow("2. Load list:", load_search_list_button)
        self._search_list_group = QGroupBox("Search: Select samples to search for")
        self._search_list_group.setLayout(search_layout)

        # Search: Manual scan
        self._scanfield = QLineEdit(placeholderText="Scan/type item ID")
        search_scan_button = QPushButton("Search for item")
        search_scan_button.clicked.connect(self.search_scanned_item)

        manual_scan_layout = QHBoxLayout()
        manual_scan_layout.addWidget(self._scanfield)
        manual_scan_layout.addWidget(search_scan_button)
        self._manual_scan_group = QGroupBox("Search: Manual scan")
        self._manual_scan_group.setLayout(manual_scan_layout)

        # Register: 
        self._fluidx_csv_button = QPushButton("Select FluidX CSV")
        self._fluidx_csv_button.clicked.connect(self.select_fluidx)
        self._sample_type = QComboBox(editable=True)
        self._sample_type.addItems([
            "Fecal",
            "Vaginal swab",
            "Rectal swab",
            "Saliva",
            "Saliva swab",
            "Biopsy",
        ])
        load_fluidx_button = QPushButton("Load FluidX CSV")
        load_fluidx_button.clicked.connect(self.load_fluidx)

        register_layout = QGridLayout()
        register_layout.addWidget(self._fluidx_csv_button, 0, 0)
        register_layout.addWidget(self._sample_type, 0, 1)
        register_layout.addWidget(load_fluidx_button)
        self._register_group = QGroupBox("Register: Create sample registration lists")
        self._register_group.setLayout(register_layout)

        # Session log 
        self._session_log = QTextEdit()
        session_log_layout = QGridLayout()
        session_log_layout.addWidget(self._session_log, 0, 0)
        self._session_log_group = QGroupBox("Session log")
        self._session_log_group.setLayout(session_log_layout)
        self._session_saved = False

        layout = QGridLayout()
        layout.addWidget(self.scantype_combo, 0, 0)
        #layout.addWidget(info_text)
        layout.addWidget(self._search_list_group, 1, 0)
        layout.addWidget(self._manual_scan_group, 2, 0)
        layout.addWidget(self._register_group, 1, 1)
        layout.addWidget(self._session_log_group, 3, 0)

        self.setLayout(layout)
    
    def select_scantype(self):
        selected_scantype = self.scantype_combo.currentText()
        self.session_log("Selected {}".format(selected_scantype))
        if selected_scantype == "Search: Manual scan (one by one)":
            pass
            # Change layout to include:
            # scantype_combo
            # self._search_list_group
            # self._manual_scan_group
            # self._session_log_group
        elif selected_scantype == "Search: FluidX scans (CSV)":
            pass
            # Change layout to include:
            # scantype_combo
            # self._search_list_group
            # self._manual_scan_group
            # self._session_log_group
        elif selected_scantype == "Register: Manual scan (one by one)":
            pass
            # Change layout to include:
            # scantype_combo
            # self._search_list_group
            # self._manual_scan_group
            # self._session_log_group
        elif selected_scantype == "Register: FluidX scans (CSV)":
            pass
            # Change layout to include:
            # scantype_combo
            # self._search_list_group
            # self._manual_scan_group
            # self._session_log_group
    
    def select_search_list(self):
        self.search_list, _ = QFileDialog.getOpenFileName(self, "Select search list")
        self._input_search_list_button.setText(self.search_list)
        self.session_log("Selected search list '{}'".format(self.search_list))
    
    def select_fluidx(self):
        self.fluidx, _ = QFileDialog.getOpenFileName(self, "Select FluidX CSV")
        self._fluidx_csv_button.setText(self.fluidx)
        self.session_log("Selected FluidX CSV '{}'".format(self.fluidx))
    
    def search_scanned_item(self):
        self.session_log("Searching for item '{}'".format(self._scanfield.text()))
        self._scanfield.setText("")
    
    def load_fluidx(self):
        if self.fluidx:
            self.session_log("Loading FluidX CSV: '{}'".format(self.fluidx))

    def session_log(self, message):
        self._session_log.append("{datetime}: {message}".format(
            datetime=datetime.now(),
            message=message,
        ))

    def _keypress_event_action(self, key):
        if key.key() == QtCore.Qt.Key_Tab:
            #self.session_log("Detected Tab key!")
            self.search_scanned_item()
    


if __name__ == '__main__':
    appctxt = AppContext()                      # 4. Instantiate the subclass
    exit_code = appctxt.run()                   # 5. Invoke run()
    sys.exit(exit_code)