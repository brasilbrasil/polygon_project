import arcpy, os, csv, shutil

# Set path to the root folder for input data
rootDir = arcpy.GetParameterAsText(0)

# Input variables
islandDir = rootDir + "\\data\\Islands\\"
outputDir = rootDir + "\\output\\"
hawaiiFC = "Main_Hawaiian_Islands_simple2.shp"
hawaiiFCPath = islandDir + hawaiiFC
fgdb = "species.gdb"
outputGDB = outputDir + fgdb
csvHeader = "spec_name,sp_code,vulner_idx,presence,cur_overlap_pct,fut_overlap_pct\n"

# Set environment
arcpy.env.workspace = outputDir
arcpy.env.overwriteOutput = True

# Set path to input selection polygon shapefile
selectionFC = arcpy.GetParameterAsText(1)

# Set the full path of the initial output CSV file
# The default is the current directory of the script/toolbox +
# protected_area_shapefile_folder/protected_area_vulnerability_report.csv
# That path is configured in the toolbox.
outputCSVPath = arcpy.GetParameterAsText(2)
outputCSVFolder = outputCSVPath.rsplit('\\',1)[0]
outputCSVName = outputCSVPath.rsplit('\\',1)[1]
initCSVPath = os.path.join(outputDir, "init.csv")

# Auxillary table path
appendCSVPath = os.path.join(rootDir, "data/tool_aux_data.csv")

# Calculation Function
compCheckBlock = """def compCheck(pFieldVal1, pFieldVal2):
    if (pFieldVal1 > 0 and pFieldVal2 > 0):
        return "BOTH"
    elif pFieldVal1 > 0:
        return "CURRENT"
    elif pFieldVal2 > 0:
        return "FUTURE"
    else:
        return "NONE" """

# CSV Function
# Merge two dictionaries based on a matching field
# http://stackoverflow.com/questions/9483051/join-two-csv-files-in-python-using-dictreader
def mergeTables(dictreader1, dictreader2):
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


#----- START PROCESSING -----#

# Create the output folder for the csv file if it does not exist already.
try:
    os.mkdir(outputCSVFolder)
except:
    pass

# Create feature layer from input selection polygon shapefile
arcpy.MakeFeatureLayer_management(selectionFC, 'input_layer')

# Create feature layer from preset generic Hawaii polygon
arcpy.MakeFeatureLayer_management(hawaiiFCPath, 'hawaii_lyr')

# Perform spatial selection from the generic Hawaii polygon to determine which islands
# overlap the input polygon
arcpy.SelectLayerByLocation_management('hawaii_lyr', 'intersect', 'input_layer')

