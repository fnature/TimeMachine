
Timemachine is a tool that takes copies of specified files and builds a history of their changes over time.
Assignement 2 of module Scrypting for Sys Automation in Msc Cloud Computing 2018.

See SFSA- 2017-18 Assessment 2.pdf for requirements.

This paper provides an overview of the design decisions and how to use the application.

---------------------------------
Index 
---------------------------------

- Rouch Design
- Design Decisions
- Assumptions
- Failure Modes
- Howtos and Testing

Note :
Config file or configfile means the configuration file.

---------------------------------
Rough design
---------------------------------


—— functions ——

check file is healthy
read files from config file
write files to config file

check and create a new config file

log and print some parameters

read record  from date config file
write  record in date config file

check path is healthy
copy a file with timestamp appended to filename

format the name of the destination folder

check modification and backup
  if the modify date is higher that the one in date config file or if the file is not in date config file
        then
            make a copy of the file to current directory
            write record with new date in date config file

print files from config file 
add file to config file 
remove file from config file 

—— body ——

We configure, instantiate and format variables, filenames and files :
filename used to records modification dates
instantiate command line arguments
read command line args ( using argpase and instantiate the defaults )
format the string of global variables to fit our script : destination, configfile and record_file

check path of configuration file is healthy

instantiation of logging


check and create a new config file
read files from config file

print and log configfile, history of records, destination
read record from date config file

if arg = list
    print files from config file 
elseif arg = add
    add file from config file
elseif arg = remove
    remove file from config file
else
for file in config file
    check modification and backup


---------------------------------
Design decisions
---------------------------------


Requirement
“It should take an initial copy when the file is first added to the configuration or the script is first run and then it should take a copy each time  it checks only if the file has changed since the script last checked”

To achieve that, we use 3 main components :
	
Config file
	- Config file contains a list of files timemachine will observe
	- We use YAML so that users can edit the file.
	- default is config.dat
	- We use a list of string. Each string is a filename.
	- A filename can contain the absolute path to the file
	

records_sent.dat
	- We use a file to keep a record when a file was modified then we make a backup of the file.
	- The file is always records_sent.dat
	- We use Pickle to write our recorded_dates, as we don’t need user to view or edit that file.
	
recorded_dates :
    - It is a dictionary containing our records of filename along with modification date. 
    - the key is the filename
    - the value is the last modification date of the file.
    - This allows to easily add or replace an existing entry because keys are uniq in a dictionary.

Requirement
“The tool must support watching and taking copies of multiple files.”
	- The use of YAML configuration file containing a list of multiple files allows to work with multiple files.
	- Note that the script allows to have duplicates if the configfile was created manually.
	- When files are added using the script command argument, it makes sure there is no duplicate.
	- We copy the files with the modification date appended to the backup filename. Therefore we can maintain multiple unique backup files.


Requirement:
The tool must read the list of files to observe from a configuration file. And the configuration filemust be editable by the user.
	- The use of YAML for the configuration file allows us this.


The tool must be able to take as an optional command line argument the location of the configuration file. If this is not provided it should default to reading from config.dat in the directory the script is run from. 
	- We use argparse module to implement this.
	- the command line argument -c specifies the filename. We don’t support having path in the filename. Path must be provided with -cl
	- the command line argument -cl specifies the location of the configuration file
	- We support absolute and relative path for -cl
	- the default is specified using argparse.
	- The choice of having -cl allows us to easily check if we can access the location
		-   see line 274 check_path(configfile_location,0)
	

The tool must be able to take as an optional command line argument the path to a directory where the copies and any information about the copies should be stored. If this option is not provided, the tool must default to using the directory the script is run from.
	- the command line argument -d specifies the destination folder
	- We support absolute and relative path for the destination folder
	- we also store in that destination folder our records of backups in the file records_sent.dat
	- therefore when a different backup folder is specified, a new records_sent.dat will be created, and all files will be copied.
	- the default is specified using argparse.


The tool must log important actions.
	- we use the module logging with following parameters maxBytes=10000000 and backupCount=3
	- we log and print to stdout all important actions.
	- we log to the file timemachine.log
	- timemachine.log is stored in the same location as the configuration file.


The tool must gracefully handle errors e.g. due to bad or missing data. 
	- See section on failures modes.


