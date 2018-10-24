#!/usr/bin/env python3.5
"""CTMR list scanner"""
__author__ = "Fredrik Boulund"
__date__ = "2018"
__version__ = "0.3.0b"

from datetime import datetime
from pathlib import Path
import sys

from fbs_runtime.application_context import ApplicationContext, cached_property
from PyQt5 import QtCore
from PyQt5.QtWidgets import (
    QWidget, QGridLayout, QGroupBox, QFormLayout, QVBoxLayout, QHBoxLayout,
    QPushButton, QFileDialog, QLineEdit, QProgressBar, QLabel, QCheckBox, 
    QTextEdit, QRadioButton, QComboBox, QMenuBar, QListView, QTableView
)
from PyQt5.QtGui import QPixmap

# Handle sneaky hidden pandas imports for PyInstaller
import pandas._libs.tslibs.np_datetime
import pandas._libs.tslibs.nattype
import pandas._libs.skiplist

from sample_list import SampleList, ScannedSampleDB, __version__ as sample_list_version

class AppContext(ApplicationContext):           # 1. Subclass ApplicationContext
    def run(self):                              # 2. Implement run()
        self.window.setWindowTitle("CTMR List Scanner version {} (SampleList: version {})".format(
            __version__, sample_list_version
        ))
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
        self.sample_list = None
        self.dbfile = "CTMR_scanned_items.sqlite3"
        self.db = ScannedSampleDB(dbfile=self.dbfile)
        self._session_saved = False

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
        self._headers_checkbox = QCheckBox("Headers")
        load_search_list_button = QPushButton("Load search list")
        load_search_list_button.clicked.connect(self.load_search_list)
        
        search_layout = QFormLayout()
        list_headers_hbox = QHBoxLayout()
        list_headers_hbox.addWidget(self._input_search_list_button)
        list_headers_hbox.addWidget(self._headers_checkbox)
        search_layout.addRow("1. Select list:", list_headers_hbox)
        search_layout.addRow("2. Load list:", load_search_list_button)
        self._search_list_group = QGroupBox("Select list of samples to search for")
        self._search_list_group.setLayout(search_layout)

        # Search: Manual scan
        self._scanfield = QLineEdit(placeholderText="Scan/type item ID")
        search_scan_button = QPushButton("Search for item")
        search_scan_button.clicked.connect(self.scan_button_action)

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
        self._select_sample_type_label = QLabel("Select sample type:")
        self._select_sample_box_label = QLabel("Select box name:")
        self._register_box = QLineEdit(placeholderText="Box name")
        self._register_scanfield = QLineEdit(placeholderText="Scan/type item ID")
        register_scan_button = QPushButton("Register item")
        register_scan_button.clicked.connect(self.register_scanned_item)

        register_fluidx_layout = QFormLayout()
        register_fluidx_layout.addRow("Select FluidX CSV:", self._register_fluidx_csv_button)
        register_fluidx_layout.addRow("Load FluidX CSV:", self._load_register_fluidx_csv_button)
        register_sample_type_hbox = QHBoxLayout()
        register_sample_type_hbox.addWidget(self._select_sample_type_label)
        register_sample_type_hbox.addWidget(self._sample_type)
        register_sample_type_hbox.addWidget(self._select_sample_box_label)
        register_sample_type_hbox.addWidget(self._register_box)
        register_scan_hbox = QHBoxLayout()
        register_scan_hbox.addWidget(self._register_scanfield)
        register_scan_hbox.addWidget(register_scan_button)
        register_fluidx_layout.addRow(register_sample_type_hbox)
        register_fluidx_layout.addRow(register_scan_hbox)
        self._register_fluidx_group = QGroupBox("Register: Create sample registration lists")
        self._register_fluidx_group.setLayout(register_fluidx_layout)

        # Session log 
        self._session_log = QTextEdit()
        self._search_progress = QProgressBar()
        self._search_progress.setMinimum(0)
        self._search_progress.setMaximum(0)
        self.save_button = QPushButton("Save current session log")
        self.save_button.clicked.connect(self.save_report)
        self.export_button = QPushButton("Export log from old session")
        self.export_button.clicked.connect(self.export_sample_list)
        self.exit_button = QPushButton("Exit")
        self.exit_button.clicked.connect(self.exit)
        session_log_layout = QVBoxLayout()
        session_log_layout.addWidget(self._search_progress)
        session_log_layout.addWidget(self._session_log)
        button_row = QHBoxLayout()
        button_row.addWidget(self.save_button)
        button_row.addWidget(self.export_button)
        button_row.addWidget(self.exit_button)
        session_log_layout.addLayout(button_row)
        self._session_log_group = QGroupBox("Session log")
        self._session_log_group.setLayout(session_log_layout)

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
        self.session_log("Started CTMR List Scanner version {} (SampleList: version {})".format(
            __version__, sample_list_version,
        ))
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
            self._search_progress.show()
            self._session_log_group.show()
        elif selected_scantype == "Register: Create sample registration list(s)":
            self.scantype_combo.show()
            self._search_list_group.hide()
            self._manual_scan_group.hide()
            self._search_fluidx_group.hide()
            self._register_fluidx_group.show()
            self._search_progress.hide()
            self._session_log_group.show()
    
    def select_search_list(self):
        self.search_list, _ = QFileDialog.getOpenFileName(self, "Select search list")
        self._input_search_list_button.setText(self.search_list)
        self.session_log("Selected search list '{}'".format(self.search_list))
    
    def load_search_list(self):
        if Path(self.search_list).is_file():
            self.db.register_session(self.search_list)
            self.sample_list = SampleList(
                self.search_list,
                self.db,
                self._headers_checkbox.isChecked()
            )
            self.session_log("Started new session: {}".format(
                self.db.session_id
            ))
            self.session_log("Loaded {} containing {} items.".format(
                self.search_list,
                self.sample_list.total_items,
            ))
            self._search_progress.setMaximum(self.sample_list.total_items)
        else:
            self.session_log("Cannot load file '{}'.".format(
                self.search_list
            ))
    
    def scan_button_action(self):
        scanned_item = self._scanfield.text()
        if not scanned_item:
            return False
        item = self.search_scanned_item(scanned_item)
        if item.id:
            self.session_log("Found item {} in column {}".format(
                item.item, item.column,
            ))
        else:
            self.session_log("Could not find item {} in lists.".format(
                item.item
            ))
        self._scanfield.setText("")
    
    def search_scanned_item(self, scanned_item):
        item = self.db.find_item(scanned_item)
        self.db.register_scanned_item(item)

        # Update progressbar
        scanned_items = self.db.get_items_scanned_in_session(self.db.session_id)
        distinct_scanned_items = set((item[1:] for item in scanned_items))
        self._search_progress.setValue(len(distinct_scanned_items))
        if self._search_progress.value == self._search_progress.maximum:
            self.session_log("COMPLETED: All {} items ".format(
                self.sample_list.total_items
                ) + "in file {} have been scanned.".format(
                self.sample_list.filename
                )
            )
        return item

    def register_scanned_item(self):
        self.session_log("Registering item '{}' of type '{}'".format(
            self._register_scanfield.text(), self._sample_type.currentText()
        ))
        self._register_scanfield.setText("")
    
    def select_search_fluidx(self):
        self.fluidx, _ = QFileDialog.getOpenFileName(self, "Select FluidX CSV")
        self._search_fluidx_csv_button.setText(self.fluidx)
        self.session_log("Selected FluidX CSV '{}'".format(self.fluidx))

    def select_register_fluidx(self):
        self.fluidx, _ = QFileDialog.getOpenFileName(self, "Select FluidX CSV")
        self._register_fluidx_csv_button.setText(self.fluidx)
        self.session_log("Selected FluidX CSV '{}'".format(self.fluidx))
    
    def load_search_fluidx(self):
        if not Path(self.fluidx).is_file():
            self.session_log("ERROR: Cannot load FluidX file")
            return
        if not self.sample_list:
            self.session_log("ERROR: Load search list before loading FluidX file.")
            return
        self.session_log("Loading items from FluidX CSV: '{}'".format(self.fluidx))
        scanned_items = self.sample_list.scan_fluidx_list(self.fluidx)
        for position, barcode, _, rack_id in scanned_items:
            item = self.search_scanned_item(barcode)
            if item.id:
                self.session_log("Found item {} from pos {} in rack {} of type {}.".format(
                    item.item, position, rack_id, item.column,
                ))
            else:
                self.session_log("Could not find item {} in lists!".format(
                    item.item
                ))

    def load_register_fluidx(self):
        if self.fluidx:
            self.session_log("Loading FluidX CSV: '{}'".format(self.fluidx))
    
    def session_log(self, message):
        self._session_log.append("{datetime}: {message}".format(
            datetime=datetime.now(),
            message=message,
        ))
    
    def save_report(self):
        if not self.search_list:
            self.session_log("ERROR: Cannot save report without first loading search list.")
            return
        outfolder = QFileDialog.getExistingDirectory(self, "Select directory to save report to")
        if Path(outfolder).is_dir():
            input_stem = Path(self.search_list).stem
            fn_datetime = self.db.session_datetime.replace(":", "-").replace(" ", "_")
            session_basename = Path("{}_{}_{}".format(
                fn_datetime, self.db.session_id, input_stem,
            ))
            session_report = outfolder / session_basename.with_suffix(".csv")
            self.db.export_session_report(str(session_report))
            self.session_log("Saved scanning session report to: {}".format(session_report))
            session_log = outfolder / session_basename.with_suffix(".log")
            with open(str(session_log), 'w') as outf:
                outf.write(self._session_log.toPlainText())
                self.session_log("Wrote session log to {}".format(session_log))
            self._session_saved = True
        else:
            self.session_log("ERROR: Could not save report to {}".format(outfolder))
    
    def export_sample_list(self):
        self.export_old_session_window = ExportOldSessionWindow(self, dbfile=self.dbfile)
        self.export_old_session_window.show()
    
    def exit(self):
        if self._session_saved:
            exit()
        else:
            self.session_log("Exit button pressed,"
                " but session log hasn't been saved."
                " Press again to confirm exit!"
            )
            self._session_saved = True


    def _keypress_event_action(self, key):
        if key.key() == QtCore.Qt.Key_Tab:
            selected_scantype = self.scantype_combo.currentText()
            if selected_scantype == "Search: Search for samples in list(s)":
                self.scan_button_action()
            elif selected_scantype == "Register: Create sample registration list(s)":
                self.register_scanned_item()
    

