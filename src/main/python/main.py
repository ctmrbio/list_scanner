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
    QPushButton, QFileDialog, QLineEdit, QProgressBar, QLabel, QCheckBox, 
    QTextEdit, QRadioButton, QComboBox, QMenuBar
)
from PyQt5.QtGui import QPixmap

from sample_list import SampleList, ScannedSampleDB


class AppContext(ApplicationContext):           # 1. Subclass ApplicationContext
    def run(self):                              # 2. Implement run()
        self.window.setWindowTitle("CTMR List Scanner")
        self.window.resize(1000, 700)
        self.window.show()
        return self.app.exec_()                 # 3. End run() with this line
    
    @cached_property
    def window(self):
        return MainWindow()


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.keyPressEvent = self._keypress_event_action  # Define custom handling of keypress events
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

        pixmap_art = QPixmap(appctxt.get_resource("bacteria.png")).scaledToHeight(50)
        art = QLabel()
        art.setPixmap(pixmap_art)
        art.setAlignment(QtCore.Qt.AlignRight)
        pixmap_logo = QPixmap(appctxt.get_resource("CTMR_logo_white_background.jpg")).scaledToHeight(50)
        logo = QLabel()
        logo.setPixmap(pixmap_logo)
        logo.setAlignment(QtCore.Qt.AlignLeft)

        self.scantype_combo = QComboBox()
        self.scantype_combo.addItems([
            "Search: Search for samples in list(s)",
            "Register: Create sample registration list(s)",
        ])
        self.scantype_combo.currentTextChanged.connect(self.select_scantype)

        # Search: select and load lists
        self._input_search_list_button = QPushButton("Select search list")
        self._input_search_list_button.clicked.connect(self.select_search_list)
        headers_checkbox = QCheckBox("Headers")
        load_search_list_button = QPushButton("Load search list")
        
        search_layout = QFormLayout()
        list_headers_hbox = QHBoxLayout()
        list_headers_hbox.addWidget(self._input_search_list_button)
        list_headers_hbox.addWidget(headers_checkbox)
        search_layout.addRow("1. Select list:", list_headers_hbox)
        search_layout.addRow("2. Load list:", load_search_list_button)
        self._search_list_group = QGroupBox("Select list of samples to search for")
        self._search_list_group.setLayout(search_layout)

        # Search: Manual scan
        self._scanfield = QLineEdit(placeholderText="Scan/type item ID")
        search_scan_button = QPushButton("Search for item")
        search_scan_button.clicked.connect(self.search_scanned_item)

        manual_scan_layout = QGridLayout()
        manual_scan_layout.addWidget(self._scanfield, 0, 0)
        manual_scan_layout.addWidget(search_scan_button, 0, 1)
        self._manual_scan_group = QGroupBox("Search: Manual scan")
        self._manual_scan_group.setLayout(manual_scan_layout)

        # Search: FluidX CSV
        self._search_fluidx_csv_button = QPushButton("Select FluidX CSV")
        self._search_fluidx_csv_button.clicked.connect(self.select_search_fluidx)
        load_search_fluidx_button = QPushButton("Load FluidX CSV")
        load_search_fluidx_button.clicked.connect(self.load_search_fluidx)
        search_fluidx_layout = QGridLayout()
        search_fluidx_layout.addWidget(self._search_fluidx_csv_button)
        search_fluidx_layout.addWidget(load_search_fluidx_button)
        self._search_fluidx_group = QGroupBox("Search: FluidX CSV")
        self._search_fluidx_group.setLayout(search_fluidx_layout)

        # Register: Manual or FluidX CSV
        self._register_fluidx_csv_button = QPushButton("Select FluidX CSV")
        self._register_fluidx_csv_button.clicked.connect(self.select_register_fluidx)
        self._sample_type = QComboBox(editable=True)
        self._sample_type.addItems([
            "Fecal",
            "Vaginal swab",
            "Rectal swab",
            "Saliva",
            "Saliva swab",
            "Biopsy",
        ])
        self._load_register_fluidx_csv_button = QPushButton("Load FluidX CSV")
        self._load_register_fluidx_csv_button.clicked.connect(self.load_register_fluidx)
        self._register_scanfield = QLineEdit(placeholderText="Scan/type item ID")
        register_scan_button = QPushButton("Register item")
        register_scan_button.clicked.connect(self.register_scanned_item)

        register_fluidx_layout = QFormLayout()
        register_fluidx_layout.addRow("Select FluidX CSV:", self._register_fluidx_csv_button)
        register_fluidx_layout.addRow("Load FluidX CSV:", self._load_register_fluidx_csv_button)
        register_fluidx_layout.addRow("Select sample type:", self._sample_type)
        register_scan_hbox = QHBoxLayout()
        register_scan_hbox.addWidget(self._register_scanfield)
        register_scan_hbox.addWidget(register_scan_button)
        register_fluidx_layout.addRow(register_scan_hbox)
        self._register_fluidx_group = QGroupBox("Register: Create sample registration lists")
        self._register_fluidx_group.setLayout(register_fluidx_layout)

        # Session log 
        self._session_log = QTextEdit()
        self._search_progress = QProgressBar()
        self._search_progress.setMinimum(0)
        self._search_progress.setMaximum(0)
        session_log_layout = QVBoxLayout()
        session_log_layout.addWidget(self._search_progress)
        session_log_layout.addWidget(self._session_log)
        self._session_log_group = QGroupBox("Session log")
        self._session_log_group.setLayout(session_log_layout)
        self._session_saved = False

        # Overall layout
        layout = QGridLayout()
        layout.addWidget(art, 0, 1)
        layout.addWidget(logo, 0, 2)
        layout.addWidget(self.scantype_combo, 0, 0)
        layout.addWidget(self._search_list_group, 2, 0, 1, 3)
        layout.addWidget(self._search_fluidx_group, 3, 0, 1, 3)
        layout.addWidget(self._manual_scan_group, 4, 0, 1, 3)
        layout.addWidget(self._register_fluidx_group, 2, 0, 1, 3)
        layout.addWidget(self._session_log_group, 5, 0, 1, 3)
        self.setLayout(layout)
        self.select_scantype()  # Set up the default chosen scantype layout
    
    def select_scantype(self):
        selected_scantype = self.scantype_combo.currentText()
        self.session_log("Selected {}".format(selected_scantype))
        if selected_scantype == "Search: Search for samples in list(s)":
            self.scantype_combo.show()
            self._search_list_group.show()
            self._manual_scan_group.show()
            self._search_fluidx_group.show()
            self._register_fluidx_group.hide()
            self._session_log_group.show()
        elif selected_scantype == "Register: Create sample registration list(s)":
            self.scantype_combo.show()
            self._search_list_group.hide()
            self._manual_scan_group.hide()
            self._search_fluidx_group.hide()
            self._register_fluidx_group.show()
            self._session_log_group.show()
            self._search_progress.hide()
    
    def select_search_list(self):
        self.search_list, _ = QFileDialog.getOpenFileName(self, "Select search list")
        self._input_search_list_button.setText(self.search_list)
        self.session_log("Selected search list '{}'".format(self.search_list))
    
    def search_scanned_item(self):
        self.session_log("Searching for item '{}'".format(self._scanfield.text()))
        self._scanfield.setText("")

    def register_scanned_item(self):
        self.session_log("Registering item '{}' of type '{}'".format(
            self._register_scanfield.text(), self._sample_type.currentText()
        ))
        self._register_scanfield.setText("")
    
    def select_search_fluidx(self):
        self.fluidx, _ = QFileDialog.getOpenFileName(self, "Select FluidX CSV")
        self._fluidx_csv_button.setText(self.fluidx)
        self.session_log("Selected FluidX CSV '{}'".format(self.fluidx))

    def select_register_fluidx(self):
        self.fluidx, _ = QFileDialog.getOpenFileName(self, "Select FluidX CSV")
        self._register_fluidx_csv_button.setText(self.fluidx)
        self.session_log("Selected FluidX CSV '{}'".format(self.fluidx))
    
    def load_search_fluidx(self):
        if self.fluidx:
            self.session_log("Loading FluidX CSV: '{}'".format(self.fluidx))

    def load_register_fluidx(self):
        if self.fluidx:
            self.session_log("Loading FluidX CSV: '{}'".format(self.fluidx))
    
    def update_progressbar(self, value, min=None, max=None):
        if min: self._search_progress.setMinimum(min)
        if max: self._search_progress.setMaximum(max)
        self._search_progress.setValue(value)

    def session_log(self, message):
        self._session_log.append("{datetime}: {message}".format(
            datetime=datetime.now(),
            message=message,
        ))

    def _keypress_event_action(self, key):
        if key.key() == QtCore.Qt.Key_Tab:
            selected_scantype = self.scantype_combo.currentText()
            if selected_scantype == "Search: Search for samples in list(s)":
                self.search_scanned_item()
            elif selected_scantype == "Register: Create sample registration list(s)":
                self.register_scanned_item()
    

if __name__ == '__main__':
    appctxt = AppContext()                      # 4. Instantiate the subclass
    exit_code = appctxt.run()                   # 5. Invoke run()
    sys.exit(exit_code)