import argparse
import yaml
import re
import pickle
import sys
import subprocess
import logging
from logging.handlers import RotatingFileHandler
import datetime
import os

#--------------------------------------FUNCTIONS--------------------------------------------

#We check if a file can be accessed
def check_file(file,mode):
    try:
        with open(file,mode) as f:
            pass
    except FileNotFoundError:
        logger.error("file {0} not found".format(file))
        print("file {0} not found".format(file), file=sys.stderr)
        return 0
    except:
        print("file {0} cannot be accessed, error is {1}".format(file,sys.exc_info()), file=sys.stderr)
        logger.error("file {0} cannot be accessed, error is {1}".format(file,sys.exc_info()))
        return 0
    else:
        return 1

#We read and return the files from the configuration file
def read_files(configfile):
    try:
        with open(configfile,"r") as f:
            files = yaml.load(f)
            #We prefer not showing the list of files in the logs
            logger.debug("Files are {0}".format(files))
            return files
    except FileNotFoundError:
        logger.error("Configfile {0} not found, timemachine must now exit".format(configfile))
        print("Config file {0} not found, timemachine must now exit".format(configfile), file=sys.stderr)
        sys.exit(1)

#We write a new list of files to the configuration file
def write_files(configfile,files):
    if check_file(configfile,"w"):
        with open(configfile,"w") as f:
            yaml.dump(files, f, default_flow_style=False)
    else:
        logger.error("timemachine must exit")
        print("timemachine must exit", file=sys.stderr)
        sys.exit(1)

#We check the configuration file and create a new one if necessary
def create_configfile(configfile,configfile_location):
    empty = 0

    #We make sure the user has not specified a path in the configuration filename
    if not configfile.find("/") == -1 :
        logger.error("the configuration filename must not contain a path, use option -cl to specify the path to the file")
        logger.error("timemachine must now exit")
        print("the configuration filename must not contain a path, use option -cl to specify the path to the file", file=sys.stderr)
        print("timemachine must now exit", file=sys.stderr)
        sys.exit(1)

    #We create the configuration file if it doesn't exit
    #If it exists, then we check we can access the file. If we can't, then we exit.
    if not os.path.isfile(configfile_location+configfile):
        subprocess.call(["touch",configfile_location+configfile])
        empty=1
    elif not check_file(configfile_location+configfile,"r"):
        #this condition checks if the file can be accessed for reading.
        print("timemachine must now exit", file=sys.stderr)
        sys.exit(1)

    #If the configuration file is empty, we add an empty list
    if os.path.getsize(configfile_location+configfile) == 0:
        write_files(configfile_location+configfile,[])
        empty=1

    #We check if the configuration file contains an empty list.
    if (read_files(configfile_location+configfile)) == []:
        empty=1

    #If the file size is 0 or if the file contains an empty list, then we notify that the configfile is empty.
    if empty:
        logger.error("Configuration file is empty, please add files")
        print("Configuration file is empty, please add files", file=sys.stderr)


#We log and print the following parameters
def log(configfile,filepath,destination):
    logger.debug("Config file is {0}".format(configfile))
    print("Config file is {0}".format(configfile))

    logger.debug("History of files recorded in {0}".format(filepath))
    print("History of files recorded in {0}".format(filepath))

    logger.debug("Destination of backups is {0}".format(destination))
    print("Destination of backups is {0}".format(destination))


#The function below opens and returns the pickle content of a file
#Applied to our script : We read the dictionnary of recorded modification dates from a record file
def read_dates_recorded(filepath):
    try:

        with open(filepath,"rb") as f:
            return pickle.load(f)
    except FileNotFoundError:
        return {}

#We record a modification date into our record file
def write_dates_recorded(file, date,dates_recorded,filepath):
#We enter a new record or modifiy an existing record in the dictionary dates_recorded
# and we write that dictionnary to the record file filepath

    dates_recorded[file] = date
    with open(filepath,"wb") as f:
        logger.debug("Writing dates_recorded to {0}".format(filepath))
        print("Writing dates_recorded to {0}".format(filepath))
        return pickle.dump(dates_recorded, f)

