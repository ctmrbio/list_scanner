#!/usr/bin/env python3
"""
CTMR list scanning application.
"""
__author__ = "Fredrik Boulund"
__date__ = "2018"

import logging
from pathlib import Path
from datetime import datetime

import pyforms
from pyforms import BaseWidget
from pyforms.controls import (
    ControlLabel, ControlDir, ControlText, ControlButton, 
    ControlFile, ControlProgress, ControlTextArea, 
    ControlCheckBox, ControlImage, ControlList
)
from AnyQt import QtCore
import cv2

from sample_list import SampleList, ScannedSampleDB


class ListScanner(BaseWidget):

    def __init__(self):
        super(ListScanner, self).__init__("CTMR list scanner")

        self.mainmenu = [
            {"File": [
                {"Export old session from DB": self._export_old_session},
                '-',
                {"Exit": self.__exit_button_action},
            ]},
        ]

        self.inputfile = ''
        self.sample_lists = ''
        self.dbfile = "CTMR_scanned_items.sqlite3"
        self.db = ScannedSampleDB(dbfile=self.dbfile)
        self.has_saved = False

        self._toplogo = ControlImage()
        self._toplogo.value = cv2.imread("img/CTMR_logo_white_background.jpg")
        self._toptext = ControlLabel('\n'.join([
            "CTMR item scanning application.",
            "Instructions:",
            " 1. Load a list file (Excel, CSV, TSV, or white-space separated text).",
            "    List files can have several columns and optionally a header line on top.",
            " 2. Focus in the scanning field and start scanning.",
            " 3. Select an output file.",
            " 4. Press 'Save and exit' to save a record of the current session and exit.",
            " NOTE: The TAB and ENTER keys have been hardcoded to submit a scanned item,",
            "       you thus need to use the mouse to switch between GUI buttons and fields.",
            ])
        )
        self._inputfile = ControlFile(label="Input list", helptext="csv, tsv, or xlsx")
        self._headers_checkbox = ControlCheckBox(label="List has headers")
        self._load_button = ControlButton(label="Load input file")
        self._load_button.value = self.__load_inputfile

        self._scanfield = ControlText(label="Scan item here:")
        self._scanbutton = ControlButton(label="Check for item in list(s)")
        self._scanbutton.value = self.__scanbutton_action
        self._progress = ControlProgress(label="%p% items scanned")
        self._textarea = ControlTextArea(label="Session log:")
        
        self._outputfolder = ControlDir(label="Output folder",
            helptext="Folder to write summary report to."
        )
        self._save_button = ControlButton("Save report")
        self._save_button.value = self.__save_button_action
        self._exit_button = ControlButton("Exit")
        self._exit_button.value = self.__exit_button_action

        self.formset = [
            ('_toptext', ' ', '_toplogo'),
            ('_inputfile', '_headers_checkbox', '_load_button'),
            ('_scanfield', '_scanbutton', '_progress'),
            '_textarea',
            ('_outputfolder', '_save_button', ' '),
            (' ', '_exit_button', ' '),
            ' ',
        ]

        self.keyPressEvent = self.__keypress_event_action
        self.focusNextPrevChild = lambda x: False  # Disable Qt intercepting TAB keypress event
    
    def __keypress_event_action(self, key):
        if (key.key() == QtCore.Qt.Key_Enter 
            or key.key() == QtCore.Qt.Key_Return
            or key.key() == QtCore.Qt.Key_Tab):
            logging.debug(f"Pressed Enter/Return or Tab")
            self.__scanbutton_action()

    def _sessionlog(self, message):
        self._textarea.__add__(f"{datetime.now()}: {message}")

    def __load_inputfile(self):
        filename = self._inputfile.value
        if Path(filename).is_file():
            self.db.register_session(filename)
            self.sample_lists = SampleList(filename, self.db, self._headers_checkbox.value)
            self._sessionlog(f"Started new session: {self.db.session_id}")
            self._sessionlog(f"Loaded {filename} containing {self.sample_lists.total_items} items.")
            self._progress.max = self.sample_lists.total_items
            self.has_saved = False
        else:
            self._sessionlog(f"Cannot load file '{filename}'."
                " Try loading different file!"
            )

    def __scanbutton_action(self):
        scanned_item = self._scanfield.value
        if not scanned_item:
            return False
        item = self.db.find_item(scanned_item)
        if item.id:
            self._sessionlog(f"Found item {item.item} in column {item.column}")
        else:
            self._sessionlog(f"WARNING: Could not find item {item.item} in lists!")
        self.db.register_scanned_item(item)
        scanned_items = self.db.get_items_scanned_in_session(self.db.session_id)
        distinct_scanned_items = set((item[1:] for item in scanned_items))
        self._progress.value = len(distinct_scanned_items)
        if self._progress.value == self._progress.max:
            self._sessionlog(f"COMPLETED: All {self.sample_lists.total_items} items"
                f" in file {self.sample_lists.filename} have been scanned."
            )
        self._scanfield.value = ""

    def __save_button_action(self):
        outfolder = Path(self._outputfolder.value)
        if outfolder.is_dir():
            input_basename = Path(self._inputfile.value).stem
            fn_datetime = self.db.session_datetime.replace(":", "-").replace(" ", "_")
            session_basename = Path(f"{fn_datetime}_{self.db.session_id}_{input_basename}")
            session_report = outfolder / session_basename.with_suffix(".csv")
            self.db.export_session_report(session_report)
            self._sessionlog(f"Saved scanning session report to: {session_report}")
            session_log = outfolder / session_basename.with_suffix(".log")
            with open(session_log, 'w') as outf:
                outf.write(self._textarea.value)
                logging.debug("Wrote session log to %s", session_log)
            self.has_saved = True
        else:
            self._sessionlog("Uh uh uh,"
                " you didn't say the magic word!"
                " (no output directory specified)"
            )
    
    def _export_old_session(self):
        session_list_window = ExportOldSession()
        session_list_window.parent = self
        session_list_window.show()
    
    def __exit_button_action(self):
        if self.has_saved:
            exit()
        else:
            self._sessionlog("Exit button pressed,"
                " but session log hasn't been saved."
                " Press again to confirm exit!"
            )
            self.has_saved = True