# Open a search cursor to the grab the island attribute from the islands
# selected prior
with arcpy.da.SearchCursor('hawaii_lyr', 'island') as cursor:
    # Loop through each overlapping island
    for row in cursor:

        # Get the area of the input overlay polygon for use in calculations later
        inputArea = 0;
        with arcpy.da.SearchCursor('input_layer', ['SHAPE@AREA']) as iCursor:
            for iRow in iCursor:
                inputArea = iRow[0]


        #--- CREATE CCE SELECTION AND INTERSECTION SHAPEFILE ---#

        # Build path to each individual island polygon shapefile
        islandCCE_FC = outputDir + row[0] + "_CCE.shp"
        islandCCE_Lyr = row[0] + "_CSel"

        # Create feature layer from individual island polygon to determine which species
        # extents overlap with the input overlay polygon
        arcpy.MakeFeatureLayer_management(islandCCE_FC, islandCCE_Lyr)

        # Get total record from individual island polygon
        cceTotalRecords = int(arcpy.GetCount_management(islandCCE_Lyr).getOutput(0))

        # Perform spatial selection from each island
        arcpy.SelectLayerByLocation_management(islandCCE_Lyr, 'intersect', 'input_layer')

        # Loop through and subdivide the selection into maximum subsets of 200 features.
        # This subdivision is needed to work around an issue where the clip geoprocessing
        # tool might fail if feature count starts to get past 200.
        increment = 200
        cceCount = 1
        cceStartIndex = 0
        cceEndIndex = cceStartIndex + increment

        # Start subdivision loop
        while cceStartIndex <= cceTotalRecords:
            # Select subset of features based on FID
            outputCCE_FC = islandCCE_Lyr + "_" + str(cceCount) + ".shp"
            outputCCE_FCPath = os.path.join(outputDir, outputCCE_FC)
            arcpy.Select_analysis(islandCCE_Lyr, outputCCE_FCPath, '"FID" >= ' + str(cceStartIndex) + ' AND "FID" < ' + str(cceEndIndex))

            # Clip out the extent of the selection polygon
            clipCCE = os.path.join(outputDir, row[0] + "_CClp_" + str(cceCount) + ".shp")
            arcpy.Clip_analysis(outputCCE_FCPath, 'input_layer', clipCCE, "")

            # Increment counters
            cceCount += 1
            cceStartIndex = cceEndIndex
            cceEndIndex += increment

        # Merge all subsets back into single shapefile
        allCCESelections = arcpy.ListFeatureClasses("*_CClp_*", "POLYGON")
        clipCCE_Merge = os.path.join(outputDir, row[0] + "_CClp.shp")
        arcpy.Merge_management(allCCESelections, clipCCE_Merge)

        # Add an area field to the CCE selection shapefile to hold the percentage calculation
        arcpy.AddField_management(clipCCE_Merge, "inxPercent", "DOUBLE", "", "", "", "", "NON_NULLABLE")

        # Calculate the percentage of area species habitat extent covered by the selection polygon
        # Divide the area of the intersected polygon by the area of the input overlay polygon
        arcpy.CalculateField_management(clipCCE_Merge, "inxPercent", "!SHAPE.area!/" + str(inputArea), "PYTHON_9.3", "")

        # Get current field list from CCE Intersection shapefile
        cceFields = arcpy.ListFields(clipCCE_Merge)

        # Build list of fields to drop
        keepFields = ["FID","Shape","spp","sp_code","vulnerabil","inxPercent"]
        dropFields = []
        for cceField in cceFields:
            if cceField.name not in keepFields:
                dropFields.append(cceField.name)

        # Drop fields from CCE Intersection shapefile
        arcpy.DeleteField_management(clipCCE_Merge, dropFields)

        # Create CCE Intersection feature layer to work with
        arcpy.MakeFeatureLayer_management(clipCCE_Merge, "clipCCE_Lyr")


        #--- CREATE FCE SELECTION AND INTERSECTION SHAPEFILE ---#

        # Build path to each individual island polygon shapefile
        islandFCE_FC = outputDir + row[0] + "_FCE.shp"
        islandFCE_Lyr = row[0] + "_FSel"

        # Create feature layer from individual island polygon to determine which species
        # extents overlap with the input overlay polygon
        arcpy.MakeFeatureLayer_management(islandFCE_FC, islandFCE_Lyr)

        # Get total record from individual island polygon
        fceTotalRecords = int(arcpy.GetCount_management(islandFCE_Lyr).getOutput(0))

        # Perform spatial selection from each island
        arcpy.SelectLayerByLocation_management(islandFCE_Lyr, 'intersect', 'input_layer')

        # Loop through and subdivide the selection into maximum subsets of 200 features.
        # This subdivision is needed to work around an issue where the clip geoprocessing
        # tool might fail if feature count starts to get past 200.
        increment = 200
        fceCount = 1
        fceStartIndex = 0
        fceEndIndex = fceStartIndex + increment

        # Start subdivision loop
        while fceStartIndex <= fceTotalRecords:
            # Select subset of features based on FID
            outputFCE_FC = islandFCE_Lyr + "_" + str(fceCount) + ".shp"
            outputFCE_FCPath = os.path.join(outputDir, outputFCE_FC)
            arcpy.Select_analysis(islandFCE_Lyr, outputFCE_FCPath, '"FID" >= ' + str(fceStartIndex) + ' AND "FID" < ' + str(fceEndIndex))

            # Clip out the extent of the selection polygon
            clipFCE = os.path.join(outputDir, row[0] + "_FClp_" + str(fceCount) + ".shp")
            arcpy.Clip_analysis(outputFCE_FCPath, 'input_layer', clipFCE, "")

            # Increment counters
            fceCount += 1
            fceStartIndex = fceEndIndex
            fceEndIndex += increment

        # Merge all subsets back into single shapefile
        allFCESelections = arcpy.ListFeatureClasses("*_FClp_*", "POLYGON")
        clipFCE_Merge = os.path.join(outputDir, row[0] + "_FClp.shp")
        arcpy.Merge_management(allFCESelections, clipFCE_Merge)

        # Add an area field to the CCE selection shapefile to hold the percentage calculation
        arcpy.AddField_management(clipFCE_Merge, "inxPercent", "DOUBLE", "", "", "", "", "NON_NULLABLE")

        # Calculate the percentage of area species habitat extent covered by the selection polygon
        # Divide the area of the intersected polygon by the area of the input overlay polygon
        arcpy.CalculateField_management(clipFCE_Merge, "inxPercent", "!SHAPE.area!/" + str(inputArea), "PYTHON_9.3", "")

        # Get current field list from FCE Intersection shapefile
        fceFields = arcpy.ListFields(clipFCE_Merge)

        # Build list of fields to drop
        dropFields = []
        for fceField in fceFields:
            if fceField.name not in keepFields:
                dropFields.append(fceField.name)

        # Drop fields from FCE Intersection shapefile
        arcpy.DeleteField_management(clipFCE_Merge, dropFields)

        # Create FCE Intersection feature layer to work with
        arcpy.MakeFeatureLayer_management(clipFCE_Merge, "clipFCE_Lyr")


        #--- CREATE JOINED SHAPEFILE FROM CCE INTERSECTION AND FCE INTERSECTION ---#

        # Field variables
        cceVulField = 'vulnerabil'
        cceSPPField = 'spp'
        cceSPCodeField = 'sp_code'
        cceIntx = 'inxPercent'
        fceVulField = row[0] + '_FClp_vu'
        fceIntx = row[0] + '_FClp_in'
        presField = 'presence'

        # Join the FCE intersection feature layer to CCE intersection feature layer based on mutual spp fields
        arcpy.AddJoin_management("clipCCE_Lyr", "spp", "clipFCE_Lyr", "spp")

        # Save the joined shapefile to disk
        outputJoin_FC = row[0] + "_Joined.shp"
        outputJoin_FCPath = os.path.join(outputDir, outputJoin_FC)
        arcpy.FeatureClassToFeatureClass_conversion("clipCCE_Lyr", outputDir, outputJoin_FC)
        # Add the presence field
        arcpy.AddField_management(outputJoin_FCPath, presField, "TEXT", "", "", 10)

        # Check the vulnerability field for both the CCE and FCE models.
        # Set the presence field value based on compCheckBlock test.
        arcpy.CalculateField_management(outputJoin_FCPath, presField, "compCheck(!"+cceVulField+"!,!"+fceVulField+"!)", "PYTHON_9.3", compCheckBlock)

        # Sort the final result by vulnerability
        outputSort_FC = row[0] + "_Sorted.shp"
        outputSort_FCPath = os.path.join(outputDir, outputSort_FC)
        sort_fields = [[cceVulField, "DESCENDING"]]
        arcpy.Sort_management(outputJoin_FCPath, outputSort_FCPath, sort_fields, "")


        #--- CREATE THE CSV REPORT ---#

        # Open a new file to write
        # This function is set to automatically overwrite any file with the same input name.
        initCSV = open(initCSVPath, 'w')
        initCSV.write(csvHeader)

        # Loop through each overlapping species extent and write out the species name, vulnerability index, presence status,
        with arcpy.da.SearchCursor(outputSort_FCPath, [cceSPPField, cceSPCodeField, cceVulField, presField, cceIntx, fceIntx]) as xCursor:
            for xRow in xCursor:
                tempWrite = xRow[0] + "," + str(int(xRow[1])) + "," + str(float(xRow[2])) + "," + str(xRow[3]) + "," + str(float(xRow[4])) + "," + str(float(xRow[5])) + "\n"
                initCSV.write(tempWrite)
        initCSV.close()

        # Delete all temporary data based on shapefile name length
        # All original source island shapefiles have 10 character file names.
        allFCs = arcpy.ListFeatureClasses()
        for fc in allFCs:
            if (len(fc) != 10):
                arcpy.Delete_management(fc)


        # --- START PROCESSING CSV FILES --- #

        # Check to see if appending table exists
        if os.path.exists(appendCSVPath):

            # Read input csv files as dictionaries
            dFile1 = open(initCSVPath, "rb" )
            dReader1 = csv.DictReader(dFile1)

            dFile2 = open(appendCSVPath, "rb" )
            dReader2 = csv.DictReader(dFile2)

            # Call the matching and appending function
            finalRecords = mergeTables(dReader1, dReader2)

            # Close access to the csv files
            dFile1.close()
            dFile2.close()

            # Read the input csv files again as raw csvs
            # Get the field names from each csv
            headerFile1 = open(initCSVPath, "rb")
            reader1 = csv.reader(headerFile1)
            headers1 = reader1.next()

            headerFile2 = open(appendCSVPath, "rb")
            reader2 = csv.reader(headerFile2)
            headers2 = reader2.next()

            # Build a single list of fieldnames
            for hdrElement in headers2:
                if hdrElement not in headers1:
                    headers1.append(hdrElement)

            # Create the ouput CSV
            finalCSV = open(outputCSVPath, "wb")
            finalWriter = csv.DictWriter(finalCSV, delimiter=',', fieldnames=headers1)
            finalWriter.writer.writerow(headers1)
            finalWriter.writerows(finalRecords)
            finalCSV.close()

            # Close access to the csv files
            headerFile1.close()
            headerFile2.close()

            # Clean up temporary CSV
            os.remove(initCSVPath)

        # If the appending table does not exist
        else:
            # Copy the file using the final output name/path
            shutil.copy2(initCSVPath, outputCSVPath)

            # Clean up temporary CSV
            os.remove(initCSVPath)