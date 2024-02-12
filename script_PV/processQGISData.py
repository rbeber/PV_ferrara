from qgis.core import *
from qgis.utils import iface
import os
import processing
import sys
import shutil


##################################################################
# This function add Vector Layer into scene
#
# Input:
# - inFile:		(<String>) absolute path of file
# - fileName:	(<String>) name to be assigned to the vector within the scene
#
##################################################################
def import_vectorLayer(inFile, fileName):
	layer = QgsVectorLayer(inFile, fileName, "ogr")

	if not layer.isValid():
		print ("Layer failed to load!")
		sys.exit()
	else:
		print ("Layer was loaded successfully!")

	"""
	Add Leyer QGIS
	"""
	QgsProject.instance().addMapLayer(layer)

	return layer


##################################################################
# This function add Raster Layer into scene
#
# Input:
# - inFile:		(<String>) absolute path of file
# - fileName:	(<String>) name to be assigned to the raster within the scene 
#
##################################################################
def import_rasterLayer(inFile, fileName):
	layer = iface.addRasterLayer(inFile, fileName)

	if not layer.isValid():
		print ("Layer failed to load!")
		sys.exit()
	else:
		print ("Layer was loaded successfully!")

	"""
	Add Leyer QGIS
	"""
	QgsProject.instance().addMapLayer(layer)

	return layer


##################################################################
# This function remove Layer from scene
#
# Input:
# - layer:		(<class 'qgis._core.QgsRasterLayer'>)
#
##################################################################
def removeLayer(layer):
	"""
	Remove layer by layer ID
	"""
	QgsProject.instance().removeMapLayers( [layer.id()] )


##################################################################
# This function reproject input raster to desire coordinate system
#
##################################################################
def warpProject(inLayer, idx, outFile):
	prjResult = processing.run("gdal:warpreproject", { 'DATA_TYPE' : 0, 'EXTRA' : '', 'INPUT' : inLayer, 'MULTITHREADING' : False, 'NODATA' : None, 'OPTIONS' : '', 'OUTPUT' : outFile, 'RESAMPLING' : 0, 'SOURCE_CRS' : None, 'TARGET_CRS' : QgsCoordinateReferenceSystem('EPSG:7791'), 'TARGET_EXTENT' : None, 'TARGET_EXTENT_CRS' : None, 'TARGET_RESOLUTION' : None })

	"""
	Add Leyer QGIS
	"""
	outLayer = iface.addRasterLayer(prjResult['OUTPUT'], "reprojected_layer_" + str(idx))
	# QgsProject.instance().addMapLayer( outLayer )

	return outLayer


##################################################################
# This function compute aspect from input layer
#
##################################################################
def compute_aspect(inLayer, idx, outFile):
	aspectResult = processing.run("gdal:aspect", { 'BAND' : 1, 'COMPUTE_EDGES' : False, 'EXTRA' : '', 'INPUT' : inLayer, 'OPTIONS' : '', 'OUTPUT' : outFile, 'TRIG_ANGLE' : False, 'ZERO_FLAT' : False, 'ZEVENBERGEN' : False })

	"""
	Add Leyer QGIS
	"""
	outLayer = iface.addRasterLayer(aspectResult['OUTPUT'], "aspect_layer_" + str(idx))
	# QgsProject.instance().addMapLayer( outLayer )

	return outLayer


##################################################################
# This function compute slope from input layer
#
##################################################################
def compute_slope(inLayer, idx, outFile):
	slopeResult = processing.run("gdal:slope", { 'AS_PERCENT' : False, 'BAND' : 1, 'COMPUTE_EDGES' : False, 'EXTRA' : '', 'INPUT' : inLayer, 'OPTIONS' : '', 'OUTPUT' : outFile, 'SCALE' : 1, 'ZEVENBERGEN' : False })

	"""
	Add Leyer QGIS
	"""
	outLayer = iface.addRasterLayer(slopeResult['OUTPUT'], "slope_layer_" + str(idx))
	# QgsProject.instance().addMapLayer( outLayer )

	return outLayer



##################################################################
# This function create vectorLayer from input layer
#
##################################################################
def compute_layer_extent(inLayer, idx):
	layerExtentResult = processing.run("native:polygonfromlayerextent", { 'INPUT' : inLayer, 'OUTPUT' : 'TEMPORARY_OUTPUT', 'ROUND_TO' : 0 })

	"""
	Add Leyer QGIS
	"""
	# QgsProject.instance().addMapLayer( layerExtentResult['OUTPUT'] )

	return layerExtentResult['OUTPUT']


