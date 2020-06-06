import csv

with open('medicationlog2.csv','w', newline='') as f:
    thewriter = csv.DictWriter(f, fieldnames= ['date','time', 'authentication'])
    thewriter.writeheader()