“The tool must check files once a minute and take a copy of any which have changed.”

	- Users must configure crontab to run the script.
	- example :
		1/ contrab -e
		2/ add the following line
			* * * * * /usr/bin/python3 /home/admin/PycharmProjects/Assignment2/timemachine.py -c config.dat -cl /home/admin -d /home/admin/Backup > /dev/null
			
			- this will run the script every minute.
			- the config file name is config.dat
			- the location of the config name is /home/admin
			- the destination folder of backups is /home/admin/Backup
			- the folder where records_sent.dat will be stored is /home/admin/Backup
			- the folder where timemachine.log will be stored is /home/admin


The tool must be robust to starting and stopping.
	- Thanks to the records in records_sent.dat, we can keep track of changes after the script stops.
	- Note also that we write the record only after we have successfully written the backup of a file.

---------------------------------
Assumptions
---------------------------------
Assumption about user will use crontab. We mention to use crontab in the help menu.

Files may be entered with absolute path or relative path in configfile
 
If the user has deleted the backup files, then the end user must delete the records_sent.dat manually in the backup folder in order to delete history memory and backup the files again. Otherwise the user may choose to backup in a different folder.


---------------------------------
Failure Modes
---------------------------------

We have multiple checks to make sure the program handles issue gracefully. We miss the time to review all that has been implemented. We have other checks that we may not present here. Please read the script for more details.

Timemachine quits gracefully :
	- We quit gracefully if config file or location of config file or destination folder can’t be accessed

	- We check that the destination folder can be accessed just before backing up a file ( we use the subprocess and cp command).

	- We inform with print and logging. We also add a message that timemachine will exit now. So that when program is run by crontab for example, and user look at the logs and will understand that the program didn’t run.


	- We quit gracefully if configfile can’t be accessed ( example : bad permission )


Timemachine handles also
	- if a file being observed can’t be accessed ( example : missing or bad permission or locked ), then we log a message. Note that the script would not backup online files that would be already opened by other applications.


	- We support if the destination folder is given in command line argument with a ‘/‘ or not at the end
		example -d /Backup or -d /Backup/
		To support this, if we have /Backup then we change it automatically to /Backup/
		This allows us to copy files to that destinations.


	- We handle if there is no configfile
		- if that’s the case, then we create it with an empty list, and we inform users to add files to it.
		- see the chapter above on the usage of list/add/remove

	

---------------------------------
Howtos and Testing
---------------------------------



---------chapter how to list/add/remove files---------

requirement
“python3 timemachine.py add somefile should add somefile to the list of files to be observed.python3 timemachine.py remove somefile should remove somefile from the list.
python3 timemachine.py list should print a list of the files being observed. “

Our implementation is based on argparse module : 

-l, --list            list the files being observed from the configuration
                        file specified
  -a ADD, --add ADD     add a file to the list of files being observed. The
                        filename may contain the absolute path
  -r REMOVE, --remove REMOVE
                        remove a file to the list of files being observed. The
                        filename may contain the absolute path

Note a user can start using the script without creating manually the configfile.
The scripts alerts if the configfile is empty. 
Example 

admin@COM-C132-VABC ~ $ rm config.dat 
admin@COM-C132-VABC ~ $ /usr/bin/python3 /home/admin/PycharmProjects/Assignment2/timemachine.py -c config.dat -cl /home/admin -d /home/admin/Backup 
...........Timemachine started...........
Configuration file is empty, please add files


The user can add file, list and remove:

example
admin@COM-C132-VABC ~ $ /usr/bin/python3 /home/admin/PycharmProjects/Assignment2/timemachine.py -c config.dat -cl /home/admin -d /home/admin/Backup -a /home/admin/file1.txt

...........Timemachine started...........
Configuration file is empty, please add files
Config file is /home/admin/config.dat
History of files recorded in /home/admin/Backup/records_sent.dat
Destination of backups is /home/admin/Backup/
/home/admin/file1.txt was added to configfile /home/admin/config.dat

admin@COM-C132-VABC ~ $ /usr/bin/python3 /home/admin/PycharmProjects/Assignment2/timemachine.py -c config.dat -cl /home/admin -d /home/admin/Backup -a /home/admin/file2.txt
...........Timemachine started...........
Config file is /home/admin/config.dat
History of files recorded in /home/admin/Backup/records_sent.dat
Destination of backups is /home/admin/Backup/
/home/admin/file2.txt was added to configfile /home/admin/config.dat

admin@COM-C132-VABC ~ $ /usr/bin/python3 /home/admin/PycharmProjects/Assignment2/timemachine.py -c config.dat -cl /home/admin -d /home/admin/Backup -l
...........Timemachine started...........
Config file is /home/admin/config.dat
History of files recorded in /home/admin/Backup/records_sent.dat
Destination of backups is /home/admin/Backup/
The list of files being observed is
/home/admin/file1.txt
/home/admin/file2.txt