##################################################################
# This function import and merge all dtm layer
#
##################################################################
def merge_layer(inFolder, outFile):
	"""
	Import all dtm layer
	"""
	layerList = []
	for count, f in enumerate(os.listdir(inFolder)):
		layer = import_rasterLayer(os.path.join(inFolder, f), "tmp_" + str(count))
		layerList.append(layer)

	"""
	merge layer
	"""
	mergeResult = processing.run("gdal:merge", { 'DATA_TYPE' : 5, 'EXTRA' : '', 'INPUT' : layerList, 'NODATA_INPUT' : None, 'NODATA_OUTPUT' : None, 'OPTIONS' : '', 'OUTPUT' : outFile, 'PCT' : False, 'SEPARATE' : False })

	return layerList


##################################################################
# This function export layer to shapefile
#
##################################################################
def export_shapeFile(layer, outFile):
	_writer = QgsVectorFileWriter.writeAsVectorFormat(layer, outFile, "utf-8", layer.crs(), "ESRI Shapefile")


##################################################################
# This function create all folder where to save the various results
#
##################################################################
def createPrjFolder(inFolder):
	#outputFolder = os.path.join(inFolder, "output")

	outputFolder = os.path.join(inFolder, os.pardir, 'output')


	"""
	Remove folder if exist
	"""
	if ( os.path.isdir(outputFolder) ):
		shutil.rmtree(outputFolder)

	slopePath = os.path.join(outputFolder, "slope")
	aspectPath = os.path.join(outputFolder, "aspect")
	tilePath = os.path.join(outputFolder, "tile")
	dtmPath = os.path.join(outputFolder, "dtm")
	
	os.mkdir(outputFolder)
	os.mkdir(slopePath)
	os.mkdir(aspectPath)
	os.mkdir(tilePath)
	os.mkdir(dtmPath)

	pathList = {}
	pathList["slope"] = slopePath
	pathList["aspect"] = aspectPath
	pathList["tile"] = tilePath
	pathList["dtm"] = dtmPath

	return pathList


##################################################################
# This function process input data
#
##################################################################
def process_data(f, inFolder, pathList):
	count = 0
	if (".tif" in f):
			inFile = os.path.join(inFolder, f)
			fileName = os.path.splitext(f)[0]

			"""
			Import Raster Layer
			"""
			layer = import_rasterLayer(inFile, "tmpLayer")

			"""
			Reproject layer to EPSG:7791
			"""
			warpLayer = warpProject(layer, count, os.path.join(pathList["dtm"], fileName + "_dtm.tif"))

			"""
			Compute aspect
			"""
			aspectLayer = compute_aspect(warpLayer, count, os.path.join(pathList["aspect"], fileName + "_aspect.tif"))

			"""
			Compute slope
			"""
			slopeLayer = compute_slope(warpLayer, count, os.path.join(pathList["slope"], fileName + "_slope.tif"))

			"""
			Compute layerExtent
			"""
			extentLayer = compute_layer_extent(warpLayer, count)

			"""
			Export vector layer
			"""
			export_shapeFile(extentLayer, os.path.join(pathList["tile"], fileName + "_tile.shp"))

			"""
			Remove layers
			"""
			removeLayer(layer)
			removeLayer(warpLayer)
			removeLayer(aspectLayer)
			removeLayer(slopeLayer)
			removeLayer(extentLayer)

			"""
			Increase count
			"""
			count = count + 1


##################################################################
# Main function
#
##################################################################
def main():
	inFolder = "/home/beber/fbk_sandbox/PV-ferrara/data/PV_ferrara/FE_data/raw_dtm"
	# inFolder = "/root/data/input/qgis/2"

	"""
	Create project folder
	"""
	pathList = createPrjFolder(inFolder)
	
	for f in os.listdir(inFolder):
		process_data(f, inFolder, pathList)

	# """
	# Merge dtm layer
	# """
	# layerList = merge_layer(pathList["dtm"], os.path.join(inFolder, "output", "dtm_merge.tif"))

	# """
	# Remove all layer
	# """
	# for layer in layerList:
	# 	removeLayer(layer)


main()