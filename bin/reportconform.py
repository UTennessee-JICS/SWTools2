'''
NAME
    reportconform.py

SYNOPSIS

    import reportconform

DESCRIPTION
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

import glob
import subprocess
import sys
import datetime
import time
import StringIO
import smtplib



def main(architecture,application,version,build,recurse,long):

    # Architecture defaults to *; we also support all
    
    if (architecture != "*") & (architecture != "all") :
        architectures = glob.glob(software_root()+"/"+architecture)

        if architectures == []:
            error("invalid architecture")
            
    else:
        # Otherwise, use the architectures that are defined in sw_config
        architectures = []
        for currentarchitecture in valid_architectures():
            archpath = glob.glob(software_root()+"/"+currentarchitecture)
            if archpath != []:
                architectures.append(archpath[0])
            else:
                error("invalid architectures defined in sw_config")

    # Print architectures

    for currentarchitecture in architectures:
        
        # See if the defined archtitecture is a valid directory
        
        if os.path.isdir(currentarchitecture):
            print "/"+currentarchitecture.split("/")[-1] + check_dir_permissions(currentarchitecture)

        # Get  applications
        
        applications = glob.glob(currentarchitecture +"/"+application)
        
        # Remove Exceptions
        
        exceptions = application_exceptions()
        
        for exception in exceptions:
            if (currentarchitecture+"/"+exception) in applications:
                applications.remove(currentarchitecture+"/"+exception)
       
        applications.sort()
       
        # Print Applications
       
        for currentapplication in applications:
          
            apperr = False
            
            perms = check_dir_permissions(currentapplication)

            if perms != "":
                apperr = True

            # See if it is a directory, and look for matching modulefiles folder
            

            try:
                supportfile = open(currentapplication+"/support")
                supportstatus = supportfile.readlines()[0].strip("\n")
                supportfile.close()
            except:
                supportstatus = "support file cannot be read"
                
            
            if os.path.isdir(currentapplication):
                print "        /"+currentapplication.split("/")[-1] \
                      + " (support status: " + supportstatus \
                      + ")" + check_dir_permissions(currentapplication)
                if module_folder_missing(currentapplication, supportstatus):
                    print "            no modulefiles folder" 
                    apperr = True 

                ood = out_of_date(currentapplication, supportstatus)
                # If apperr was already True and out of date is False,
                # we don't want to change apperr
                if ood:
                    apperr = True

#                 # Open check4newver

#                 try:
#                     file = open(currentapplication+"/.check4newver")
#                     lastline = file.readlines()[-1]
#                     file.close()
#                 except:
#                     print "error: %s is empty or cannot be read" % (currentapplication+"/.check4newver")
#                     lastline = ""
#                     apperr = True

#                 # See if is is out of date

#                 if "next check" in lastline:
#                     duedate = lastline.split()[-1]
#                     duedate = datetime.date(*time.strptime(duedate,"%Y-%m-%d")[0:3])
#                 else:
#                     print '           .check4newver: no "next check" in last line'
#                     duedate = datetime.date(3000,1,1)
#                     apperr = True
                    
#                 if (datetime.date.today() > duedate):
#                     print "           this software is out of date"
#                     apperr = True
                
                # Look for missing files

                files = application_required_files()
                
                for file in files:
                    if not os.path.isfile(currentapplication+"/"+file):
                        print "           %s is missing" % file
                        apperr = True
                    else:
                        myfile = open(currentapplication+"/"+file)
                        lines = myfile.readlines()
                        if lines == []:
                            print "            %s is empty" % file
                            apperr = True
                   
                        perms = check_dir_permissions(currentapplication+"/"+file)
                     
                        if perms != "" :
                            print "           " + file + perms
                            apperr = True
                
                # Make sure the templates have been modified
                rval = subprocess.call("diff " + currentapplication +"/description" +" "+ template_directory()+"description.template > /dev/null 2>&1" , shell=True)
                if rval == 0:
                    print "           description is unchanged from the template"
                    apperr = True
        
            # Print versions
        
            versions = glob.glob(currentapplication+"/"+version)
       
            for currentversion in versions:
#mrf:start
                # check if .notverdirs file exists and if so
                # skip all directory names it contains
                shortver = currentversion.split('/')
                if notverdirs(currentapplication,shortver[4]):
                     continue
#mrf:end

                vererr = False
                if long:
                    stdoutver = sys.stdout
                    sys.stdout = StringIO.StringIO()
               
                perms = check_dir_permissions(currentversion)
                if perms != "":
                    vererr= True
                    #print "vererr1"
                if os.path.isdir(currentversion):
                    print "                /" + currentversion.split("/")[-1] + perms 
               
                    if module_file_missing(currentapplication,
                                           currentversion,
                                           supportstatus):
                        print "                      " \
                              + "version does not have modulefile" 
                        vererr = True
                       # print "vererr2"
                # Print builds
                else:
                    if perms != "":
                        print "           " + currentversion.split("/")[-1] + perms
                        vererr=True

                builds = glob.glob(currentversion+"/"+build)
               
                for currentbuild in builds:
                    if not os.path.isdir(currentbuild):
                        builds.remove(currentbuild)
               
                for currentbuild in builds:

#mrf:start
                    # check if .notbuilddirs file exists and if so
                    # skip all directory names it contains
                    shortbuild = currentbuild.split('/')
                    if notbuilddirs(currentversion,shortbuild[5]):
                         continue
#mrf:end
                    builderr = False
                    
                    if long:
                        stdoutbuild = sys.stdout
                        sys.stdout = StringIO.StringIO()
                
                    perms = check_dir_permissions(currentbuild)

                    if perms != "":
                        builderr = True
                        
                    if "is missing either gX or oX" in perms:
                        print "                            " + perms
               
                    if os.path.isdir(currentbuild):
                        try:
                            ownerfile = open(currentbuild+"/.owners")
                            owner = ownerfile.readlines()[0].strip("\n")
                            ownerfile.close()
                        except:
                            owner = ""
                            print "                            can't open ownerfile"
                            builderr = True
                        print "                            /" + currentbuild.split("/")[-1] + " (owner: " + owner + ")" + perms
                                            
                        files = glob.glob(currentbuild+"/*")

                        for file in files:
                            if check_permissions(file,"                                ") == True:
                                builderr = True
                        files = build_required_files() 
                    
                        if os.path.isfile(currentbuild+"/.lock"):
                            print "                                Lockfile present"  
                            builderr = True
                            
                        for file in files:
                            if not os.path.isfile(currentbuild+"/"+file):
                                print "                                %s is missing" % file
                                builderr = True
                                
                        for file in ["rebuild","relink","retest"]:
                            if os.path.isfile(currentbuild+"/"+file):
                                try:
                                    myfile = open(currentbuild+"/"+file)
                                except:
                                    print "                                %s could not be opened" % file
                                    builderr = True
                                    continue
                        
                                lines = myfile.readlines()
                                myfile.close()
                        
                            for line in lines:
                                if "#" not in line:
                                    if "exit 3" in line:
                                        print "                                %s contains an exit 3" % (file)
                                        builderr = True
                        if recurse:
                           
                            now = datetime.date.today().isoformat()
                            
                            stdout = sys.stdout
                            sys.stdout = StringIO.StringIO()
                            os.path.walk(currentbuild, callback,currentbuild)
                            lines = sys.stdout.getvalue()
                            sys.stdout = stdout
                            
                            for line in lines:
                                if ("not gR" in line) or ("not gW" in line) or ("not oR" in line) or ("oW" in line):
                                    builderr = True
                                    for line in lines:
                                        print line,
                                    break
                   
                    else:
                        if perms != "":
                            print "                             " + currentbuild.split("/")[-1] + perms
                            builderr = True
                    if long:
                        buildtext = sys.stdout.getvalue() 
                        sys.stdout = stdoutbuild

                        if builderr:
                            print buildtext,
                            vererr = True
                            #print "SENDING MAIL"
                            #name = "fm9@ornl.gov"
                            #to = "To: fm9@ornl.gov\r\n"
                            #fromfield = "From: swadm@ornl.gov\r\n"
                            name = "mfahey@utk.edu"
                            to = "To: mfahey@utk.edu\r\n"
                            fromfield = "From: swadm@nics.utk.edu\r\n"
                            subject = "Subject: Problem with " + currentbuild + "\r\n\r\n"
                            body = buildtext
                            # Make the message a single string
                            msg = to+fromfield+subject+body

                            msg = msg.replace("                            ","")
                            # Send the message using smtplib

                            # This assumes you have a local smtp server; If you don't, you will need to modufy this
                            #server = smtplib.SMTP("localhost")
                            #server = smtplib.SMTP("mail.ccs.ornl.gov")
                            server = smtplib.SMTP("localhost")
                            #server.sendmail("swadm@ornl.gov","fm9@ornl.gov",msg)
                            server.quit()

                if long:
                    vertext = sys.stdout.getvalue() 
                    sys.stdout = stdoutver
                    if vererr:
                        print vertext, 

# ---------------------------------------------------------------------------
def out_of_date(currentapplication, supportstatus):

    # Apps with only 'vendor' support cannot get out of date
    
    if re.match(r'^\s*vendor\s*$', supportstatus):
        return False
    
    # Open check4newver

    try:
        file = open(currentapplication+"/.check4newver")
        lastline = file.readlines()[-1]
        file.close()
    except:
        print "error: %s is empty or cannot be read" % (currentapplication+"/.check4newver")
        lastline = ""
        apperr = True

    # See if is is out of date
        
    if "next check" in lastline:
        try:
            duedate = lastline.split()[-1]
            duedate = datetime.date(*time.strptime(duedate,"%Y-%m-%d")[0:3])
        except ValueError:
            print 'failure on application %s' % currentapplication
            print 'bad date (%s) in .check4newver needs to be fixed' % duedate
            sys.exit(1)
    else:
        print '           .check4newver: no "next check" in last line'
        duedate = datetime.date(3000,1,1)
        apperr = True
        
    if (datetime.date.today() > duedate):
        print "           this software is out of date"
        apperr = True
                
