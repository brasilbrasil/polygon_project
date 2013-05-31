rootDir = "C:/Users/lfortini/Dropbox/code/polygon_project - Copy/"
inputDir = rootDir + "data/CEs/"
inputCSV1 = rootDir + "data/spp_aux_data.csv"
inputCSV2 = rootDir + "data/tool_aux_data.csv"

#http://www.econpy.org/tutorials/general/csv-pandas-dataframe
#http://pandas.pydata.org/pandas-docs/dev/merging.html
##first instal pandas
import pandas
from pandas import read_csv
df1 = read_csv(inputCSV1)
df2 = read_csv(inputCSV2)
del df1['Unnamed: 0'] #delete
del df2['Unnamed: 0'] #delete
df3=pandas.DataFrame.merge(df1, df2, on="sp_code")
del df3['spp_y'] #delete
df3.rename(columns={'spp_x': 'Species_name'}, inplace=True)
df3.to_csv(rootDir+'output.csv', sep=',', na_rep='') #http://pandas.pydata.org/pandas-docs/dev/generated/pandas.DataFrame.to_csv.html


#pandas data manipulations
print df1
print df1['sp_code']
df1.index
df1.columns
df1['flag'] = df1['Ha'] == 1 #to add column
df1['flag2'] = df1['Oa'] == 1 #to add column
del df1['flag'] #delete
flag2 = df1.pop('flag2') #delete
df1
df1['foo'] = 'bar'
df1





##attempt
import csv
import collections
index = collections.defaultdict(list)

file1= open(inputCSV1, "rb" )
rdr= csv.DictReader(file1)
for row in rdr:
    index[row['sp_code']].append(row)
file1.close()

file2= open( inputCSV2, "rb" )
rdr= csv.DictReader(file2)
for row in rdr:
    print row, index[row['sp_code']]
file2.close()


f1 = csv.reader(open(inputCSV1, 'rb'))
f2 = csv.reader(open(inputCSV2, 'rb'))

mydict = {}
for row in f1:
    mydict[row[0]] = row[1:]

for row in f2:
    mydict[row[0]] = mydict[row[0]].extend(row[1:])

fout = csv.write(open('out.txt','w'))
for k,v in mydict:
    fout.write([k]+v)

##attempt: works but yields cumbersome list
import csv
file1= open( inputCSV1, "rb" )
rdr1= csv.DictReader(file1)

file2= open( inputCSV2, "rb" )
rdr2= csv.DictReader(file2)
    
def test(dictreader1, dictreader2):
    dictreader2 = list(dictreader2)
    matchedlist = []
    for dictline1 in dictreader1:
        for dictline2 in dictreader2:
            if dictline1['sp_code'] == dictline2['sp_code']:
                entry = dictline1.copy()
                entry.update(dictline2)
                matchedlist.append(entry)
    return matchedlist
a=test(rdr1, rdr2)
csv_writer = csv.writer("test_text.csv" [, dialect='excel'])
file1.close()
file2.close()


##attempt
import csv
with open(inputCSV1) as f:
    r = csv.reader(f, delimiter=',')
    dict1 = {row[0]: row[1] for row in r}

with open(inputCSV2) as f:
    r = csv.reader(f, delimiter=',')
    dict2 = {row[0]: row[1] for row in r}

keys = set(dict1.keys() + dict2.keys())
with open(rootDir+'output.csv', 'wb') as f:
    w = csv.writer(f, delimiter=',')
    w.writerows([[key, dict1.get(key, "''"), dict2.get(key, "''")]
                 for key in keys])