admin@COM-C132-VABC ~ $ /usr/bin/python3 /home/admin/PycharmProjects/Assignment2/timemachine.py -c config.dat -cl /home/admin -d /home/admin/Backup -r /home/admin/file2.txt
...........Timemachine started...........
Config file is /home/admin/config.dat
History of files recorded in /home/admin/Backup/records_sent.dat
Destination of backups is /home/admin/Backup/
/home/admin/file2.txt was removed from configfile /home/admin/config.dat


Note that -l takes precedence over -a and -a takes precedence over -r
	- example :if we have both argument in the command line only -l will run.


Note that user can remove all files from the configuration files
When the last file is removed, the script can still run, but it will ask to add files
example

admin@COM-C132-VABC ~ $ /usr/bin/python3 /home/admin/PycharmProjects/Assignment2/timemachine.py -c config.dat -cl /home/admin -d /home/admin/Backup 
...........Timemachine started...........
Configuration file is empty, please add files
Config file is /home/admin/config.dat
History of files recorded in /home/admin/Backup/records_sent.dat
Destination of backups is /home/admin/Backup/





---------chapter how to run Timemachine, check modifications and backup---------

here is an example how to test the script

decide which files to observe, here create your files you want to watch for, and we add a special case where we remove all permissions to file2.txt :

touch ~/file1.txt
touch ~/file2.txt
chmod 000 ~/file2.txt
touch ~/file3.txt

decide which folder to use for your backups, here we decide to use
/home/admin/timemachine/backup

decide which folder to use for your configuration file, here we decide to use
/home/admin/timemachine

decide which name to use for your configuration file, here we decide to use
myconfig.dat

admin@COM-C132-VABC ~ $ /usr/bin/python3 /home/admin/PycharmProjects/Assignment2/timemachine.py -d /home/admin/timemachine/backup -cl /home/admin/timemachine -c myconfig.dat
The folder /home/admin/timemachine/ was not found, timemachine must now exit

we create the folder /home/admin/timemachine/ and run again

admin@COM-C132-VABC ~ $ /usr/bin/python3 /home/admin/PycharmProjects/Assignment2/timemachine.py -d /home/admin/timemachine/backup -cl /home/admin/timemachine -c myconfig.dat
...........Timemachine started...........
Configuration file is empty, please add files
Config file is /home/admin/timemachine/myconfig.dat
History of files recorded in /home/admin/timemachine/backup/records_sent.dat
Destination of backups is /home/admin/timemachine/backup/


we have to add the files to the configuration file


admin@COM-C132-VABC ~ $ /usr/bin/python3 /home/admin/PycharmProjects/Assignment2/timemachine.py -d /home/admin/timemachine/backup -cl /home/admin/timemachine -c myconfig.dat -a file1.txt
...........Timemachine started...........
Configuration file is empty, please add files
Config file is /home/admin/timemachine/myconfig.dat
History of files recorded in /home/admin/timemachine/backup/records_sent.dat
Destination of backups is /home/admin/timemachine/backup/
file1.txt was added to configfile /home/admin/timemachine/myconfig.dat
admin@COM-C132-VABC ~ $ /usr/bin/python3 /home/admin/PycharmProjects/Assignment2/timemachine.py -d /home/admin/timemachine/backup -cl /home/admin/timemachine -c myconfig.dat -a file2.txt
...........Timemachine started...........
Config file is /home/admin/timemachine/myconfig.dat
History of files recorded in /home/admin/timemachine/backup/records_sent.dat
Destination of backups is /home/admin/timemachine/backup/
file2.txt was added to configfile /home/admin/timemachine/myconfig.dat
admin@COM-C132-VABC ~ $ /usr/bin/python3 /home/admin/PycharmProjects/Assignment2/timemachine.py -d /home/admin/timemachine/backup -cl /home/admin/timemachine -c myconfig.dat -a file3.txt
...........Timemachine started...........
Config file is /home/admin/timemachine/myconfig.dat
History of files recorded in /home/admin/timemachine/backup/records_sent.dat
Destination of backups is /home/admin/timemachine/backup/
file3.txt was added to configfile /home/admin/timemachine/myconfig.dat
admin@COM-C132-VABC ~ $ 

We can now list our files

