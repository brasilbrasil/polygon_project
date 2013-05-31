# Import libraries
import arcpy, os, zipfile, fnmatch, xml
import xml.etree.ElementTree as ET

# Input variables
server = False #if running script on server with full dataset
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
outputFCEshp = "ISLANDS_FCE.shp"
outputCCEshp = "ISLANDS_CCE.shp"
fgdb = "species.gdb"
outputGDB = outputDir + fgdb
tableName = "VULNERABILITY"
tablePath = outputDir + fgdb + "/" + tableName
overlayscript = "poly_overlay.py"
speciestoolbox = "SpeciesTools.tbx"
overwrite = False

# General Functions
# Check maximum value in raster to skip empty rasters
def get_num_attributes(raster, value):
	jnk = arcpy.GetRasterProperties_management(raster, value)
	jnk = jnk.getOutput(0)
	jnk = float(jnk)
	return jnk


#--- START SCRIPT ---#

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
rasterList = arcpy.ListRasters("CCE*", "tif")

# Loop through list of rasters
for raster in rasterList:
    # Use the same file name for output but with a shapefile extension
    outPoly = outputDir + raster[:-4] + ".shp"

##    # Check the tif aux xml file to determine if the tif is empty.
##    # RasterToPolygon_conversion tool will fail if the raster is empty
##    # Use the etree library to read the metadata xml file for the tif
##    rasterXML = ET.parse(inputDir + raster + ".aux.xml")
##    xmlRoot = rasterXML.getroot()
##
##    # Loop through the metadata xml for the MDI elements
##    for mdi in xmlRoot.iter('MDI'):
##        # Get the STATISTICS_MAXIMUM value.
##        if (mdi.get('key') == 'STATISTICS_MAXIMUM'):
##            mdiValue = float(mdi.text)
##            # A value above 0 assumes that there is data.
##            if (mdiValue > 0):
    # Find model number from raster name
    speciesNum = int(raster[-8:-4])

    # There are a few non-native species that have model numbers > 1085 that are excluded
    if speciesNum < 1086:
        # Check to see if the polygons have been created
        if arcpy.Exists(outPoly) == False or overwrite == True:
##            # Process CCE rasters
##            if raster[0:1]=="C":
            # Convert raster file to polygon without simplifying/smoothing
            arcpy.RasterToPolygon_conversion(raster, outPoly, "NO_SIMPLIFY")

            # Add a species ID field to enable joining with vulnerability table later
            # The SPEC_ID field created will be a long integer that's non-nullable
            arcpy.AddField_management(outPoly, "SPEC_ID", "LONG", "", "", "", "", "NON_NULLABLE")

            # Populate the SPEC_ID field with the 4 digit code from the file name of the input tif filename
            arcpy.CalculateField_management(outPoly, "SPEC_ID", speciesNum, "PYTHON_9.3", "")
            print "doing " + raster
        else:
            print "already done with " + raster

# Retrieve list of raster from workspace (CEs directory)
rasterList = arcpy.ListRasters("FCE*", "tif")

# Loop through list of rasters
for raster in rasterList:
    # Use the same file name for output but with a shapefile extension
    outPoly = outputDir + raster[:-4] + ".shp"

##    # Check to see if raster has any data first before processing
##    rasMax = get_num_attributes(raster, "MAXIMUM")
##    if (rasMax > 0.0):

    # Check the tif aux xml file to determine if the tif is empty.
    # RasterToPolygon_conversion tool will fail if the raster is empty
    # Use the etree library to read the metadata xml file for the tif
    rasterXML = ET.parse(inputDir + raster + ".aux.xml")
    xmlRoot = rasterXML.getroot()

    # Loop through the metadata xml for the MDI elements
    for mdi in xmlRoot.iter('MDI'):
        # Get the STATISTICS_MAXIMUM value.
        if (mdi.get('key') == 'STATISTICS_MAXIMUM'):
            mdiValue = float(mdi.text)
            # A value above 0 assumes that there is data.
            if (mdiValue > 0):

                # Find model number from raster name
                speciesNum = int(raster[-8:-4])

                # There are a few non-native species that have model numbers > 1085 that are excluded
                if speciesNum < 1086:
                    # Check to see if the polygons have been created
                    if arcpy.Exists(outPoly) == False or overwrite == True:

        ##                # Process FCE rasters
        ##                elif raster[0:1] == "F":
                        # Convert raster file to polygon without simplifying/smoothing
                        arcpy.RasterToPolygon_conversion(raster, outPoly, "NO_SIMPLIFY")

                        # Add a species ID field to enable joining with vulnerability table later
                        # The SPEC_ID field created will be a long integer that's non-nullable
                        arcpy.AddField_management(outPoly, "SPEC_ID", "LONG", "", "", "", "", "NON_NULLABLE")

                        # Populate the SPEC_ID field with the 4 digit code from the file name of the input tif filename
                        arcpy.CalculateField_management(outPoly, "SPEC_ID", speciesNum, "PYTHON_9.3", "")
                        print "doing " + raster
                    else:
                        print "already done with " + raster

            else:
                print raster + " is empty. Skipping."

# Change environment to output subdirectory
arcpy.env.workspace = outputDir
arcpy.env.qualifiedFieldNames = False


# Retrieve list of POLYGON feature classes (shapefiles) from output directory
# The wildcard option is used but only the second set of shapefiles should be in the output folder
cceList = arcpy.ListFeatureClasses("CCE*.shp", "POLYGON")

# Create a new empty feature class to append shapefiles into
spatial_reference = arcpy.Describe(cceList[0]).spatialReference
arcpy.CreateFeatureclass_management(outputDir, outputCCEshp, "POLYGON", cceList[0], "", "", spatial_reference)