# TODO: incomplete
class ExportOldSession(BaseWidget):
    def __init__(self):
        super(ExportOldSession, self).__init__("Export old session")

        self.dbfile = "CTMR_scanned_items.sqlite3"
        self.db = ScannedSampleDB(dbfile=self.dbfile)

        self._session_list = ControlList(label=f"Old sessions in DB: {self.dbfile}")
        self._session_list.horizontal_headers = ["Datetime", "Filename", "Session"]
        self._session_list.select_entire_row = True
        self._session_list.readonly = True

        self._outputfolder = ControlDir(label="Output folder",
            helptext="Folder to write summary report to."
        )
        self._export_button = ControlButton(label="Export report")
        self._export_button.value = self._export_button_action

        self._populate_session_list()

        self._formset = [
            '_session_list',
            ('_outputfolder', '_export_button'),
        ]
    
    def _populate_session_list(self):
        for session in self.db.get_sessions_list():
            self._session_list += session
    
    def _export_button_action(self):
        datetime, list_filename, session_id = self._session_list.value[self._session_list.selected_row_index]
        outfolder = Path(self._outputfolder.value)
        if outfolder.is_dir():
            input_basename = Path(list_filename).stem
            fn_datetime = datetime.replace(":", "-").replace(" ", "_")
            session_basename = Path(f"{fn_datetime}_{session_id}_{input_basename}")
            session_report = outfolder / session_basename.with_suffix(".csv")
            self.db.export_session_report(session_report)
            self._sessionlog(f"Saved scanning session report to: {session_report}")
            self.has_saved = True
        self.close()



if __name__ == "__main__":
    pyforms.start_app(ListScanner)