class ExportOldSessionWindow(QWidget):
    def __init__(self, parent, dbfile):
        super(ExportOldSessionWindow, self).__init__()
        self.setWindowTitle("Export old scanning session")
        self.resize(700, 400)
        self.db = ScannedSampleDB(dbfile=dbfile)
        self._parent = parent

        self.session_list = QTableView()
        self.session_list.setShowGrid(False)
        self.session_list.setSelectionBehavior(1)  # Select only rows
        self.session_list.setSortingEnabled(True)
        header = ["Datetime", "List filename", "Session ID"]
        self.session_list.setModel(SessionTableModel(header=header, table_data=self.db.get_sessions_list()))
        self.session_list.resizeColumnsToContents()
        self.session_list.resizeRowsToContents()

        self.export_button = QPushButton("Export log from selected session")
        self.export_button.clicked.connect(self.export_session)
        self.close_button = QPushButton("Close")
        self.close_button.clicked.connect(self.close_window)

        layout = QGridLayout()
        layout.addWidget(self.session_list, 0, 0, 1, 2)
        layout.addWidget(self.export_button, 1, 0, 1, 1)
        layout.addWidget(self.close_button, 1, 1, 1, 1)
        self.setLayout(layout)

    @staticmethod
    def grouper(iterable, n):
        """ Group iterable into n-size groups. `iterable` must have a multiple of `n` values."""
        grouped = []
        current_group = []
        for idx, thing in enumerate(iterable, start=1):
            current_group.append(thing)
            if idx % 3 == 0:
                grouped.append(current_group)
                current_group = []
        return grouped

    def export_session(self):
        outfolder = QFileDialog.getExistingDirectory(self, "Select directory to export session report to")
        if Path(outfolder).is_dir():
            for selected_row in self.grouper(self.session_list.selectedIndexes(), 3):
                selected_data = [
                    self.session_list.model().data(selected_row[0], QtCore.Qt.DisplayRole),
                    self.session_list.model().data(selected_row[1], QtCore.Qt.DisplayRole),
                    self.session_list.model().data(selected_row[2], QtCore.Qt.DisplayRole),
                ]
                self._export_session_to_folder(
                    outfolder=outfolder,
                    datetime=selected_data[0],
                    filename_stem=Path(selected_data[1]).stem,
                    session_id=selected_data[2],
                )
        else:
            self._parent.session_log("ERROR: No valid output folder selected")


    def _export_session_to_folder(self, outfolder, datetime, filename_stem, session_id):
        fn_datetime = datetime.replace(":", "-").replace(" ", "_")
        session_basename = Path("{}_{}_{}".format(
            fn_datetime, session_id, filename_stem,
        ))
        session_report = outfolder / session_basename.with_suffix(".csv")
        self.db.export_session_report(str(session_report), session_id=session_id)
        self._parent.session_log("Saved scanning session report to: {}".format(session_report))
    
    def close_window(self):
        self.hide()


class SessionTableModel(QtCore.QAbstractTableModel):
    def __init__(self, header, table_data):
        super(SessionTableModel, self).__init__()
        self.header = header
        self.table_data = table_data

    def rowCount(self, parent):
        return len(self.table_data)
    
    def columnCount(self, parent):
        return len(self.header)
    
    def data(self, index, role):
        if not index.isValid():
            return None
        if role == QtCore.Qt.DisplayRole:
            return self.table_data[index.row()][index.column()]

    def headerData(self, col, orientation, role):
        if orientation == QtCore.Qt.Horizontal and role == QtCore.Qt.DisplayRole:
            return self.header[col]
        return None
    
    def sort(self, ncol, order):
        self.table_data = sorted(self.table_data, key=lambda row: row[ncol])
        if order == QtCore.Qt.DescendingOrder:
            self.table_data.reverse()
        self.layoutChanged.emit()




if __name__ == '__main__':
    appctxt = AppContext()                      # 4. Instantiate the subclass
    exit_code = appctxt.run()                   # 5. Invoke run()
    sys.exit(exit_code)