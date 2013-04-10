import arcpy
rootdir="Y:/Test files/"
arcpy.env.workspace = rootdir
rasterList = arcpy.ListRasters("*", "tif")
for raster in rasterList:    
    arcpy.Resample_management(rootdir+raster, rootdir+raster[:-4]+"_1000m.tif", "1000", "NEAREST")
#test comment
