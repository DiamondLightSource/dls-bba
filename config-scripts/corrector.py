import csv
import numpy as np
from numpy.lib.recfunctions import append_fields


CORRECTORS_TXT = "/dls_sw/prod/R3.14.12.3/support/fastfeedback/12-3/fofbApp/opi/correctors.txt"
HEADERS = "epics, ioc, card, slot, link, farow, mml1, slow"
SPECIAL = [
    "SR02A-PC-HSCOR-01", "SR02A-PC-HSCOR-02", "SR09S-PC-HSTR-01", "SR09S-PC-HSTR-02", 
    "SR13S-PC-HSTR-01", "SR13S-PC-HSTR-02", "SR02A-PC-VSCOR-01", "SR02A-PC-VSCOR-02", 
    "SR09S-PC-VSTR-01", "SR09S-PC-VSTR-02", "SR13S-PC-VSTR-01", "SR13S-PC-VSTR-02"]

def open_file(filepath):
    with open(filepath, "r", encoding='utf8', newline="") as file:
        data = np.genfromtxt(file, names=True, dtype=None, encoding="UTF-8")
    return data

def add_column(file):
    zeros = []
    for row in file:
        zeros.append("0")
    new_data = append_fields(file, "slow", zeros)
    return new_data

def sort_slow(file):
    for row in file:
        if row[0] in SPECIAL:
            row[7] = "1"
    return file

def save_file(file):
    np.savetxt("correctors.csv", file, header = HEADERS, delimiter = ",", fmt='%s')


def append_slow():
    """MAIN"""
    file = open_file(CORRECTORS_TXT)
    file = add_column(file)
    file = sort_slow(file)
    save_file(file)


def main():
    append_slow()


if __name__ == "__main__":
    main()