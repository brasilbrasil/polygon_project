import arcpy, os

# Input variables
root = "C:/Users/Eok/Documents/GitHub/polygon_project/"
islandDir = root + "islands/"
hawaiiFC = "ALL.shp"
hawaiiFCPath = islandDir + hawaiiFC
outputCSVName = "report.csv"
outputCSVPath = "C:/Users/Eok/Documents/GitHub/polygon_project/" + outputCSVName
csvHeader = "Species Name,Vulnerability Index\n"

# Change environment to Islands subdirectory
arcpy.env.workspace = islandDir

# Set path to input selection polygon shapefile
selectionFC = arcpy.GetParameterAsText(0)

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
        # Build path to each individual island polygon shapefile
        islandFC = islandDir + row[0] + ".shp"

        # Create feature layer from individual island polygon to determine which species
        # extents overlap with the input polygon
        arcpy.MakeFeatureLayer_management(islandFC, 'island_layer')

        # Perform spatial selection from each island
        arcpy.SelectLayerByLocation_management('island_layer', 'intersect', 'input_layer')

        # Open a new file to write
        # This function is set to automatically overwrite any file with the same input name.
        f = open(outputCSVPath, 'w')
        f.write(csvHeader)

        # Loop through each overlapping species extent and write out the species namea and
        # vulnerability index to the CSV output file
        with arcpy.da.SearchCursor('island_layer', ['spp','vulnerabil']) as xCursor:
            for xRow in xCursor:
                tempWrite = xRow[0] + "," + str(xRow[1]) + "\n"
                f.write(tempWrite)
        f.close()