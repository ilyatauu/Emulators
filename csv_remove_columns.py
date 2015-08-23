__author__ = 'izaides'

import os
import csv

def select_filter(name):
    sname = name.split('_', 1)
    if len(sname) == 1:
        return True
    if sname[1] in ["solution", "solution_time"]:
        return True
    return False

filename = r"C:\Users\izaides\PycharmProjects\Emulators\Problem Sets\SmallToMedium\ProblemsWithP60_80\results_tbased.csv"
outfilename = r"C:\Users\izaides\PycharmProjects\Emulators\Problem Sets\SmallToMedium\ProblemsWithP60_80\results_tbased_selected.csv"

with open(filename, 'rb') as fr, open(outfilename, 'wb') as fw:
    reader = csv.reader(fr, dialect='excel')
    writer = csv.writer(fw, dialect='excel')
    header = reader.next()

    names = dict(zip(header, range(0, len(header))))
    selected_fields = filter(select_filter, header)
    selected_indices = [names[x] for x in selected_fields]
    writer.writerow([header[i] for i in selected_indices])
    for r in reader:
        wr = [r[i] for i in selected_indices]
        writer.writerow(wr)