admin@COM-C132-VABC ~ $ /usr/bin/python3 /home/admin/PycharmProjects/Assignment2/timemachine.py -d /home/admin/timemachine/backup -cl /home/admin/timemachine -c myconfig.dat -l
...........Timemachine started...........
Config file is /home/admin/timemachine/myconfig.dat
History of files recorded in /home/admin/timemachine/backup/records_sent.dat
Destination of backups is /home/admin/timemachine/backup/
The list of files being observed is
file1.txt
file2.txt
file3.txt



We run the script to run the first check and backup

admin@COM-C132-VABC ~ $ /usr/bin/python3 /home/admin/PycharmProjects/Assignment2/timemachine.py -d /home/admin/timemachine/backup -cl /home/admin/timemachine -c myconfig.dat
...........Timemachine started...........
Config file is /home/admin/timemachine/myconfig.dat
History of files recorded in /home/admin/timemachine/backup/records_sent.dat
Destination of backups is /home/admin/timemachine/backup/
we run 1st backup of file1.txt
The folder /home/admin/timemachine/backup/ was not found, timemachine must now exit


oups indeed we have not created the folder /home/admin/timemachine/backup/
let’s create it and run the script again

admin@COM-C132-VABC ~ $ mkdir  /home/admin/timemachine/backup/
admin@COM-C132-VABC ~ $ /usr/bin/python3 /home/admin/PycharmProjects/Assignment2/timemachine.py -d /home/admin/timemachine/backup -cl /home/admin/timemachine -c myconfig.dat
...........Timemachine started...........
Config file is /home/admin/timemachine/myconfig.dat
History of files recorded in /home/admin/timemachine/backup/records_sent.dat
Destination of backups is /home/admin/timemachine/backup/
we run 1st backup of file1.txt
file1.txt was copied to /home/admin/timemachine/backup/2017-11-26 22:55:25.174276file1.txt
Writing dates_recorded to /home/admin/timemachine/backup/records_sent.dat
file file2.txt cannot be accessed, error is (<class 'PermissionError'>, PermissionError(13, 'Permission denied'), <traceback object at 0x7f40c2c127c8>)
we run 1st backup of file3.txt
file3.txt was copied to /home/admin/timemachine/backup/2017-11-26 21:45:56.166167file3.txt
Writing dates_recorded to /home/admin/timemachine/backup/records_sent.dat


We can see that the backup worked ok for file1.txt and file3.txt


let’s correct the issue and run the script again

admin@COM-C132-VABC ~ $ chmod u+r file2.txt 

admin@COM-C132-VABC ~ $ /usr/bin/python3 /home/admin/PycharmProjects/Assignment2/timemachine.py -d /home/admin/timemachine/backup -cl /home/admin/timemachine -c myconfig.dat
...........Timemachine started...........
Config file is /home/admin/timemachine/myconfig.dat
History of files recorded in /home/admin/timemachine/backup/records_sent.dat
Destination of backups is /home/admin/timemachine/backup/
file1.txt has not been modified
we run 1st backup of file2.txt
file2.txt was copied to /home/admin/timemachine/backup/2017-11-26 21:45:56.166167file2.txt
Writing dates_recorded to /home/admin/timemachine/backup/records_sent.dat
file3.txt has not been modified

We cab see that backup of file2.txt works ok now.
Also the script explains that file1.txt and file2.txt have not been modified since then.

let’s change the modification dates of our files  and run the script again

admin@COM-C132-VABC ~ $ touch file*

admin@COM-C132-VABC ~ $ /usr/bin/python3 /home/admin/PycharmProjects/Assignment2/timemachine.py -d /home/admin/timemachine/backup -cl /home/admin/timemachine -c myconfig.dat
...........Timemachine started...........
Config file is /home/admin/timemachine/myconfig.dat
History of files recorded in /home/admin/timemachine/backup/records_sent.dat
Destination of backups is /home/admin/timemachine/backup/
file1.txt has been modified since last backup, we run new backup
file1.txt was copied to /home/admin/timemachine/backup/2017-11-26 23:34:23.234337file1.txt
Writing dates_recorded to /home/admin/timemachine/backup/records_sent.dat
file2.txt has been modified since last backup, we run new backup
file2.txt was copied to /home/admin/timemachine/backup/2017-11-26 23:34:23.234337file2.txt
Writing dates_recorded to /home/admin/timemachine/backup/records_sent.dat
file3.txt has been modified since last backup, we run new backup
file3.txt was copied to /home/admin/timemachine/backup/2017-11-26 23:34:23.234337file3.txt
Writing dates_recorded to /home/admin/timemachine/backup/records_sent.dat

Timemachine did backup all files correctly.

Let’s take a look at the log file :

