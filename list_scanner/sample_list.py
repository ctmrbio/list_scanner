from pathlib import Path
from uuid import uuid1
from datetime import datetime
from collections import namedtuple
import logging
import sqlite3
import csv

import tabulator

Item = namedtuple("Item", ["id", "item", "column"])
DATETIME_FMT = "%Y-%m-%d %H:%M:%S"

class ScannedSampleDB():
    """
    Small on-disk SQLite3 database persisting records of all items
    observed in input lists and all items scanned in a session.
    """

    def __init__(self, dbfile):
        if not Path(dbfile).is_file():
            self.initiate_new_db(dbfile)
        else:
            self.db = sqlite3.connect(dbfile)
        self.session_id = ""
        self.session_datetime = ""

    def initiate_new_db(self, dbfile):
        self.db = sqlite3.connect(dbfile)
        self.db.executescript(
            """
            DROP TABLE IF EXISTS session;
            DROP TABLE IF EXISTS item;
            DROP TABLE IF EXISTS scanned_item;
            CREATE TABLE session (
                id TEXT PRIMARY KEY,
                filename TEXT,
                datetime TEXT
            );
            CREATE TABLE item (
                id INTEGER PRIMARY KEY,
                session TEXT, 
                column TEXT,
                item TEXT,
                FOREIGN KEY(session) REFERENCES session(id)
            );
            CREATE TABLE scanned_item (
                id INTEGER,
                session TEXT,
                item TEXT,
                scanned_datetime TEXT,
                FOREIGN KEY(session) REFERENCES session(id)
            )
            """
        )
        self.db.commit()

    def register_session(self, filename):
        """
        Register a session.
        """
        self.session_id = str(uuid1())
        self.session_datetime = datetime.now().strftime(DATETIME_FMT)
        session_data = (self.session_id, filename, self.session_datetime)
        logging.debug(session_data)
        self.db.execute(
            """
            INSERT INTO session VALUES (
                ?, ?, ?
            )
            """,
            session_data
        )
        self.db.commit()

    def register_items(self, itemlists):
        """
        Register items parsed from a potentially multi-column input file.
        """
        return -1
        total_items = 0
        for column, items in itemlists.items():
            if isinstance(column, str):
                column = column.strip()
            items = [str(item).strip() for item in items if not pd.isnull(item)]
            logging.debug("Inserting {} items from column named '{}'".format(
                len(items),
                column
            ))
            items_to_insert = [(self.session_id, column, item) for item in items]
            self.db.executemany(
                """
                INSERT INTO item (session, column, item) 
                VALUES (?, ?, ?)
                """,
                items_to_insert
            )
            total_items += len(items_to_insert)
        self.db.commit()
        return total_items
    
    def find_item(self, search_item):
        """
        Search for item in current session list(s).
        """
        result = self.db.execute(
            """
            SELECT id, column 
            FROM item i
            WHERE i.item = (?) AND i.session = (?)
            """,
            [search_item, self.session_id]
        ).fetchall()

        if len(result) > 1:
            logging.error("Found more than one item match for '%s'!", search_item)
        try:
            item_id, column = result[0]
            item = Item(item_id, search_item, column)
        except IndexError:
            item = Item("", search_item, "")

        return item

    def register_scanned_item(self, item):
        self.db.execute(
            """
            INSERT INTO scanned_item
            VALUES (?, ?, ?, ?)
            """,
            (item.id, self.session_id, item.item, datetime.now().strftime(DATETIME_FMT))
        )
        self.db.commit()
    
    def get_items_scanned_in_session(self, session):
        result = self.db.execute(
            """
            SELECT si.scanned_datetime, si.item, i.column
            FROM scanned_item AS si
            JOIN item AS i
            WHERE si.id = i.id AND si.session = ?
            """,
            [session]
        ).fetchall()
        return result
    
    def get_items_not_scanned_in_session(self, session):
        result = self.db.execute(
            """
            SELECT DISTINCT i.item, i.column
            FROM item AS i
            WHERE i.item NOT IN (
                SELECT si.item 
                FROM scanned_item AS si
                WHERE si.session = ?
            )
            """,
            [session]
        ).fetchall()
        return result
    
    def get_sessions_list(self):
        result = self.db.execute(
            """
            SELECT datetime, filename, id
            FROM session
            """
        ).fetchall()
        return result

    def export_session_report(self, report_filename):
        logging.info("Exporting {} to {}".format(
            self.session_id,
            report_filename,
        ))
        scanned_items = self.get_items_scanned_in_session(self.session_id)
        not_scanned_items = self.get_items_not_scanned_in_session(self.session_id)
        with open(report_filename, 'w') as outfile:
            outfile.write("Datetime; Item; Column\n")
            for item in scanned_items:
                outfile.write("{}; {}; {}\n".format(
                    item[0], item[1], item[2],
                ))
            for item in not_scanned_items:
                outfile.write(";{}; {}\n".format(
                    item[0], item[1],
                ))

    

class SampleList():

    def __init__(self, filename, db, header=False):
        self.db = db
        self.total_items = -1
        self.filename = filename
        self.header = header
        self.read_lists()
    
    def read_lists(self):
        if self.header:
            header = 0  # Pandas needs the rownumber of the header
            logging.debug("Reading data with headers on row 0")
        else:
            header = None  # Pandas needs None instead of False
            logging.debug("Reading data without headers")

        if Path(self.filename).suffix.lower() in (".xlsx", ".xls"):
            logging.info("Found excelfile %s", self.filename)
            #items = pd.read_excel(self.filename, header=header)
        elif Path(self.filename).suffix.lower() in (".csv"):
            logging.info("Found csv %s", self.filename)
            #items = pd.read_csv(self.filename, header=header, sep=',')
        elif Path(self.filename).suffix.lower() in (".tsv"):
            logging.info("Found tsv %s", self.filename)
            #items = pd.read_csv(self.filename, header=header, sep='\t')
        else:
            logging.info("Found %s, assuming whitespace separated", self.filename)
            #items = pd.read_csv(self.filename, header=header, engine="python", sep=r'\s+')
        #logging.info("Data shape is (rows, columns): %s", items.shape)
        #self.total_items = self.db.register_items(items.to_dict(orient="list"))

    @staticmethod
    def scan_fluidx_list(fluidx_file):
        #items = pd.read_csv(fluidx_file, header=None)
        #logging.info("FluidX shape is (rows, columns): %s", items.shape)
        return items.values.tolist()




        


