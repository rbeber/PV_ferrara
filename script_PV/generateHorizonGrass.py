import os, shutil
import subprocess, shlex
from subprocess import Popen, PIPE
from calendar import monthrange
import datetime
from multiprocessing import Process, Pool
import multiprocessing as mp
import timeit
import time
import sys


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
# This function import raster
#
###################################################################
def import_raster(inFile, outName, prjPath):
    cmd = "grass " + prjPath + " --exec r.import input=" + inFile + " output=" + outName

    run_grass_cmd(cmd)

    return outName


###################################################################
# This function import vector
#
###################################################################
def import_vector(inFile, outName, prjPath):
    cmd = "grass " + prjPath + " --exec v.import --overwrite input=" + inFile + " output=" + outName

    run_grass_cmd(cmd)

    return outName


###################################################################
# This function set grass region
#
###################################################################
def set_region(vector_name, res, prjPath, region_type):
    cmd = "grass " + prjPath + " --exec g.region " + region_type + "=" + vector_name + " res=" + str(res)

    run_grass_cmd(cmd)


###################################################################
# This function compute r.horizon function
#
###################################################################
def compute_horizon(raster_name, prjPath, start=0, end=80, step=10, bufferzone=500, outName="horangle", maxdistance=5000):
    cmd = "grass " + prjPath + " -f --exec r.horizon elevation=" + raster_name + " step=" + str(step) + " bufferzone=" + str(bufferzone) + " output=" + outName + " maxdistance=" + str(maxdistance) + " start=" + str(start) + " end=" + str(end)
    run_grass_cmd(cmd)


###################################################################
# This function prepare data for r.horizon function
#
###################################################################
def process_data(inputData):
    compute_horizon(inputData[0], inputData[1], inputData[2], inputData[3], inputData[4], inputData[5], inputData[6], inputData[7])


###################################################################
# This function export horizon maps
#
###################################################################
def export_horizon_map(horizon_name, outFolder):
    cmd = "grass " + prjPath + " --exec r.out.gdal input=" + horizon_name + " output=" + os.path.join(outFolder, horizon_name) + " format=GTiff"

    run_grass_cmd(cmd)

###################################################################
# This function create folder to save all output
#
###################################################################
def check_outfolder(dataFolder):
    outFolder = os.path.join(dataFolder, "horizon")

    if (os.path.isdir(outFolder)):
        shutil.rmtree(outFolder)
    
    os.mkdir(outFolder)

    return outFolder


###################################################################
# This function create folder remove input raster
#
###################################################################
def remove_raster(list_rasterName, prjPath):
    cmd = "grass " + prjPath + " -f --exec g.remove -f type=raster name=" + list_rasterName

    run_grass_cmd(cmd)


###################################################################
# This function prepare data to compute horizon maps
#
###################################################################
def prepare_data(r, prjPath, dataFolder, horizon_start, horizon_end, horizon_step, horizon_bufferzone, horizon_maxdistance, outFolder):
    if (".tif" in r):
        """
        Set name of horangle maps
        """
        horizon_name = r.replace(".tif", "_horangle")

        """
        Import Raster
        """
        raster_name = import_raster(os.path.join(dataFolder, "dtm", r), r, prjPath)

        """
        Import vector tile
        """
        tile_name = import_vector(os.path.join(dataFolder, "tile", r.replace("_dtm.tif", "_tile.shp")), "tile", prjPath)
        
        """
        Set grass region
        """
        set_region(tile_name, 1, prjPath, "vector")

        """
        Compute Horizon
        """
        procs = ()
        step_arr = [0]
        x = 0
        for i in range(0, int(horizon_end/horizon_step)+1):
            x = x + horizon_step
            if (x >= 360):
                x = 360
                step_arr.append(x)
                break
            step_arr.append(x)
        
        start = 0
        for count, end_step in enumerate(step_arr):
            if (count == 0):
                continue
            elif (count % max_proccess_step == 0):
                procs += ( [raster_name, prjPath, start, end_step, horizon_step, horizon_bufferzone, horizon_name, horizon_maxdistance,], )
                start = end_step
        
        if (start < 360):
            procs += ( [raster_name, prjPath, start, end_step, horizon_step, horizon_bufferzone, horizon_name, horizon_maxdistance,], )
        
        with Pool(MAX_PROCESSOR) as p:
            p.map(process_data, procs)

        """
        Export horizon map
        """
        list_rasterName = raster_name
        for i in range( int(horizon_end/horizon_step) ):
            step = '%03d' % (horizon_step * i)
            h_name = horizon_name + "_" + str(step)
            export_horizon_map(h_name, outFolder)
            list_rasterName = list_rasterName + "," + str(h_name)
        
        """
        Remove all maps
        """
        remove_raster(list_rasterName, prjPath)

###################################################################
# Main function
#
###################################################################
if __name__ == "__main__":
    """
    Get Start Time
    """
    start_time_main = timeit.default_timer()

    """
    Do not modify this variable
    """
    location_name = "/home/trentinoLocation"

    """
    Modify these variables according to your project
    """
    coord_system_code = 7791
    dataFolder = "/root/Data/dtm/output"
    max_proccess_step = 4                           # Indicates how many steps to process each individual r.horizon process
    horizon_step = 10
    horizon_start = 0
    horizon_end = 360
    horizon_bufferzone = 500
    horizon_name = "horangle"
    horizon_maxdistance = 1500

    # start_dtm = "5h691551305_DSMFirst_dtm_9x9_merge"
    # last_dtm = "5h691551310_DSMFirst_dtm_9x9_merge"

    """
    Create new project Location
    """
    prjPath = create_project(coord_system_code, location_name)

    """
    Check output folder
    """
    outFolder = check_outfolder(dataFolder)

    """
    Compute horizon maps
    """
    start_process = False
    for r in sorted( os.listdir(os.path.join(dataFolder, "dtm")) ):
        # if (start_dtm in r):
        #     start_process = True
        # elif (last_dtm in r):
        #     start_process = False
        #     prepare_data(r, prjPath, dataFolder, horizon_start, horizon_end, horizon_step, horizon_bufferzone, horizon_maxdistance, outFolder)
        
        # if (start_process):
        prepare_data(r, prjPath, dataFolder, horizon_start, horizon_end, horizon_step, horizon_bufferzone, horizon_maxdistance, outFolder)

    
    """
    Get Elapsed Time
    """
    elapsed_time = timeit.default_timer() - start_time_main
    print ("---> Time elapsed r.horizon: " + time.strftime("%H:%M:%S", time.gmtime(elapsed_time)))