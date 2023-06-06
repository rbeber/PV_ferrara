import os, shutil
import subprocess, shlex
from subprocess import Popen, PIPE
from calendar import monthrange
import datetime
from multiprocessing import Process, Pool
import multiprocessing as mp
import timeit
import time, sys


MAX_PROCESSOR = mp.cpu_count() - 2


###################################################################
# This function run shell command
#
###################################################################
def run_grass_cmd(cmd):
    p = subprocess.run(shlex.split(cmd))


###################################################################
# This function create new Location and PERMANENT Mapset
#
###################################################################
def create_project(coord_system_code, location_name):
    if ( not os.path.isdir(location_name) ):
        cmd = "grass -e -c epsg:" + str(coord_system_code) + " " + location_name
        run_grass_cmd(cmd)

    return os.path.join(location_name, "PERMANENT")


###################################################################
# This function import vector
#
###################################################################
def import_vector(inFile, outName, prjPath):
    cmd = "grass " + prjPath + " --exec v.import --overwrite input=" + inFile + " output=" + outName

    run_grass_cmd(cmd)

    return outName


###################################################################
# This function import raster
#
###################################################################
def import_raster(inFile, outName, prjPath):
    if ( os.path.exists(inFile) ):
        cmd = "grass " + prjPath + " --exec r.import input=" + inFile + " output=" + outName

        run_grass_cmd(cmd)

        return outName
    else:
        return None

###################################################################
# This function set grass region
#
###################################################################
def set_region(raster_name, res, prjPath, region_type):
    cmd = "grass " + prjPath + " --exec g.region " + region_type + "=" + raster_name + " grow=1001 res=" + str(res)

    run_grass_cmd(cmd)


###################################################################
# This function create new Location and PERMANENT Mapset
#
###################################################################
def create_project(coord_system_code, location_name):
    if ( not os.path.isdir(location_name) ):
        cmd = "grass -e -c epsg:" + str(coord_system_code) + " " + location_name
        run_grass_cmd(cmd)

    return os.path.join(location_name, "PERMANENT")


###################################################################
# This function merge input raster
#
###################################################################
def merge_raster(list_rasterName, prjPath, outName):
    cmd = "grass " + prjPath + " -f --exec r.patch input=" + list_rasterName + " output=" + outName

    run_grass_cmd(cmd)

    return outName


###################################################################
# This function export 3x3 maps
#
###################################################################
def export_raster_map(raster_name, prjPath, outFolder):
    cmd = "grass " + prjPath + " -f --exec r.null map=" + str(raster_name) + " null=0"

    run_grass_cmd(cmd)


    cmd_1 = "grass " + prjPath + " -f --exec r.out.gdal -f input=" + str(raster_name) + " output=" + os.path.join(outFolder, "3x3_tile", raster_name + ".tif") + " format=GTiff"

    run_grass_cmd(cmd_1)


###################################################################
# This function create folder to save all output
#
###################################################################
def check_outfolder(dataFolder):
    outFolder = os.path.join(dataFolder, "3x3_tile")

    if (os.path.isdir(outFolder)):
        shutil.rmtree(outFolder)
    
    os.mkdir(outFolder)


###################################################################
# This function create folder remove input raster
#
###################################################################
def remove_raster(list_rasterName, prjPath):
    cmd = "grass " + prjPath + " -f --exec g.remove -f type=raster name=" + list_rasterName

    run_grass_cmd(cmd)



def process_data(prjPath, f, dataFolder):
    if (".tif" in f):
        """
        import main raster and vector tile
        """
        dtm_raster = import_raster( os.path.join(dataFolder, "dtm", f), f.replace(".tif", ".tif"), prjPath )
        tile_vector = import_vector( os.path.join(dataFolder, "tile", f.replace("_dtm.tif", "_tile.shp")), "tile", prjPath )

        """
        Convert file name to number
        """

        # splitName = [c for c in f]
        # arr = [splitName[i] for i in (2,3,4,5,6,7,8,9,10)]
        # id_raster = ""
        # for e in arr:
        #     id_raster = id_raster + str(e)
        # id_raster = int(id_raster)

        # splitName = [c for c in f]
        # arr = [splitName[i] for i in (0,1,2,3,4,5,6,7)]
        
        # f name is something like arr_col-arr_row-dtm_flt_dtm  >>  eg>> 2707-970-dtm_flt_dtm
        arr_col = int(f[:4])
        arr_row = int(f[5:8])
        id_raster = f[:8]
        """
        Get ID of nearest dtm
        """
        nearest_idx = []
        nearest_idx.append(str(arr_col + 1)+ '-' +str(arr_row   ))
        nearest_idx.append(str(arr_col + 1)+ '-' +str(arr_row +1))
        nearest_idx.append(str(arr_col    )+ '-' +str(arr_row +1))
        nearest_idx.append(str(arr_col - 1)+ '-' +str(arr_row +1))
        nearest_idx.append(str(arr_col - 1)+ '-' +str(arr_row   ))
        nearest_idx.append(str(arr_col - 1)+ '-' +str(arr_row -1))
        nearest_idx.append(str(arr_col    )+ '-' +str(arr_row -1))
        nearest_idx.append(str(arr_col + 1)+ '-' +str(arr_row -1))
        """
        Import nearest raster
        """
        rasterName_arr = []
        for iter, n_id in enumerate(nearest_idx):
            rasterName = f.replace(str(id_raster), str(n_id))
            rasterName_arr.append( import_raster( os.path.join(dataFolder, "dtm", rasterName), rasterName.replace(".tif", ""), prjPath ) )
        
        """
        Set region
        """
        set_region(tile_vector, 1, prjPath, "vector")

        """
        Merge all dtm
        """
        list_rasterName = f #.replace(".tif", "")
        for raster in rasterName_arr:
            if ( raster is not None ):
                list_rasterName = list_rasterName + "," + raster
        
        raster_name = merge_raster(list_rasterName, prjPath, f.replace(".tif", "_3x3_merge"))

        """
        Export raster map
        """
        export_raster_map(raster_name, prjPath, dataFolder)

        """
        Delete all rester
        """
        list_rasterName = list_rasterName + "," + str(raster_name)
        remove_raster(list_rasterName, prjPath)


###################################################################
# Main function
#
###################################################################
if __name__ == "__main__":
    coord_system_code = 32632
    location_name = "trentinoLocation"

    """
    Set name of first and last dtm to be processed
    """
    # first_dtm = "5h691551305_DSMFirst_dtm"
    # last_dtm = "5h691551340_DSMFirst_dtm"

    """
    Set input data folder
    """
    # dataFolder = "/root/data/input/qgis/2/output"
    dataFolder = "/root/PV_ferrara/test_data/output"

    """
    Set project path
    """
    base_location = os.path.join("home", location_name)

    """
    Create new project Location
    """
    prjPath = create_project(coord_system_code, base_location)

    """
    Check outFolder
    """
    check_outfolder(dataFolder)

    # start_process = False
    for f in os.listdir( os.path.join(dataFolder, "dtm") ):
        if ("xml" not in f):
            process_data(prjPath, f, dataFolder)



        


        
    

