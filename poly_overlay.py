import arcpy, os

# Set path to the root folder for input data
rootDir = arcpy.GetParameterAsText(0)

# Input variables
islandDir = rootDir + "\\data\\Islands\\"
outputDir = rootDir + "\\output\\"
outputTable = "C:/Users/Eok/Documents/GitHub/polygon_project/output/species.gdb/ccetable"
hawaiiFC = "Main_Hawaiian_Islands_simple2.shp"
hawaiiFCPath = islandDir + hawaiiFC
fgdb = "species.gdb"
outputGDB = outputDir + fgdb
csvHeader = "SPEC_NAME,VULNER_IDX,PRESENCE,CUR_OVERLAP_PCT,FUT_OVERLAP_PCT\n"

# Change environment to Islands subdirectory
arcpy.env.workspace = outputGDB
arcpy.env.overwriteOutput = True

# Set path to input selection polygon shapefile
selectionFC = arcpy.GetParameterAsText(1)

# Set the full path of the output CSV file
# The default is the current directory of the script/toolbox +
# protected_area_shapefile_folder/protected_area_vulnerability_report.csv
# That path is configured in the toolbox.
outputCSVPath = arcpy.GetParameterAsText(2)
outputCSVFolder = outputCSVPath.rsplit('\\',1)[0]
outputCSVName = outputCSVPath.rsplit('\\',1)[1]

# Calculation functions
compCheckBlock = """def compCheck(pFieldVal1, pFieldVal2):
    if (pFieldVal1 > 0 and pFieldVal2 > 0):
        return "BOTH"
    elif pFieldVal1 > 0:
        return "CURRENT"
    elif pFieldVal2 > 0:
        return "FUTURE"
    else:
        return "NONE" """


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

        #--- CREATE CCE SELECTION AND INTERSECTION SHAPEFILE ---#

        # Build path to each individual island polygon shapefile
        islandCCE_FC = outputDir + row[0] + "_CCE.shp"
        islandCCE_Lyr = row[0] + "_CSel"
        outputCCE_FC = islandCCE_Lyr + ".shp"
        outputCCE_FCPath = os.path.join(outputDir, outputCCE_FC)
##        outputCCE_FCPath = os.path.join(outputGDB, islandCCE_Lyr)

        # Create feature layer from individual island polygon to determine which species
        # extents overlap with the input polygon
        arcpy.MakeFeatureLayer_management(islandCCE_FC, islandCCE_Lyr)

        # Perform spatial selection from each island
        arcpy.SelectLayerByLocation_management(islandCCE_Lyr, 'intersect', 'input_layer')

        # Save the spatial selection to intermediate shapefile
        arcpy.FeatureClassToFeatureClass_conversion(islandCCE_Lyr, outputDir, outputCCE_FC)
##        arcpy.FeatureClassToGeodatabase_conversion(islandCCE_Lyr, outputGDB)

        # Add an area field to the CCE selection shapefile
        arcpy.AddField_management(outputCCE_FCPath, "sppArea", "DOUBLE", "", "", "", "", "NON_NULLABLE")

        # Populate the new field with the area value from the SHAPE field
        arcpy.CalculateField_management(outputCCE_FCPath, "sppArea", "!SHAPE.area!", "PYTHON_9.3", "")

##        # Create an intersection between the selection polygon and the selected species polygons
##        inFCs1 = ['input_layer', outputCCE_FCPath]
##        inFCs1 = ['input_layer', islandCCE_Lyr]
##        intersectCCE = os.path.join(outputDir, row[0] + "_CInt.shp")
##        intersectCCE = row[0] + "_CCE_Intersect"
##        clusterTolerance = 1
##        arcpy.Intersect_analysis(inFCs1, intersectCCE, "", 0, "INPUT")

        # Clip out the extent of the selection polygon
        clipCCE = os.path.join(outputDir, row[0] + "_CClp.shp")
        arcpy.Clip_analysis(outputCCE_FCPath, 'input_layer', clipCCE, "")

        # Add an area field to the CCE selection shapefile to hold the percentage calculation
        arcpy.AddField_management(clipCCE, "inxPercent", "DOUBLE", "", "", "", "", "NON_NULLABLE")

        # Calculate the percentage of area species habitat extent covered by the selection polygon
        arcpy.CalculateField_management(clipCCE, "inxPercent", "!SHAPE.area!/!sppArea!", "PYTHON_9.3", "")

        # Get current field list from CCE Intersection shapefile
        cceFields = arcpy.ListFields(clipCCE)

        # Build list of fields to drop
        keepFields = ["FID","Shape","spp","sp_code","vulnerabil","inxPercent"]
        dropFields = []
        for cceField in cceFields:
            if cceField.name not in keepFields:
                dropFields.append(cceField.name)

        # Drop fields from CCE Intersection shapefile
        arcpy.DeleteField_management(clipCCE, dropFields)

        # Create CCE Intersection feature layer to work with
        arcpy.MakeFeatureLayer_management(clipCCE, "clipCCE_Lyr")


        #--- CREATE FCE SELECTION AND INTERSECTION SHAPEFILE ---#

        # Build path to each individual island polygon shapefile
        islandFCE_FC = outputDir + row[0] + "_FCE.shp"
        islandFCE_Lyr = row[0] + "_FSel"
        outputFCE_FC = islandFCE_Lyr + ".shp"
        outputFCE_FCPath = os.path.join(outputDir, outputFCE_FC)
