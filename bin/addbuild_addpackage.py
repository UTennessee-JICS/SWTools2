'''
NAME
    addbuild_addpackage.py

SYNOPSIS

    import addbuild_addpackage

    addbuild_addpackage(application,version,build,log,action,debug)

DESCRIPTION

    This module implements the addpackage and addbuild functions of the NCCS'
    software tools package. This module will create a package or build directory
    and place the appropriate template files in that directory.

HISTORY

    Contact nai@ornl.gov or swadm@ornl.gov for questions or to report a bug.

    Implemented by Nick Jones, January 2008

    2/13/2008 - Rewrite and comments update
    3/27/2008 - Implemented exceptions and additional commenting
    2009-03-20/tpb - calls to no_wildcards() requires two args now so it
                     can tell the user which field contains the error
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

import os 
import shutil
import getpass
import datetime

def main(architecture,application,version,build,action,debug):

    # Set the application path
    
    # We don't support wildcards here, (we might end up with 100's of new dirs)
    # Since we don't support wildcards, we're not using the glob module
    
    application_path = software_root() \
                       + "/" + architecture \
                       + "/" + no_wildcards(application, 'application')

    if vendor(application_path) & (action == "addbuild"):
       error("cannot perform an addbuild on a package with a vendor exception at the application level")
   
    if action == "addbuild":

        # Make sure that the application directory already exists
        
        if not os.path.isdir(application_path):
            error("%s (application directory) does not exist" % application_path)
        
        # If version is a "tag" then get_versions will return the correct version from the version file
        # If it is not a "tag" then if will merely return the path to that directory
       
        version_path = get_versions(application_path,version)
        
        # Make sure that the version directory exists
        
        if not os.path.isdir(version_path):
            error("%s (version directory) does not exist" % version_path)
      
        # Set the build path
      
        build_path = os.path.join(version_path, build)
      
        # Try to create the build directory
        
        try:
            os.mkdir(build_path)
        except:
            error("Cannot create build directory")
    
        # Set the proper permissions on the build dir. Read the octal permissions string from the config file
        
        os.chmod(build_path, int(builddir_perms(), 8))
    
        # These are the files that will be copied when an addbuild is performed
        
        file_permission_pairs  = addbuild_templates()
        destination_path = build_path
        
        # Make the owner file
    
        make_owner_file(destination_path)
        print "creating %s/.owners" % destination_path
        
        template_dir = template_directory()
    
    elif action == "addpackage":
        
        # Try to create the application directory
        
        if os.path.exists(application_path) \
           and os.path.isdir(application_path):
            print "%s already exists" % application_path
            return
            
        try:
            os.mkdir(application_path)
        except:
            error("Cannot create %s" % application_path)

        os.chmod(application_path,int(appdir_perms(),8))

        # These are the files that will be copied when an addpackage is performed
        
        file_permission_pairs = addpackage_templates()
        destination_path = application_path
        
        # Create .check4newver

        make_check4newver_file(application_path)
        
        today = datetime.date.today()
        days_until_check = today + datetime.timedelta(int(90))
        print "creating %s" % (application_path+"/.check4newver")
        print "\t%s: new version installed\n\t%s: next check of %s on %s\n" % (today,today,application_path,days_until_check)
        
        template_dir = os.path.join(template_directory(), '..')
        
    # Copy the files

    for (file, permission) in file_permission_pairs:
        source = os.path.join(template_dir, file)
        target = os.path.join(destination_path, file)
        try:
            shutil.copy(source, target)
        except:
            error("could not create %s . Check the template directory" % (destination_path+"/"+file))
        
        print "creating %s" % (target)
     
        # Double check the permissions
        
        try:
            os.chmod(target, int(permission, 8))
        except:
            error("%s%s%s has invalid permission string (%s) or does not exist. \
                   Check the directory and config." % (target, permission))
    
    print "  %s successful." % action
