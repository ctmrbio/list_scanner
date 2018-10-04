from pathlib import Path
from collections import defaultdict
import logging
import csv 

def read_list(filename, header=False):
    """Read potentially multicolumn list file.

    Returns: 
        items   {"column": [item, item, item, ...]}
                Each column represented by a list,
                indexed by column name.
    """
    if Path(filename).suffix.lower() in (".xlsx", ".xls"):
        logging.info("Found excelfile %s", filename)
        delimiter = "excel"
    elif Path(filename).suffix.lower() in (".csv"):
        logging.info("Found csv %s", filename)
        delimiter = ","
    elif Path(filename).suffix.lower() in (".tsv"):
        logging.info("Found tsv %s", filename)
        delimiter = "\t"
    else:
        logging.info("Found %s, assuming whitespace separated", filename)
        delimiter = " "

    items = defaultdict(list)
    with open(filename) as f:
        ncols = len(f.readline().split(delimiter))
        f.seek(0)  

        if header:
            fieldnames = None  # Tell csv.DictReader use first row as headers
        else:
            fieldnames = list(range(1, ncols+1))
        
        if delimiter == "excel":
            dict_reader = excel_dict_reader(filename, fieldnames)
        elif delimiter == " ":
            dict_reader = csv.DictReader(f, fieldnames=fieldnames, delimiter=delimiter, skipinitialspace=True)
        else:
            dict_reader = csv.DictReader(f, fieldnames=fieldnames, delimiter=delimiter)

        for row in dict_reader:
            for column, item in row.items():
                items[column].append(item)
    return items


def excel_dict_reader(filename, fieldnames):
    """Read potentially multicolumn list from Excel file.

    Yields {"column": "item", ...} objects like csv.DictReader.
    """
    return {"Column": "Sample1"}