#We verify if we can access a destination path
def check_path(destination,logging):
#The logging parameter allows us to have no error when check_path is called the first time
#Reminder : The first time the function is called, the logger is not instanciated so we should not log.

    if not os.path.isdir(destination):
        print("The folder {0} was not found, timemachine must now exit".format(destination), file=sys.stderr)
        if logging: #We don't log the first time check_path is called in the script
            logger.error("The folder {0} was not found, timemachine must now exit".format(destination))
        sys.exit(1)
    elif not os.access(destination, os.W_OK):
        print("The folder {0} cannot be accessed with write permission, timemachine must now exit".format(destination), file=sys.stderr)
        if logging: #We don't log the first time check_path is called in the script
            logger.error("The folder {0} cannot be accessed with write permission, timemachine must now exit".format(destination))
        sys.exit(1)

#We copy a file to a specified folder.
#The copied filename has the last modification date appended to it.This allows us to maintain unique backup files.
def copy_file(file,destination,timestamp):
    check_path(destination,1)#we exit the script if the backup destination can't be accessed

    timestamp_formated = str(datetime.datetime.fromtimestamp(timestamp))

    #We extract the filename only from the original file specified.
    #Example : we extract file1.txt from /home/admin/file1.txt
    #That allow use to copy file1.txt to the destination folder.
    filelist = file.split("/")
    filename = filelist[-1]
    subprocess.call(["cp",file,destination+timestamp_formated+filename]) #We append the timestamp to the destination backup file
    logger.debug("{0} was copied to {1}".format(file,destination+timestamp_formated+filename))
    print("{0} was copied to {1}".format(file,destination+timestamp_formated+filename))

#We format the destination folder
def format_destination(destination):
#We add a '/' at the end of destination folder if not specified
#It is useful for example when copying a backup file in check_for_modif
#It allows us to append the timestamp to the destination backup file and not have formating error.
#It is also used for everytime we concatenate destination+configfile and destination+

    if not destination[-1] == "/":
        destination = destination + "/"
    return destination

#We check if file has been modified and take a backup of the file if that's the case
def check_for_modif(file,destination,dates_recorded):
    #We make sure the file can be read
    if check_file(file,"r"):
        timestamp=os.path.getmtime(file)
        #Here we check if there is an entry already in the dictionnary for that file.
        if dates_recorded.get(file) is not None:
            #We check if the file has been modified.
            #We compare the current timestamp with the recorded timestamp in the dictionnary.
            if timestamp > dates_recorded[file]:
                logger.debug("{0} has been modified since last backup, we run new backup".format(file))
                print("{0} has been modified since last backup, we run new backup".format(file))
                #We copy the file to the destination folder
                #The copied file will have the timestamp appended to its filename.
                copy_file(file,destination,timestamp)
                #We then record that file and timestamp into the dictionnary and write into the record file
                write_dates_recorded(file,timestamp,dates_recorded,destination+DATE_RECORD_FILE)
            else:
                logger.debug("{0} has not been modified".format(file))
                print("{0} has not been modified".format(file))
        else:#We have no existing entry in the dictionnary, we then do the 1st backup of the file
            logger.debug("we run 1st backup of {0}".format(file))
            print("we run 1st backup of {0}".format(file))
            #We copy the file to the destination folder
            #The copied file will have the timestamp appended to its filename.
            copy_file(file,destination,timestamp)
            #We then record that file and timestamp into the dictionnary and write into the record file.
            write_dates_recorded(file,timestamp,dates_recorded,destination+DATE_RECORD_FILE)



#We print a sorted list of files being observed from the configuration file specified
def print_files(configfile):
    logger.debug("The command to list files being observed was called")
    files = read_files(configfile)
    files.sort()
    print("The list of files being observed is")
    for file in files:
        print(file)


#We add a file into the configuration file
def add_file(configfile,files,file):
    logger.debug("The command to add a file was called")
    #Condition where the file was not already in the configuration file.
    # We then append that file to the list files, and write that list into the configuration file.
    if file not in files:
        files.append(file)
        write_files(configfile,files)
        print("{1} was added to configfile {0}".format(configfile,file))
        logger.debug("{1} was added to configfile {0}".format(configfile,file))
    else:#Condition where the file is already in the configuration file.
        # We want a uniq list of files, so we don't append the file again.
        print("{1} is already in configfile {0}".format(configfile,file), file=sys.stderr)
        logger.error("{1} is already in configfile {0}".format(configfile,file))
        sys.exit(1)