# Append the all the listed feature classes into the empty feature class
# Fields are not tested as they are assumed to all be the same.
outputCCEPath = outputDir + outputCCEshp
outputCCELayer = "cce_layer"
arcpy.Append_management(cceList, outputCCEshp, "NO_TEST", "", "")
arcpy.MakeFeatureLayer_management(outputCCEPath, outputCCELayer)


# Retrieve list of POLYGON feature classes (shapefiles) from output directory
# The wildcard option is used but only the second set of shapefiles should be in the output folder
fceList = arcpy.ListFeatureClasses("FCE*.shp", "POLYGON")

# Create a new empty feature class to append shapefiles into
spatial_reference = arcpy.Describe(fceList[0]).spatialReference
arcpy.CreateFeatureclass_management(outputDir, outputFCEshp, "POLYGON", fceList[0], "", "", spatial_reference)

# Append the all the listed feature classes into the empty feature class
# Fields are not tested as they are assumed to all be the same.
outputFCEPath = outputDir + outputFCEshp
outputFCELayer = "fce_layer"
arcpy.Append_management(fceList, outputFCEPath, "NO_TEST", "", "")
arcpy.MakeFeatureLayer_management(outputFCEPath, outputFCELayer)


# Change environment to Islands subdirectory
arcpy.env.workspace = islandDir

# Retrieve each island polygon from Islands directory
islandList = arcpy.ListFeatureClasses("*.shp","POLYGON")

# Loop through list of island shapefiles
for island in islandList:
    # Make sure we're only using the individual island shapefiles, skip the main island set
    if (len(island) == 6):
        #--- Create shapefile from CCE shapefiles ---#

        # Setup new variables to work with island CCE shapefiles and outputs
        islandCCELayer = island[-6:-4] + "_CCElyr"
        islandCCEshp = island[-6:-4] + "_CCEx.shp"
        islandCCEPath = outputDir + islandCCEshp
        islandCCEPath2 = outputDir + island[:-4] + "_CCE.shp"

        # Create feature layer from island polygon
        arcpy.MakeFeatureLayer_management(island, islandCCELayer)

        # Perform spatial selection from the allislands.shp by each island
        arcpy.SelectLayerByLocation_management(outputCCELayer, 'intersect', islandCCELayer)

        # Save the spatial selection to intermediate shapefile
        arcpy.FeatureClassToFeatureClass_conversion(outputCCELayer, outputDir, islandCCEshp)

        # Dissolve the multiple polygons created by the Raster to Polygon tool
        # into a single multipart polygon
        arcpy.Dissolve_management(islandCCEPath, islandCCEPath2, "SPEC_ID")

        # Join species reference table to final polygons
        # joinedFieldList = ["spp","vulnerability"]
        # All fields are currently joined to final island polygon.
        # Since the values are simple, this should be minimal overhead.
        arcpy.JoinField_management(islandCCEPath2, "SPEC_ID", tablePath, "sp_code")

        # Delete intermediate island shapefiles
        arcpy.Delete_management(islandCCEPath)


        #--- Create shapefile from FCE shapefiles ---#

        # Setup new variables to work with island FCE shapefiles and outputs
        islandFCELayer = island[-6:-4] + "_FCElyr"
        islandFCEshp = island[-6:-4] + "_FCEx.shp"
        islandFCEPath = outputDir + islandFCEshp
        islandFCEPath2 = outputDir + island[:-4] + "_FCE.shp"

        # Create feature layer from island polygon
        arcpy.MakeFeatureLayer_management(island, islandFCELayer)

        # Perform spatial selection from the allislands.shp by each island
        arcpy.SelectLayerByLocation_management(outputFCELayer, 'intersect', islandFCELayer)

        # Save the spatial selection to intermediate shapefile
        arcpy.FeatureClassToFeatureClass_conversion(outputFCELayer, outputDir, islandFCEshp)

        # Dissolve the multiple polygons created by the Raster to Polygon tool
        # into a single multipart polygon
        arcpy.Dissolve_management(islandFCEPath, islandFCEPath2, "SPEC_ID")

        # Join species reference table to final polygons
        # joinedFieldList = ["spp","vulnerability"]
        # All fields are currently joined to final island polygon.
        # Since the values are simple, this should be minimal overhead.
        arcpy.JoinField_management(islandFCEPath2, "SPEC_ID", tablePath, "sp_code")

        # Delete intermediate island shapefiles
        arcpy.Delete_management(islandFCEPath)


# Create a zip file of the results in the same directory as the script and prepare to write
zf = zipfile.ZipFile('SpeciesTools.zip', 'w', zipfile.ZIP_DEFLATED)

# Loop through the data/Islands directory
for tempRoot, dirs, files in os.walk(islandDirName):
    # Zip only the Main_Hawaiian_Islands_simple2.shp file
    for file in fnmatch.filter(files, 'Main*'):
        zf.write(os.path.join(tempRoot, file))

# Loop through the output directory
for tempRoot, dirs, files in os.walk(outputDirName):
    # Zip only files with filenames of 10 characters.
    # This will zip the individual output island shapefiles since they follow a set
    # naming convention. Done this way to avoid looping through an extra list just to filter
    # out the individual island names.
    for file in files:
        if len(file) == 10:
            zf.write(os.path.join(tempRoot, file))

# Zip the overlay script
# The overlay script is currently expected to be in the same directory as this script
zf.write(overlayscript)

# Zip the SpeciesToolbox
# The SpeciesToolbox is currently expected to be in the same directory as this script
zf.write(speciestoolbox)

# Close out zip file to stop writing
zf.close()