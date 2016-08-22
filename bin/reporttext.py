'''

NAME
    report.py

SYNOPSIS

    import report
    report.main(action,

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

def main(architecture,application,version,build,recurse,long,diff):

    if diff != None:
        file = open(diff)
        text = file.readlines()
        file.close()
        print "New text: "                                                        
    
    # Architecture defaults to *; we also support all
    
    if (architecture != "*") & (architecture != "all") :
        architectures = glob.glob(software_root()+"/"+architecture)
    else:
        architectures = []
        for currentarchitecture in valid_architectures():
            architectures.append(software_root()+"/"+currentarchitecture)
        
    # Print architecures
    
    architectures.sort()

    for currentarchitecture in architectures:
        
        if os.path.isdir(currentarchitecture):
            archtext = currentarchitecture.split("/")[-1].ljust(15)
                
        # Print applications
        
        applications = glob.glob(currentarchitecture +"/"+application)
        
        exceptions = application_exceptions()
        
        for exception in exceptions:
            if (currentarchitecture+"/"+exception) in applications:
                applications.remove(currentarchitecture+"/"+exception)
        
        applications.sort()
        
        longest_app_length = 0
        
        for currentapplication in applications:
            
            if len(currentapplication) > longest_app_length :
                longest_app_length = len(currentapplication)
            
            if os.path.isdir(currentapplication):
                apptext = archtext+currentapplication.split("/")[-1].ljust(20)
#mrf
            descfile = open(currentapplication+"/description","r")
            desctext = descfile.readlines()
            descfile.close()
            for line in desctext:
              if "Category" in line:
                cats = (line.split(":")[1]).lstrip(" ").strip("\n").ljust(40)
#mrf
            # Print versions

            versions = glob.glob(currentapplication+"/"+version)
       
            versions.sort()
            atleastonever = 0
       
            for currentversion in versions:

                if os.path.isdir(currentversion):
                    vertext =  apptext+currentversion.split("/")[-1].ljust(15)
                    atleastonever = 1
                
                # Print builds
                
                builds = glob.glob(currentversion+"/"+build)
               
                builds.sort()
                atleastonebuild = 0
              
                for currentbuild in builds:

                    if os.path.isdir(currentbuild):
                        atleastonebuild = 1

                        try:
                            file = open(currentbuild+"/status")
                            status = file.readlines()[0].strip("\n")
                            file.close()
                        except:
                            if (controlled(currentapplication) != False) or (controlled(currentversion) != False):
                                status = "controlled"
                            else:
                                status = "file unreadable"
                        
                        
                        try:
                            file = open(currentbuild+"/.owners")
                            owner = file.readlines()[0].strip("\n")
                            file.close()
                        except:
                             
                            if (controlled(currentapplication) != False) or (controlled(currentversion) != False):
                                owner = "controlled"
                            else:
                                owner = "file unreadable"
                       
                        
                        if diff != None:
                            line =  vertext+cats+currentbuild.split("/")[-1].ljust(40) + status.ljust(20) + owner.ljust(15)
                        
                            if line+"\n" not in text:
                                print line
                            else:
                                text.remove(line+"\n")
                            
                        else:
                            print vertext+cats+currentbuild.split("/")[-1].ljust(40) + status.ljust(20) + owner.ljust(15)
            if atleastonever == 0:
               print apptext+"               "+cats
            if atleastonever == 1:
              if atleastonebuild == 0:
                print vertext+cats

    if diff!= None: 
        print "Text in old report not in new report: "
        for line in text:
            print line,