#we remove a file from the configuration list
def remove_file(configfile,files,file):
    logger.debug("The command to remove a file was called")
    try:
        files.remove(file)
    except Exception as e:
        #If we couldn't remove the file from the list, we alert and exit.
        s = str(e)
        #Condition where the file to remove is not in the list.
        if s == "list.remove(x): x not in list":
            print("{0} is not in the configuration list".format(file), file=sys.stderr)
            logger.error("{0} is not in the configuration list".format(file))
        else:#Condition where the file can't be removed due to another error.
            print("{0} could not be removed, error is {1}".format(file,s), file=sys.stderr)
            logger.error("{0} could not be removed, error is {1}".format(file,s))
        sys.exit(1)
    #If we have no exited we write the new list into the configuration file
    write_files(configfile,files)
    print("{1} was removed from configfile {0}".format(configfile,file))
    logger.debug("{1} was removed from configfile {0}".format(configfile,file))



#-----------------------------------------BODY--------------------------------------------


#DATE_RECORD_FILE : filename used to records modification dates
DATE_RECORD_FILE = "records_sent.dat"

#Instantiation of command line arguments
parser = argparse.ArgumentParser( description='Backup files on modifications - Use Crontab to schedule')
parser.add_argument('-c', '--configfile', default="config.dat", help='specify the configuration filename. Only a filename without the path is allowed. Default is config.dat')
parser.add_argument('-cl', '--configfile_location', default=".", help='specify the location path of the configuration filename. Default is \'.\'')
parser.add_argument('-d', '--destination', default=".", help='specify the destination path where files should be backed up. Default is \'.\'')
parser.add_argument('-l', '--list', action="store_true", help='list the files being observed from the configuration file specified')
parser.add_argument('-a', '--add', help='add a file to the list of files being observed. The filename may contain the absolute path')
parser.add_argument('-r', '--remove',help='remove a file to the list of files being observed. The filename may contain the absolute path. Note that -l takes precedence over -a and -a takes precedence over -r')

#We read comand line arguments
args = parser.parse_args()

#We format the variables
destination = format_destination(args.destination) #We format the destination string
configfile_location = format_destination(args.configfile_location) #We format the destination string
configfile=configfile_location+args.configfile #We add the path provided to the configfile name
record_file=destination+DATE_RECORD_FILE #We add the path provided to the history of records file.

#We first make sure that the path to the configuration file can be accessed and be written to.
#  If not we exit the script.
#Calling it here allows us to write logs into that path with no subsequent error.
#The second parameter 0 ensures that we don't try to log.
check_path(configfile_location,0)

#Instantiation of logging
LOG_FILENAME = configfile_location+'timemachine.log'
rotating_handler = RotatingFileHandler(LOG_FILENAME,
				    maxBytes=10000000,
				    backupCount=3)
formatter = logging.Formatter('%(asctime)s %(levelname)-8s %(message)s')
rotating_handler.setFormatter(formatter)

logger = logging.getLogger('demoapp')
logger.setLevel(logging.DEBUG)
logger.addHandler(rotating_handler)

#Print and log
logger.debug("...........Timemachine started...........")
print("...........Timemachine started...........")

#We create the configuration file if it doesn't exist or is empty
create_configfile(args.configfile,configfile_location)

#We read the list of files from the configuration file
files = read_files(configfile)

#We print and log to the user the name of the configfile, history of records, destination.
log(configfile,record_file,destination)

#We read the history of files recorded
dates_recorded = read_dates_recorded(record_file)

#We perform the queries of the user.
#It is based on the command line arguments provided by the user
if args.list:
    print_files(configfile) #We print the list of files from configfile
elif args.add:
    add_file(configfile,files,args.add) #We add a file to the list of files in configfile
elif args.remove:
    remove_file(configfile,files,args.remove)#We remove a file to the list of files in configfile
else:
    for file in files: #We check for modifications and backup the modified files
        check_for_modif(file,destination,dates_recorded)




