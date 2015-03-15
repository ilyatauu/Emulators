import csv

filename1 = "C:\\Users\\izaides\\Documents\\visual studio 2013\\Projects\\PythonApplication1\\Emulators\\GeneratedProblems\\GeneratedProblems_201411192342\\results_all.csv"
filename2 = "C:\\Users\\izaides\\Documents\\visual studio 2013\\Projects\\PythonApplication1\\Emulators\\GeneratedProblems\\GeneratedProblems_201411192342\\lower_bound.out"
filename3 = "C:\\Users\\izaides\\Documents\\visual studio 2013\\Projects\\PythonApplication1\\Emulators\\GeneratedProblems\\GeneratedProblems_201411192342\\upper_bound.out"

filename_out = "C:\\Users\\izaides\\Documents\\visual studio 2013\\Projects\\PythonApplication1\\Emulators\\GeneratedProblems\\GeneratedProblems_201411192342\\joined.csv"

with open(filename1, 'rb') as csvfile:
    data1 = list(csv.reader(csvfile, delimiter=','))

with open(filename2, 'rb') as csvfile:
    data2 = list(csv.reader(csvfile, delimiter=','))

with open(filename3, 'rb') as csvfile:
    data3 = list(csv.reader(csvfile, delimiter=','))

found = set()
ind = False

with open(filename_out, 'wb') as csvfile:
    writer = csv.writer(csvfile, delimiter=',')
    for d1 in data1:
        ind = False
        for d2 in data2:
            if d2[0] in found:
                continue
            for d3 in data3:
                if d3[0] in found:
                    continue
                if d1[0].replace(".out", "") == d2[0] and d2[0] == d3[0]:
                    writer.writerow(d1+d2+d3)
                    found.add(d2[0])
                    ind = True
                    break
            if ind is True:
                break

    # for r in[d1 + d2 for d1 in data1 for d2 in data2 for d3 in data3 if d1[0] == d2[0] and d1[0] == d3[0]]:
    #    writer.writerow(r)