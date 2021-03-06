#
# huge_file_sort_spatial_coherence.py
#
# (c) 2014, martin isenburg - http://rapidlasso.com
#     rapidlasso GmbH - fast tools to catch reality
#
# This LAStools pipeline sorts huge LAS or LAZ files
# into a more coherent point order using a tile-based
# multi-core pipeline. The input file is first tiled
# using lastile with the specified tile size. All tiles
# are then sorted into a spatially coherent z-order 
# (e.g. space-filling curve). The sorted tiles are then
# merged back into a single file and all temporary tiles
# are deleted.
#
# LiDAR input:   LAS/LAZ/BIN/TXT/SHP/BIL/ASC/DTM
# LiDAR output:  LAS/LAZ/BIN/TXT
#
# for licensing see http://lastools.org/LICENSE.txt
#

import sys, os, arcgisscripting, subprocess

def check_output(command,console):
    if console == True:
        process = subprocess.Popen(command)
    else:
        process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True)
    output,error = process.communicate()
    returncode = process.poll()
    return returncode,output 

### create the geoprocessor object
gp = arcgisscripting.create(9.3)

### report that something is happening
gp.AddMessage("Starting huge_file_sort_spatial_coherence ...")

### define positions of arguments in argv array
arg_input_file     =  1
arg_tile_size      =  2
arg_bucket_size    =  3
arg_cores          =  4
arg_empty_temp_dir =  5
arg_output_file    =  6
arg_output_format  =  7
arg_verbose        =  8
arg_count_needed   =  9

### get number of arguments
argc = len(sys.argv)

### make sure we have right number of arguments
if argc != arg_count_needed:
    gp.AddMessage("Error. Wrong number of arguments. Got " + str(argc) + " expected " + str(arg_count_needed))
    sys.exit(1)    

### report arguments (for debug)
#gp.AddMessage("Arguments:")
#for i in range(0, argc):
#    gp.AddMessage("[" + str(i) + "]" + sys.argv[i])

### get selected arguments
empty_temp_dir = sys.argv[arg_empty_temp_dir]

### get the path to LAStools
lastools_path = os.path.dirname(os.path.dirname(os.path.dirname(sys.argv[0])))

### make sure the path does not contain spaces
if lastools_path.count(" ") > 0:
    gp.AddMessage("Error. Path to .\\lastools installation contains spaces.")
    gp.AddMessage("This does not work: " + lastools_path)
    gp.AddMessage("This would work:    C:\\software\\lastools")
    sys.exit(1)    

### make sure the path does not contain open or closing brackets
if (lastools_path.count("(") > 0) or (lastools_path.count(")") > 0):
    gp.AddMessage("Error. Path to .\\lastools installation contains brackets.")
    gp.AddMessage("This does not work: " + lastools_path)
    gp.AddMessage("This would work:    C:\\software\\lastools")
    sys.exit(1)   

### complete the path to where the LAStools executables are
lastools_path = lastools_path + "\\bin"

### check if path exists
if os.path.exists(lastools_path) == False:
    gp.AddMessage("Cannot find .\\lastools\\bin at " + lastools_path)
    sys.exit(1)
else:
    gp.AddMessage("Found " + lastools_path + " ...")

### create the full path to the lastile executable
lastile_path = lastools_path+"\\lastile.exe"

### check if the lastile executable exists
if os.path.exists(lastile_path) == False:
    gp.AddMessage("Cannot find lastile.exe at " + lastile_path)
    sys.exit(1)
else:
    gp.AddMessage("Found " + lastile_path + " ...")

### create the full path to the lassort executable
lassort_path = lastools_path+"\\lassort.exe"

### check if the lassort executable exists
if os.path.exists(lassort_path) == False:
    gp.AddMessage("Cannot find lassort.exe at " + lassort_path)
    sys.exit(1)
else:
    gp.AddMessage("Found " + lassort_path + " ...")

### create the full path to the lasmerge executable
lasmerge_path = lastools_path+"\\lasmerge.exe"

### check if the lasmerge executable exists
if os.path.exists(lasmerge_path) == False:
    gp.AddMessage("Cannot find lasmerge.exe at " + lasmerge_path)
    sys.exit(1)
else:
    gp.AddMessage("Found " + lasmerge_path + " ...")

### check if the empty temp directory exists
if os.path.exists(empty_temp_dir) == False:
    gp.AddMessage("Cannot find empty temp dir " + empty_temp_dir)
    sys.exit(1)
else:
    gp.AddMessage("Found " + empty_temp_dir + " ...")

### make sure the empty temp directory is emtpy
if os.listdir(empty_temp_dir) != []:
    gp.AddMessage("Empty temp directory '" + empty_temp_dir + "' is not empty")
    sys.exit(1)
else:
    gp.AddMessage("And it's empty ...")

###################################################
### first step: tile huge input file
###################################################

### create the command string for lastile.exe
command = ['"'+lastile_path+'"']

### maybe use '-verbose' option
if sys.argv[arg_verbose] == "true":
    command.append("-v")

### add input LiDAR
command.append("-i")
command.append('"'+sys.argv[arg_input_file]+'"')

### maybe use a user-defined tile size
if sys.argv[arg_tile_size] != "1000":
    command.append("-tile_size")
    command.append(sys.argv[arg_tile_size].replace(",","."))

### maybe an output directory was selected
if empty_temp_dir != "#":
    command.append("-odir")
    command.append('"'+empty_temp_dir+'"')

### give temporary tiles a meaningful name
command.append("-o")
command.append("temp_huge_sort_spatial_coherence.laz")

