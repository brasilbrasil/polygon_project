# Import libraries
import arcpy, os

# Input variables
#root="C:/Users/Eok/Documents/GitHub/"
root="C:/Users/lfortini/code/"
inputDir = root+"polygon_project/data/CEs/"
outputDir = inputDir + "Output/"
outputFC = "allspecies.shp"
inputCSV = root+"polygon_project/data/spp_aux_data.csv"
fgdb = "species.gdb"
outputGDB = outputDir + fgdb
tableName = "VULNERABILITY"
tablePath = outputDir + fgdb + "/" + tableName
overwrite=False

# Set work environment
arcpy.env.workspace = inputDir
try:
    os.mkdir(outputDir)
except:
    pass

# Check to see if the allspecies.gdb exists
if not os.path.exists(outputDir + fgdb):
    # Create a file geodatabase to hold the CSV table for joining to output polygon
    arcpy.CreateFileGDB_management(outputDir, fgdb)

    # Import all rows of CSV file into file geodatabase
    arcpy.TableToTable_conversion(inputCSV, outputDir + fgdb, tableName, "", "", "")

# Retrieve list of raster from working folder
rasterList = arcpy.ListRasters("*", "tif")

# Loop through list of rasters
for raster in rasterList:
    outPoly2 = outputDir + raster[:-4] + "x.shp"
    if arcpy.Exists(outPoly2)==False or overwrite==True:
        # Convert raster file to polygon without simplifying/smoothing
        outPoly = outputDir + raster[:-4] + ".shp"
        arcpy.RasterToPolygon_conversion(raster, outPoly, "NO_SIMPLIFY")
    
        # Add a species ID field to enable joining with vulnerability table later
        # The SPEC_ID field created will be a long integer that's non-nullable
        arcpy.AddField_management(outPoly, "SPEC_ID", "LONG", "", "", "", "", "NON_NULLABLE")
    
        # Populate the SPEC_ID field with the 4 digit code from the file name of the input tif filename
        arcpy.CalculateField_management(outPoly, "SPEC_ID", int(raster[-8:-4]), "PYTHON_9.3", "")
    
        # Dissolve the multiple polygons created by the Raster to Polygon tool into a single multipart polygon
        arcpy.Dissolve_management(outPoly, outPoly2, "SPEC_ID")
    
        # Delete first polygon created to limit output files
        arcpy.Delete_management(outPoly)
        print "done with " + raster
    else:
        print "already vectorized " + raster

# Change environment to output subdirectory
arcpy.env.workspace = outputDir
arcpy.env.qualifiedFieldNames = False

# Retrieve list of POLYGON feature classes (shapefiles) from output directory
# The wildcard option is used but only the second set of shapefiles should be in the output folder
fcList = arcpy.ListFeatureClasses("*x.shp","POLYGON")

# Create a new empty feature class to append shapefiles into
arcpy.CreateFeatureclass_management(outputDir, outputFC, "POLYGON", fcList[0])

# Append the all the listed feature classes into the empty feature class
# Fields are not tested as they are assumed to all be the same.
outputFCPath = outputDir + outputFC
arcpy.Append_management(fcList, outputFCPath, "NO_TEST", "", "")

# Join species reference table to final polygon
joinedFieldList = ["spp","vulnerability"]
arcpy.JoinField_management(outputFCPath, "SPEC_ID", tablePath, "sp_code", joinedFieldList)

