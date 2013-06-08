rootDir = "C:/Users/lfortini/Dropbox/code/polygon_project/"
#rootDir = "E:/Cloud/Github/polygon_project/"
inputDir = rootDir + "data/CEs/"
inputCSV1 = rootDir + "data/merge_test_data1.csv"
inputCSV2 = rootDir + "data/merge_test_data2.csv"
outputCSV = "test.csv"

import csv

# Function to merge two dictionaries based on a matching field
# http://stackoverflow.com/questions/9483051/join-two-csv-files-in-python-using-dictreader
def test(dictreader1, dictreader2):
    dictreader2 = list(dictreader2)
    matchedlist = []
    for dictline1 in dictreader1:
        for dictline2 in dictreader2:
            # "Join" the records based on the sp_code field
            if dictline1['sp_code'] == dictline2['sp_code']:
                entry = dictline1.copy()
                # The update function will add the dictionary line 1 and 2
                # together and drop any matching fields.
                entry.update(dictline2)
                matchedlist.append(entry)
    return matchedlist


# --- START PROCESSING CSV FILES --- #

# Read input csv files as dictionaries
file1 = open( inputCSV1, "rb" )
rdr1 = csv.DictReader(file1)

file2 = open( inputCSV2, "rb" )
rdr2 = csv.DictReader(file2)

# Call the matching and appending function
a = test(rdr1, rdr2)

# Close access to the csv files
file1.close()
file2.close()


# Read the input csv files again as raw csvs
# Get the field names from each csv
headerFile1 = open(inputCSV1, "rb" )
reader = csv.reader(headerFile1)
headers = reader.next()

headerFile2 = open(inputCSV2, "rb" )
reader2 = csv.reader(headerFile2)
headers2 = reader2.next()

# Build a single list of fieldnames
for hdrElement in headers2:
    if hdrElement not in headers:
        headers.append(hdrElement)

# Create the ouput CSV
f = open(outputCSV, "wb")
outWriter = csv.DictWriter(f, delimiter=',', fieldnames=headers)
outWriter.writer.writerow(headers)
outWriter.writerows(a)
f.close()

# Close access to the csv files
headerFile1.close()
headerFile2.close()