##        outputFCE_FCPath = os.path.join(outputGDB, islandFCE_Lyr)

        # Create feature layer from individual island polygon to determine which species
        # extents overlap with the input polygon
        arcpy.MakeFeatureLayer_management(islandFCE_FC, islandFCE_Lyr)

        # Perform spatial selection from each island
        arcpy.SelectLayerByLocation_management(islandFCE_Lyr, 'intersect', 'input_layer')

        # Save the spatial selection to intermediate shapefile
        arcpy.FeatureClassToFeatureClass_conversion(islandFCE_Lyr, outputDir, outputFCE_FC)
##        arcpy.FeatureClassToGeodatabase_conversion(islandFCE_Lyr, outputGDB)

        # Add an area field to the CCE selection shapefile
        arcpy.AddField_management(outputFCE_FCPath, "sppArea", "DOUBLE", "", "", "", "", "NON_NULLABLE")

        # Populate the new field with the area value from the SHAPE field
        arcpy.CalculateField_management(outputFCE_FCPath, "sppArea", "!SHAPE.area!", "PYTHON_9.3", "")

##        # Process: Find all stream crossings (points)
##        inFCs2 = ['input_layer', outputFCE_FCPath]
##        inFCs2 = ['input_layer', islandFCE_Lyr]
##        intersectFCE = os.path.join(outputDir, row[0] + "_FInt.shp")
##        intersectFCE = row[0] + "_FCE_Intersect"
##        arcpy.Intersect_analysis(inFCs2, intersectFCE, "", clusterTolerance, "INPUT")

        # Clip out the extent of the selection polygon
        clipFCE = os.path.join(outputDir, row[0] + "_FClp.shp")
        arcpy.Clip_analysis(outputFCE_FCPath, 'input_layer', clipFCE, "")

        # Add an area field to the CCE selection shapefile to hold the percentage calculation
        arcpy.AddField_management(clipFCE, "inxPercent", "DOUBLE", "", "", "", "", "NON_NULLABLE")

        # Calculate the percentage of area species habitat extent covered by the selection polygon
        arcpy.CalculateField_management(clipFCE, "inxPercent", "!SHAPE.area!/!sppArea!", "PYTHON_9.3", "")

        # Get current field list from FCE Intersection shapefile
        fceFields = arcpy.ListFields(clipFCE)

        # Build list of fields to drop
        dropFields = []
        for fceField in fceFields:
            if fceField.name not in keepFields:
                dropFields.append(fceField.name)

        # Drop fields from FCE Intersection shapefile
        arcpy.DeleteField_management(clipFCE, dropFields)

        # Create FCE Intersection feature layer to work with
        arcpy.MakeFeatureLayer_management(clipFCE, "clipFCE_Lyr")


        #--- CREATE JOINED SHAPEFILE FROM CCE INTERSECTION AND FCE INTERSECTION ---#

        # Field variables
        cceVulField = 'vulnerabil'
        cceSPPField = 'spp'
        cceIntx = 'inxPercent'
        fceVulField = row[0] + '_FClp_vu'
        fceIntx = row[0] + '_FClp_in'
        presField = 'presence'

        # Join the FCE intersection feature layer to CCE intersection feature layer based on mutual spp fields
        arcpy.AddJoin_management("clipCCE_Lyr", "spp", "clipFCE_Lyr", "spp")

        # Save the joined shapefile to disk
        outputJoin_FC = row[0] + "_Joined.shp"
        outputJoin_FCPath = os.path.join(outputDir, outputJoin_FC)
##        outputJoin_FCPath = os.path.join(outputGDB, islandCCE_Lyr + "_1")
        arcpy.FeatureClassToFeatureClass_conversion("clipCCE_Lyr", outputDir, outputJoin_FC)
##        arcpy.FeatureClassToGeodatabase_conversion(islandCCE_Lyr, outputGDB)

        # Add the presence field
        arcpy.AddField_management(outputJoin_FCPath, presField, "TEXT", "", "", 10)

        # Check the vulnerability field for both the CCE and FCE models.
        # Set the presence field value based on compCheckBlock test.
        arcpy.CalculateField_management(outputJoin_FCPath, presField, "compCheck(!"+cceVulField+"!,!"+fceVulField+"!)", "PYTHON_9.3", compCheckBlock)


        #--- CREATE THE CSV REPORT ---#

        # Open a new file to write
        # This function is set to automatically overwrite any file with the same input name.
        f = open(outputCSVPath, 'w')
        f.write(csvHeader)

        # Loop through each overlapping species extent and write out the species name, vulnerability index, presence status,
        with arcpy.da.SearchCursor(outputJoin_FCPath, [cceSPPField, cceVulField, presField, cceIntx, fceIntx]) as xCursor:
            for xRow in xCursor:
                tempWrite = xRow[0] + "," + str(float(xRow[1])) + "," + str(xRow[2]) + "," + str(float(xRow[3])) + "," + str(float(xRow[4])) + "\n"
                f.write(tempWrite)
        f.close()

        # Delete intermediate shapefiles
        arcpy.Delete_management(outputCCE_FCPath)
        arcpy.Delete_management(clipCCE)
        arcpy.Delete_management(outputFCE_FCPath)
        arcpy.Delete_management(clipFCE)
        arcpy.Delete_management(outputJoin_FCPath)