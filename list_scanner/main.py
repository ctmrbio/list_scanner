#!/usr/bin/env python3.6
"""CTMR list scanner"""
__author__ = "Fredrik Boulund"
__date__ = "2018"

from datetime import datetime
from pathlib import Path
import sys

import enaml
from enaml.qt.qt_application import QtApplication

from sample_list import SampleList, ScannedSampleDB

if __name__ == "__main__":
    app = QtApplication()

    with enaml.imports():
        from list_enaml import ListScanner

    view = ListScanner()
    view.show()

    app.start()