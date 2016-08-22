'''
NAME
    rebuild_relink_retest.py

SYNOPSIS

    import rebuild_relink_retest

    main(application,version,build,log,stdoutflag,action,debug)

DESCRIPTION


HISTORY

    2009.0313/tpb added arg build_path to main() so we can pass in the
                  list of builds to work on. If the list is empty, we
                  call make_build_list() to get the list. This allows
                  swdriver to pass us a list of duplicate builds, so
                  don't repeat operations on the originals. Also added
                  dryrun option.

'''
'''

                   Copyright (c) 2010, UT-Battelle, LLC

                          All rights reserved

                          SWTools, Version 1.0

                          OPEN SOURCE LICENSE

Subject to the conditions of this License, UT-Battelle, LLC (the "Licensor") 
hereby grants, free of charge, to any person (the "Licensee") obtaining a 
copy of this software and associated documentation files (the "Software"), 
a perpetual, worldwide, non-exclusive, no-charge, royalty-free, irrevocable 
copyright license to use, copy, modify, merge, publish, distribute, and/or 
sublicense copies of the Software.

1. Redistributions of Software must retain the above open source license 
grant, copyright and license notices, this list of conditions, and the 
disclaimer listed below.  Changes or modifications to, or derivative 
works of the Software must be noted with comments and the contributor 
and organization's name.  If the Software is protected by a proprietary 
trademark owned by Licensor or the Department of Energy, then derivative 
works of the Software may not be distributed using the trademark without 
the prior written approval of the trademark owner. 

2. Neither the names of Licensor nor the Department of Energy may be used 
to endorse or promote products derived from this Software without their 
specific prior written permission.

3. The Software, with or without modification, must include the following 
acknowledgment:

"This product includes software produced by UT-Battelle, LLC under Contract 
No. DE-AC05-00OR22725 with the Department of Energy."

4. Licensee agrees to unconditionally assign to Licensor all rights in 
any changes or modifications to, or derivative works of the Software.  
Licensee agrees to furnish the Licensor within a reasonable time a copy 
of any changes or modifications to, or derivative works of the Software 
according to the instructions found on the following web site:


                     http://www.nccs.gov/user-support/swtools

********************************************************************************
                               DISCLAIMER

UT-BATTELLE, LLC AND THE GOVERNMENT MAKE NO REPRESENTATIONS AND DISCLAIM ALL
WARRANTIES, BOTH EXPRESSED AND IMPLIED.  THERE ARE NO EXPRESS OR IMPLIED 
WARRANTIES OF MERCHANTABILITY OR FITNESS FOR A PARTICULAR PURPOSE, OR THAT 
THE USE OF THE SOFTWARE WILL NOT INFRINGE ANY PATENT, COPYRIGHT, TRADEMARK, 
OR OTHER PROPRIETARY RIGHTS, OR THAT THE SOFTWARE WILL ACCOMPLISH THE INTENDED 
RESULTS OR THAT THE SOFTWARE OR ITS USE WILL NOT RESULT IN INJURY OR DAMAGE.  
THE USER ASSUMES RESPONSIBILITY FOR ALL LIABILITIES, PENALTIES, FINES, CLAIMS, 
CAUSES OF ACTION, AND COSTS AND EXPENSES, CAUSED BY, RESULTING FROM OR ARISING 
OUT OF, IN WHOLE OR IN PART THE USE, STORAGE OR DISPOSAL OF THE SOFTWARE.

********************************************************************************
'''

from swadm import *
from config import *

import parse
import glob
import os
import datetime
import sys
import getpass
import subprocess


def main(application,version,build,build_path,
         log,stdoutflag,action,debug,resume, dryrun=False):
    
    old_umask = os.umask(int(get_umask(),8))

    # If logging is enabled, use the Tee class to copy stdout to log

    if log :
        log_object = Tee(log_directory()+"/"+action+"/"+getarch()+"_"+machinename()+"_"+datetime.date.today().isoformat()+"_"+getpass.getuser(),"a")
        file.write("---------------------------------------------------------------------------------")

    if resume != None:
        resumefile = open(resume)
        resumetext = resumefile.readlines()
        resumefile.close()

    if build_path == []:
        build_path = make_build_list(application, version, build)

    if dryrun:
        print "%s dryrun: would operate on the following builds:" % action
        for build in build_path:
            print "   %s" % build
        return
        
#    print build_path

    # Work with the environment variables

    if action == "retest":

        # check if SW_WORKDIR set, if so use it 
        try:
           environment_variable_path = os.environ[get_work_environment()]
        # otherwise use WORKDIR
        except:
#mrf:begin
#           error("%s not defined" % get_work_environment())
          try:
             print "SW_WORKDIR not defined, using WORKDIR instead"
             environment_variable_path = os.environ['WORKDIR']
          except:
             error("SW_WORKDIR and WORKDIR not defined")
#mrf:end

        if not os.path.isdir(environment_variable_path):
            error("%s:%s does not exist" % (get_work_environment(),environment_variable_path) )           
        
    # Decide which script we're going to call

    for currentbuild in build_path:

        appname = currentbuild.split("/")
        time = datetime.datetime.today().isoformat()
    
        if action == "retest":
            try:
                if not os.path.isdir(environment_variable_path+"/"+action):
                    os.mkdir(environment_variable_path+"/"+action)
                if not os.path.isdir(environment_variable_path+"/"+action+"/"+time):
                    os.mkdir(environment_variable_path+"/"+action+"/"+time)
                
                os.mkdir(environment_variable_path+"/"+action+"/"+time+"/"+appname[-3]+"_"+appname[-2]+"_"+appname[-1])
         
            except:
                error("could not create %s" % (environment_variable_path+"/"+action+"/"+time+"/"+appname[-3]+"_"+appname[-2]+"_"+appname[-1]) )

            os.environ[get_work_environment()] = (environment_variable_path+"/"+action+"/"+time+"/"+appname[-3]+"_"+appname[-2]+"_"+appname[-1])
            
        if action == "rebuild":
            destination_path = currentbuild+"/rebuild"
        elif action == "relink":
            destination_path = currentbuild+"/relink"
        elif action == "retest":
            destination_path = currentbuild+"/retest"

        # Call the script

        if os.path.isfile(destination_path):
           
            if (not os.path.isfile(currentbuild+"/.lock")) & (not os.path.isfile(currentbuild+"/.running")):
                file = open(currentbuild+"/.lock","w")
                file.close()
            elif resume != None:
                if os.path.isfile(currentbuild+"/.lock"):
                    os.remove(currentbuild+"/.lock")
            else:
                if os.path.isfile(currentbuild+"/.lock"):
                    error( currentbuild + " is locked. If you know that no one else is using the application, you can delete "+currentbuild +"/.lock" ,False)
                
                if os.path.isfile(currentbuild+"/.running"):
                    error("%s has a job in the batch queue. If you know that this is not the case, you can delete %s/.running" % (currentbuild,currentbuild),False)
                    
                if action == "retest":
                    os.environ[get_work_environment()]= environment_variable_path 
                    os.system("rm -rf " + environment_variable_path+"/"+action+"/"+time)
           
                continue
       

            resumeflag = False
            if resume != None:
                for line in resumetext:
                    if destination_path in line:
                        resumeflag = True
                        break

                if resumeflag == True:
                    print "Skipping %s" % destination_path
                    if os.path.isfile(currentbuild+"./lock"):
                        os.remove(currentbuild+"/.lock")        
                    if action == "retest":
                        os.environ[get_work_environment()]= environment_variable_path 
                        os.system("rm -rf " + environment_variable_path+"/"+action+"/"+time)
                   
                    continue
               
       
            try:
                if stdoutflag:
                    return_value = subprocess.call("env SW_BLDDIR=" + currentbuild + " " + destination_path , shell=True)
                else:
                    return_value = subprocess.call("env SW_BLDDIR=" + currentbuild + " " + destination_path + " > /dev/null 2>&1" , shell=True)
            
                os.remove(currentbuild+"/.lock")
                    
            except KeyboardInterrupt:
                print error("Keyboard Interrupt")
            
            return_message(destination_path,return_value)
            
            
        else:
            if controlled(currentbuild.rsplit("/",1)[0]) or controlled(currentbuild.rsplit("/",2)[0]):
                error("%s is controlled" % destination_path,False)
            else:
                error("%s does not exist" % destination_path,False)
            continue 
            
   
        if action == "retest":
            os.environ[get_work_environment()]= environment_variable_path 
          
        if (action == "retest") & (return_value != 2):
            os.system("rm -rf " + environment_variable_path+"/"+action+"/"+time)
        # chmod the files. Throw away the outout because this will fail if the script is run by someone who
        # doesn't own the files. Thats OK. We mainly want to make sure that the all of the newly created files
        # are world readable/writeable
        os.system("chmod -R ug+w,a+rX " +currentbuild +" > /dev/null 2>&1")
        # changing this to :install, was :ccsstaff - 03-16-2011 Scott S.
        os.system("chown -R :install " +currentbuild +" > /dev/null 2>&1")

       
    # Restore the umask to the previous umask (before the script was run)
    os.umask(old_umask)
        
