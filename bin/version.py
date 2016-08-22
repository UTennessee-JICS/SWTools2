'''
NAME
    version.py

SYNOPSIS
    swversion -a APP [-d days] [--debug]

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
import datetime
import glob
import time
import smtplib

def main(architecture,application,wait,action,debug):

    # Get today's date, and the future date that is "wait" days away
    
    today = datetime.date.today()
    days = today + datetime.timedelta(int(wait))
  
    # Build the applications path

    application_path = []

    for path in glob.glob(software_root()+"/"+architecture+"/"+application):
        application_path.append(path)
                                
    for exception in application_exceptions():
        for app in application_path:
            if exception == app.rsplit("/",1)[1] :
                application_path.remove(app)
        
   
    # Traverse the application list

    for current_application_path in application_path:

        # currentapplication is the end of the application_path
        
        currentapplication = current_application_path
        
        if not os.path.isdir(current_application_path):
            error("No applications match your criteria")
                        
        # Try to open the file in append mode
        
        try:
            file = open(current_application_path+"/.check4newver","a")
        except:
            error("%s/.check4newver: error opening file" \
                  % current_application_path)

    
        # Switch based on the action

        if action == "installed":
            msg = "%s: new version of %s installed \n%s: next check on %s\n" \
                  % (today,currentapplication,today,days)
            outplex(msg, [file, sys.stdout])
            
        elif action == "none":
            msg = \
                "%s: no new version of %s available\n%s: next check on %s\n" \
                % (today,currentapplication,today,days)
            outplex(msg, [file, sys.stdout])
            
        elif action == "conform":
            # Close .check4newver
            file.close()
            
            # Open it again, this time not in append mode
            file = open(current_application_path+"/.check4newver")
            
            # Try to read the last line of the file
            try:
                lastline = file.readlines()[-1]
            except:
                print " error: %s is empty" \
                      % (current_application_path+"/.check4newver")
                file.close()
                continue
            
            file.close()
        
            # If the last line doesn't contain a date, then this is an
            # "email sent to" line in this case we send email again, but
            # don't keep writing it to the file. We set the duedate to
            # year 1-1-1
        
            if "next check on" in lastline: 
                duedate = lastline.split()[-1]
                duedate = datetime.date(*time.strptime(duedate,"%Y-%m-%d")[0:3])
            else:
                duedate = datetime.date(1,1,1)
        
            # if the app is out of date we send email

            print "Conformance checking " + currentapplication
       
            if(today > duedate): 
                
                # Open the owners file and look for usernames
 
                names = []               
#                try:
#                    file = open(current_application_path+"/.owners")
#                except:
#                    print "  error: %s does not exist" % (current_application_path+"/.owners")
#                    continue
#                
#                try:
#                    names = file.readlines()
#                except:
#                    print "  error: %s is empty" % (current_application_path+"/.owners")
#                    file.close()
#                    continue
           
                # Open .check4newver again, this time in append mode
                
                file = open(current_application_path+"/.check4newver","a")
                msg = "%s: Due date to check for new version has passed\n" \
                      % (today)
                if "next check on" in lastline:
                    file.write(msg)
                print "\t%s" % msg

# mrf:
# inserted logic here to find all the owners for all versions and 
# builds and put them in the names list            

                vers = glob.glob(current_application_path+"/*")
                vernames=[]
                for ver in vers:
                  shortver = ver.split('/')
#                  print "shortver", shortver[4]
                  if notverdirs(current_application_path,shortver[4]):
                    continue
                  if os.path.isdir(ver):
                    builds = glob.glob(ver+'/*')
                    for build in builds:
                      if os.path.isdir(build):
                        try:
                          bofile = open(build+"/.owners")
                        except:
                          print "  error: %s does not exist" % (build+"/.owners")
                          continue
                        try:
                          bldnames = bofile.readlines()
                          bofile.close()
                          for bldname in bldnames:
                            try:
                              i=vernames.index(bldname)
                            except:
                              try:
                                i=names.index(bldname)
                              except:
                                vernames.append(bldname)
                        except:
                          print "  error: %s is empty" % (build+"/.owners")
#                    print "vernames",vernames
                    names.extend(vernames)
#                print "names",names

# mrf:
           
                # Send email to the owners
           
                for name in names:

                    # Build up the message
                    
                    name = name.strip()
                    name = name+"@mail.ccs.ornl.gov"
                    to = "To: " + name  + "\n"
                    fromfield = "From: " + from_field() + "\n"
                    subject = "Subject: Check for " + currentapplication \
                              + " updates\n"
                    body = "According to our records, it is time to" \
                           + " check for a " + currentapplication + " update "
                    
                    # Make the message a single string
                    msg = to+fromfield+subject+body
            

                    # Send the message using smtplib
                    # This assumes you have a local smtp server; If you don't, you will need to modufy this
                   
#                    server = smtplib.SMTP("localhost")
                    server = smtplib.SMTP("mail.ccs.ornl.gov")
                    server.sendmail(from_field(),name,msg)
                    server.quit()

                    msg = "%s: Email sent to : %s \n" % (today,name)
                    if "next check on" in lastline:
                        file.write(msg)
                    print "\t%s" % msg
                    days = today + datetime.timedelta(30)
                    file.write("%s: next check on %s on %s\n" \
                               % (today,currentapplication,days))
                
                file.close()
            else:
                print "Has not been 90 days since notification. Notfication will occur on or after %s" % duedate

            
        elif action == "set":
            msg = "%s: next check on %s on %s\n" \
                  % (today,currentapplication,days)
            outplex(msg, [file, sys.stdout])
            
        else:
            error( "%s : invalid action" % action)

        file.close()
