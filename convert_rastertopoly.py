# Import libraries
import arcpy, os

# Input variables
root = "C:/Users/Eok/Documents/GitHub/polygon_project/"
##root = "C:/Users/lfortini/code/"
inputDir = root + "data/CEs/"
islandDir = root + "data/Islands/"
outputDir = root + "output/"
outputFC = "allislands.shp"
inputCSV = root + "data/spp_aux_data.csv"
fgdb = "species.gdb"
outputGDB = outputDir + fgdb
tableName = "VULNERABILITY"
tablePath = outputDir + fgdb + "/" + tableName
overwrite = False

# Set environment to CEs directory
arcpy.env.workspace = inputDir

# Create output directory if it doesn't already exist
try:
    os.mkdir(outputDir)
except:
    pass


# Check to see if the allspecies.gdb exists, if not create it
if not os.path.exists(outputDir + fgdb):
    # Create a file geodatabase to hold the CSV table for joining to output polygon
    arcpy.CreateFileGDB_management(outputDir, fgdb)

    # Import all rows of CSV file into file geodatabase
    arcpy.TableToTable_conversion(inputCSV, outputDir + fgdb, tableName, "", "", "")

# Retrieve list of raster from workspace (CEs directory)
rasterList = arcpy.ListRasters("*", "tif")

# Loop through list of rasters
for raster in rasterList:
    outPoly = outputDir + raster[:-4] + ".shp"

    # Check to see if the polygons have been created
    if arcpy.Exists(outPoly) == False or overwrite == True:
        # Convert raster file to polygon without simplifying/smoothing
        arcpy.RasterToPolygon_conversion(raster, outPoly, "NO_SIMPLIFY")

        # Add a species ID field to enable joining with vulnerability table later
        # The SPEC_ID field created will be a long integer that's non-nullable
        arcpy.AddField_management(outPoly, "SPEC_ID", "LONG", "", "", "", "", "NON_NULLABLE")

        # Populate the SPEC_ID field with the 4 digit code from the file name of the input tif filename
        arcpy.CalculateField_management(outPoly, "SPEC_ID", int(raster[-8:-4]), "PYTHON_9.3", "")

# Change environment to output subdirectory
arcpy.env.workspace = outputDir
arcpy.env.qualifiedFieldNames = False

# Retrieve list of POLYGON feature classes (shapefiles) from output directory
# The wildcard option is used but only the second set of shapefiles should be in the output folder
fcList = arcpy.ListFeatureClasses("*.shp","POLYGON")

# Create a new empty feature class to append shapefiles into
spatial_reference = arcpy.Describe(fcList[0]).spatialReference
arcpy.CreateFeatureclass_management(outputDir, outputFC, "POLYGON", fcList[0], "", "", spatial_reference)

# Append the all the listed feature classes into the empty feature class
# Fields are not tested as they are assumed to all be the same.
outputFCPath = outputDir + outputFC
arcpy.Append_management(fcList, outputFCPath, "NO_TEST", "", "")
arcpy.MakeFeatureLayer_management(outputFCPath, 'output_layer')

# Change environment to Islands subdirectory
arcpy.env.workspace = islandDir

# Retrieve each island polygon from Islands directory
islandList = arcpy.ListFeatureClasses("*.shp","POLYGON")

# Loop through list of island shapefiles
for island in islandList:
    # Setup new variables to work with island shapefiles and outputs
    islandLayer = island[-6:-4] + '_lyr'
    islandFC = island[-6:-4] + "x.shp"
    islandFCPath = outputDir + islandFC
    islandFCPath2 = outputDir + island[:-4] + ".shp"

    # Create feature layer from island polygon
    arcpy.MakeFeatureLayer_management(island, islandLayer)

    # Perform spatial selection from the allislands.shp by each island
    arcpy.SelectLayerByLocation_management('output_layer', 'intersect', islandLayer)

    # Save the spatial selection to intermediate shapefile
    arcpy.FeatureClassToFeatureClass_conversion('output_layer', outputDir, islandFC)

    # Dissolve the multiple polygons created by the Raster to Polygon tool
    # into a single multipart polygon
    arcpy.Dissolve_management(islandFCPath, islandFCPath2, "SPEC_ID")

    # Join species reference table to final polygons
    # joinedFieldList = ["spp","vulnerability"]
    # All fields are currently joined to final island polygon.
    # Since the values are simple, this should be minimal overhead.
    arcpy.JoinField_management(islandFCPath2, "SPEC_ID", tablePath, "sp_code")

    # Delete intermediate island shapefiles
    arcpy.Delete_management(islandFCPath)