admin@COM-C132-VABC ~ $ tail /home/admin/timemachine/timemachine.log 
2017-11-26 23:34:25,186 DEBUG    Destination of backups is /home/admin/timemachine/backup/
2017-11-26 23:34:25,187 DEBUG    file1.txt has been modified since last backup, we run new backup
2017-11-26 23:34:25,190 DEBUG    file1.txt was copied to /home/admin/timemachine/backup/2017-11-26 23:34:23.234337file1.txt
2017-11-26 23:34:25,190 DEBUG    Writing dates_recorded to /home/admin/timemachine/backup/records_sent.dat
2017-11-26 23:34:25,191 DEBUG    file2.txt has been modified since last backup, we run new backup
2017-11-26 23:34:25,194 DEBUG    file2.txt was copied to /home/admin/timemachine/backup/2017-11-26 23:34:23.234337file2.txt
2017-11-26 23:34:25,195 DEBUG    Writing dates_recorded to /home/admin/timemachine/backup/records_sent.dat
2017-11-26 23:34:25,196 DEBUG    file3.txt has been modified since last backup, we run new backup
2017-11-26 23:34:25,199 DEBUG    file3.txt was copied to /home/admin/timemachine/backup/2017-11-26 23:34:23.234337file3.txt
2017-11-26 23:34:25,200 DEBUG    Writing dates_recorded to /home/admin/timemachine/backup/records_sent.dat
admin@COM-C132-VABC ~ $ 

we can grep for errors in the log file

admin@COM-C132-VABC ~ $ grep -i error /home/admin/timemachine/timemachine.log 
2017-11-26 23:17:53,544 ERROR    Configuration file is empty, please add files
2017-11-26 23:19:12,818 ERROR    Configuration file is empty, please add files
2017-11-26 23:19:51,219 ERROR    file file1.text not found
2017-11-26 23:19:51,219 ERROR    file file2.text not found
2017-11-26 23:19:51,219 ERROR    file file3.text not found
2017-11-26 23:20:20,272 ERROR    Configuration file is empty, please add files
2017-11-26 23:20:35,932 ERROR    file1.text is already in configfile /home/admin/timemachine/myconfig.dat
2017-11-26 23:21:02,215 ERROR    file file1.text not found
2017-11-26 23:21:02,215 ERROR    file file2.text not found
2017-11-26 23:21:02,215 ERROR    file file3.text not found
2017-11-26 23:24:40,298 ERROR    file file1.text not found
2017-11-26 23:24:40,298 ERROR    file file2.text not found
2017-11-26 23:24:40,298 ERROR    file file3.text not found
2017-11-26 23:27:12,879 ERROR    Configuration file is empty, please add files
2017-11-26 23:27:21,562 ERROR    Configuration file is empty, please add files
2017-11-26 23:28:06,893 ERROR    The folder /home/admin/timemachine/backup/ was not found, timemachine must now exit
2017-11-26 23:29:17,656 ERROR    file file2.txt cannot be accessed, error is (<class 'PermissionError'>, PermissionError(13, 'Permission denied'), <traceback object at 0x7f40c2c127c8>)


let’s verify our config file 
admin@COM-C132-VABC ~ $ cat /home/admin/timemachine/myconfig.dat 
- file1.txt
- file2.txt
- file3.txt

The config file appears as expected

let’s verify our backups and records_sent.dat

admin@COM-C132-VABC ~ $ ll /home/admin/timemachine/backup/
total 12
drwxr-xr-x 2 admin admin 4096 Nov 26 23:34 .
drwxr-xr-x 3 admin admin 4096 Nov 26 23:29 ..
-r-------- 1 admin admin    0 Nov 26 23:32 2017-11-26 21:45:56.166167file2.txt
-rw-r--r-- 1 admin admin    0 Nov 26 23:29 2017-11-26 21:45:56.166167file3.txt
-rw-r--r-- 1 admin admin    0 Nov 26 23:29 2017-11-26 22:55:25.174276file1.txt
-rw-r--r-- 1 admin admin    0 Nov 26 23:34 2017-11-26 23:34:23.234337file1.txt
-r-------- 1 admin admin    0 Nov 26 23:34 2017-11-26 23:34:23.234337file2.txt
-rw-r--r-- 1 admin admin    0 Nov 26 23:34 2017-11-26 23:34:23.234337file3.txt
-rw-r--r-- 1 admin admin   83 Nov 26 23:34 records_sent.dat

All Files with different modification dates have been correctly copied.
Note the file size is 0, as the original file size is 0 also.










