# Abozar Alizadeh
import sys
from csv import reader
from helpers import *


if __name__ == '__main__':
    arguments = sys.argv
    if len(arguments) < 2:
        raise Exception("Please pass input log file\n"
                        "For example: python http_log_monitoring.py LOG_FILE.csv")

    path_to_log_file = arguments[1]
    with open(path_to_log_file, 'r') as read_obj:
        # pass the file object to reader() to get the reader object
        csv_reader = reader(read_obj)
        # drop header
        header = next(csv_reader)
        # create log analyzer
        analyzer = AnalyzeLogs()
        # Iterate over each row in the csv using reader object without loading the whole file in memory
        for row in csv_reader:
            # row variable is a list that represents a row in csv
            analyzer.execute(HttpLog(*row))