### store temporary tiles in compressed format
command.append("-olaz")

### report command string
gp.AddMessage("LAStools command line:")
command_length = len(command)
command_string = str(command[0])
command[0] = command[0].strip('"')
for i in range(1, command_length):
    command_string = command_string + " " + str(command[i])
    command[i] = command[i].strip('"')
gp.AddMessage(command_string)

### run command
returncode,output = check_output(command, False)

### report output of lastile
gp.AddMessage(str(output))

### check return code
if returncode != 0:
    gp.AddMessage("Error. huge_file_sort_spatial_coherence failed in lastile step.")
    sys.exit(1)

### report success
gp.AddMessage("lastile step done.")

###################################################
### second step: spatial coherent sort of each tile
###################################################

### create the command string for lassort.exe
command = ['"'+lassort_path+'"']

### maybe use '-verbose' option
if sys.argv[arg_verbose] == "true":
    command.append("-v")

### add input LiDAR
command.append("-i")
if empty_temp_dir != "#":
    command.append('"'+empty_temp_dir+"\\temp_huge_sort_spatial_coherence*.laz"+'"')
else:
    command.append("temp_huge_sort_spatial_coherence*.laz")

# specify the bucket size used in the spatial sort
command.append("-bucket_size")
command.append(sys.argv[arg_bucket_size].replace(",","."))

# existing tiling is not of relevance for this application
command.append("-destroy_tiling")

### give duplicate-removed tiles a meaningful appendix
command.append("-odix")
command.append("_s")

### store duplicate-removed tiles in compressed format
command.append("-olaz")

### maybe we should run on multiple cores
if sys.argv[arg_cores] != "1":
    command.append("-cores")
    command.append(sys.argv[arg_cores])

### report command string
gp.AddMessage("LAStools command line:")
command_length = len(command)
command_string = str(command[0])
command[0] = command[0].strip('"')
for i in range(1, command_length):
    command_string = command_string + " " + str(command[i])
    command[i] = command[i].strip('"')
gp.AddMessage(command_string)

### run command
returncode,output = check_output(command, False)

### report output of lassort
gp.AddMessage(str(output))

### check return code
if returncode != 0:
    gp.AddMessage("Error. huge_file_sort_spatial_coherence failed in lassort step.")
    sys.exit(1)

### report success
gp.AddMessage("lassort step done.")

###################################################
### third step: merge coherent tiles into one file
###################################################

### create the command string for lastile.exe
command = ['"'+lasmerge_path+'"']

### maybe use '-verbose' option
if sys.argv[arg_verbose] == "true":
    command.append("-v")

### add input LiDAR
command.append("-i")
if empty_temp_dir != "#":
    command.append('"'+empty_temp_dir+"\\temp_huge_sort_spatial_coherence*_s.laz"+'"')
else:
    command.append("temp_huge_sort_spatial_coherence*_s.laz")

### maybe an output file name was selected
if sys.argv[arg_output_file] != "#":
    command.append("-o")
    command.append('"'+sys.argv[arg_output_file]+'"')

### maybe an output format was selected
if sys.argv[arg_output_format] != "#":
    if sys.argv[arg_output_format] == "las":
        command.append("-olas")
    elif sys.argv[arg_output_format] == "laz":
        command.append("-olaz")
    elif sys.argv[arg_output_format] == "bin":
        command.append("-obin")
    elif sys.argv[arg_output_format] == "xyzc":
        command.append("-otxt")
        command.append("-oparse")
        command.append("xyzc")
    elif sys.argv[arg_output_format] == "xyzci":
        command.append("-otxt")
        command.append("-oparse")
        command.append("xyzci")
    elif sys.argv[arg_output_format] == "txyzc":
        command.append("-otxt")
        command.append("-oparse")
        command.append("txyzc")
    elif sys.argv[arg_output_format] == "txyzci":
        command.append("-otxt")
        command.append("-oparse")
        command.append("txyzci")

### report command string
gp.AddMessage("LAStools command line:")
command_length = len(command)
command_string = str(command[0])
command[0] = command[0].strip('"')
for i in range(1, command_length):
    command_string = command_string + " " + str(command[i])
    command[i] = command[i].strip('"')
gp.AddMessage(command_string)

### run command
returncode,output = check_output(command, False)

### report output of lasmerge
gp.AddMessage(str(output))

### check return code
if returncode != 0:
    gp.AddMessage("Error. lasmerge failed.")
    sys.exit(1)

### report success
gp.AddMessage("lasmerge step done.")

###################################################
### final step: clean-up all temporary files
###################################################

### create the command string for clean-up
command = ["del"]

### add temporary files wildcard
if empty_temp_dir != "#":
    command.append('"'+empty_temp_dir+"\\temp_huge_sort_spatial_coherence*.laz"+'"')
else:
    command.append("temp_huge_sort_spatial_coherence*.laz")

### report command string
gp.AddMessage("clean-up command line:")
command_length = len(command)
command_string = str(command[0])
command[0] = command[0].strip('"')
for i in range(1, command_length):
    command_string = command_string + " " + str(command[i])
    command[i] = command[i].strip('"')
gp.AddMessage(command_string)

### run command
returncode,output = check_output(command, False)

### report output of clean-up
gp.AddMessage(str(output))

### check return code
if returncode != 0:
    gp.AddMessage("Error. huge_file_sort_spatial_coherence failed in clean-up step.")
    sys.exit(1)

### report success
gp.AddMessage("clean-up step done.")

### report happy end
gp.AddMessage("Success. huge_file_sort_spatial_coherence done.")
