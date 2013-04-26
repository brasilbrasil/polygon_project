# Import libraries
import arcpy, os, zipfile, fnmatch

# Input variables
server=True #if running script on server with full dataset
if server:
    rootDir = "Y:/PICCC_analysis/polygon_project - Copy/"
    inputDir = "Y:/VA data/CEs/"
    inputCSV ="Y:/VA data/CAO/"+"spp_habitat_requirements_poly.csv"
else:
    rootDir = "C:/Users/Eok/Documents/GitHub/polygon_project/"
    inputDir = rootDir + "data/CEs/"
    inputCSV = rootDir + "data/spp_aux_data.csv"

islandDirName = "data/Islands/"
islandDir = rootDir + islandDirName
outputDirName = "output/"
outputDir = rootDir + outputDirName
outputFC = "allislands.shp"
fgdb = "species.gdb"
outputGDB = outputDir + fgdb
tableName = "VULNERABILITY"
tablePath = outputDir + fgdb + "/" + tableName
overlayscript = "poly_overlay.py"
speciestoolbox = "SpeciesTools.tbx"
overwrite = False

### Set environment to CEs directory
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
    if raster[0:1]=="C": #to process CCE rasters only
        if int(raster[-8:-4])<1086: #there are a few non-native species that have model numbers >1085 that are excluded 
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
                print "doing " + raster
            else:
                print "already done with " + raster

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
    # Make sure we're only using the individual island shapefiles, skip the main island set
    if (len(island) == 6):
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

# Create a zip file of the results in the same directory as the script and prepare to write
zf = zipfile.ZipFile('SpeciesTools.zip', mode='w')

# Loop through the data/Islands directory
for tempRoot, dirs, files in os.walk(islandDirName):
    # Zip only the Main_Hawaiian_Islands_simple2.shp file
    for file in fnmatch.filter(files, 'Main*'):
        zf.write(os.path.join(tempRoot, file))

# Loop through the output directory
for tempRoot, dirs, files in os.walk(outputDirName):
    # Zip only files with filenames of 6 characters.
    # This will zip the individual output island shapefiles since they follow a set
    # naming convention. Done this way to avoid looping through an extra list just to filter
    # out the individual island names.
    for file in files:
        if len(file) == 6:
            zf.write(os.path.join(tempRoot, file))

# Zip the overlay script
# The overlay script is currently expected to be in the same directory as this script
zf.write(overlayscript)

# Zip the SpeciesToolbox
# The SpeciesToolbox is currently expected to be in the same directory as this script
zf.write(speciestoolbox)

# Close out zip file to stop writing
zf.close()