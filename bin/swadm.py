'''
swadm.py

These are helper functions that are used throughtout swtools. 

Unfortunately, since they are all used quite extensively, I cannot
organize them in any meaningful way other than alphabetization. Read
comments to get an idea of what each function does.

HISTORY

    2009-03-13 - added routines make_build_list(), make_dup_list()
                 added field name to no_wildcards()
                 moved machinename() to config.py

'''
''''
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

import datetime
import getpass
import glob
import os
import platform
import re
import socket
import sys
import stat
import string

from config import *

def callback(arg, directory, files):

    '''
    This is used by report conform to do recursive permissions checks in conjunction with os.walk
    ''' 
    
    if directory != arg:
    
        cleandirectory = directory.replace(arg,"")
        spacing = ""

        for i in range(0,string.count(cleandirectory,"/") ):
            spacing = spacing + "    "

        print "                " + spacing +"/"+ cleandirectory.rsplit("/",1)[1]

        for file in files:
                check_permissions(directory+"/"+file, "                  "  + spacing)

def check_dir_permissions(path,space=""):
    '''
    This checks for group write, group read, and other read
    '''

    try:
        mode = stat.S_IMODE(os.stat(path)[stat.ST_MODE])
    except:
        line = ("%s%s : %s is missing either gX or oX" % (space,path.rsplit("/",1)[1],path.rsplit("/",1)[0] ))
        return line
 
    line = " : "
 
    if not mode & stat.S_IRGRP:
        line = line + "not gR "         
    if not mode & stat.S_IROTH:
        line = line + "not oR "
    if not mode & stat.S_IWGRP:
        line = line + "not gW "
    if mode & stat.S_IWOTH:
        line = line + "oW"

    if os.stat(path)[stat.ST_GID] != 506:
        line = line + "not install owned"

    if line != " : ":
        return line
    else:
        return ""

def check_permissions(path, space="", quiet=False):
    '''
    This checks for group write, group read, and other read
    '''

    try:
        mode = stat.S_IMODE(os.stat(path)[stat.ST_MODE])
    except:
        if quiet:
            rval = "%s%s : %s is missing either gX or oX" \
                   % (space,
                      path.rsplit("/",1)[1],
                      path.rsplit("/",1)[0] )
            return rval
        else:
            print ("%s%s : %s is missing either gX or oX" \
                   % (space,
                      path.rsplit("/",1)[1],
                      path.rsplit("/",1)[0] ))
            return
        
    line = ("%s%s : " % (space,path.rsplit("/",1)[1] ))
   
    if not mode & stat.S_IRGRP:
        line = line + "not gR "         
    if not mode & stat.S_IROTH:
        line = line + "not oR "
    if not mode & stat.S_IWGRP:
        line = line + "not gW "
    if mode & stat.S_IWOTH:
        line = line + "oW"

    if os.stat(path)[stat.ST_GID] != 506:
        line = line + "not install owned"

    if line != ("%s%s : " % (space,path.rsplit("/",1)[1] )) :
        if quiet:
            return line
        else:
            print line
        return True

    return False

def enforce_requirements():
    version = platform.python_version_tuple()

    if int(version[0]) >= 2:
        if int(version[1]) >= 5:
            return;
        
    error("This program requires at least python 2.5. You may need to load the swtools module if you have not done so.")

    if getarch() == None:
        error("This machine is not listed as supported in sw_config. If you think that this is wrong, please contact your local swtools administrator")

def error(message,fatal=True):
    '''
    function to standardize error message output
    '''
    
    print >>sys.stderr, "  error:  %s  " % message

    if fatal == True: 
        sys.exit(2)

# ---------------------------------------------------------------------------
# Look for .exceptions under path. If it contains the feature string, return
# True. Otherwise, return False. If .exceptions does not exist, that's the
# same as it being empty -- i.e., there are no exceptions.
#
def exceptfile_contains(path, feature):
    if os.path.isfile(path+"/.exceptions"):
        try:            
            exceptionfile = open(path+"/.exceptions")
            exceptiontext = exceptionfile.readlines()
            exceptionfile.close()
     
            for line in exceptiontext:
                line = re.sub(r'#.*', "", line)
                if feature in line: 
                    return True
        except:
            error("%s cannot be opened" % (path+"/.exceptions"), False)
            return False

    return False

# ---------------------------------------------------------------------------
# Expand aspec, vspec, and bspec into a list of builds that match the
# criteria
#
def make_build_list(aspec, vspec, bspec):
    app = no_wildcards(aspec, 'application')

    if bspec == "*":
        error("Although wildcards are allowed for build,"
              + " * by itself is not an acceptable build spec.")

    if app == "all":
        app = "*"
        if vspec not in valid_versions() :
            error("If app is 'all', version must be one of "
                  + ", ".join(valid_versions))
    else:
        vspec = no_wildcards(vspec, 'version')

    # Build the applications path

    application_path = []
    application_path.append(os.path.join(software_root(), getarch(), app))
        
    if application_path == []:
        error("No applications match your criteria")

    # Build the versions path
    version_path = []
    for currentapplication in application_path:
        if os.path.isdir(os.path.join(currentapplication, vspec)):
            version_path.append(os.path.join(currentapplication, vspec))
        else :
            error("%s does not exist" % (currentapplication+"/"+vspec) )

    # Build the build path 

    build_path = []

    for currentversion in version_path:
        for currentbuild in glob.glob(os.path.join(currentversion,bspec)):
            build_path.append(currentbuild)    

    if build_path == []:
        error("no builds match your criteria")

    return build_path

# ---------------------------------------------------------------------------
# Expand aspec, vspec, and bspec into a list of builds that match the
# criteria
#
def make_dup_list(build_list, bspec, dspec):
    destination_list = []
    for currentbuild in build_list:
        buildname = os.path.basename(currentbuild)
        destination_list.append(os.path.dirname(currentbuild)
                                + "/"
                                + buildname.replace(bspec.strip("*"),
                                                    dspec))
    return destination_list

# ---------------------------------------------------------------------------
# Decide whether the modulefile for a version is missing and whether it
# should be reported.
#
def module_file_missing(app, version, support):
    rval = True
    arch = os.path.dirname(app)
    path = arch + "/modulefiles/" + os.path.basename(app) \
           + "/" + os.path.basename(version) + "*"
    # print >> sys.stderr, "Globbing '%s'" % path
    mlist = glob.glob(path)
    if mlist != []:
        rval = False
    elif vendor(version):
        rval = False
    elif 'vendor' in support:
        rval = False
    elif exceptfile_contains(app, 'module'):
        rval = False
    elif exceptfile_contains(version, 'module'):
        rval = False

    return rval

# ---------------------------------------------------------------------------
# Decide whether the modulefile folder for an app is missing and whether it
# should be reported.
#
def module_folder_missing(app, support):
    arch = os.path.dirname(app)
    if exceptfile_contains(app, 'module'):
        rval = False
    elif not os.path.isdir(os.path.dirname(app) \
                           + "/modulefiles/" \
                           + os.path.basename(app)) \
                           and 'vendor' not in support:
        rval = True
    else:
        rval = False

    return rval

# ---------------------------------------------------------------------------
def notbuilddirs(path,build):
   # undocumented feature
   # can put a file .notbuilddirs in the ver folder with a list
   #   of directories you want to skip
   # only reporthtml uses this so far
    if os.path.isfile(path+"/.notbuilddirs"):
        try:            
            notbuilddirsfile = open(path+"/.notbuilddirs")
            notbuilddirstext = notbuilddirsfile.readlines()
            notbuilddirsfile.close()
            
            for notbuild in notbuilddirstext:
                if notbuild.strip("\n") == build:
                    return True
        except:
            return False

    return False

def notverdirs(path,ver):
   # undocumented feature
   # can put a file .notverdirs in the app folder with a list
   #   of directories you want to skip
   # only reporthtml uses this so far
    if os.path.isfile(path+"/.notverdirs"):
        try:            
            notverdirsfile = open(path+"/.notverdirs")
            notverdirstext = notverdirsfile.readlines()
            notverdirsfile.close()
            
            for notver in notverdirstext:
                if notver.strip("\n") == ver:
                    return True
        except:
            return False

    return False

def noweb(path):
    if os.path.isfile(path+"/.exceptions"):
        try:            
            exceptionfile = open(path+"/.exceptions")
            exceptiontext = exceptionfile.readlines()
            exceptionfile.close()
     
            for line in exceptiontext:
                if "noweb" in line: 
                    if line[0] != "#":
                        return True
        except:
            error("%s cannot be opened" % (path+"/.exceptions"), False)
            return False

    return False

def controlled(path):
    if os.path.isfile(path+"/.exceptions"):
        try:            
            exceptionfile = open(path+"/.exceptions")
            exceptiontext = exceptionfile.readlines()
            exceptionfile.close()
            
            
            for line in exceptiontext:
                if "controlled" in line:                   
                    if line[0] != "#":
                        return int((line.split()[1]).strip("\n"),8)
        except:
            error("%s cannot be opened" % (path+"/.exceptions"), False)
            return False

    return False

def vendor(path):
    if os.path.isfile(path+"/.exceptions"):
        try:            
            exceptionfile = open(path+"/.exceptions")
            exceptiontext = exceptionfile.readlines()
            exceptionfile.close()
            
            
            for line in exceptiontext:
                if "vendor" in line:
                    if line[0] != "#":
                        return True
        except:
            error("%s cannot be opened" % (path+"/.exceptions"), False)
            return False

    return False

def perc(path):
    if os.path.isfile(path+"/.exceptions"):
        try:            
            exceptionfile = open(path+"/.exceptions")
            exceptiontext = exceptionfile.readlines()
            exceptionfile.close()
            
            for line in exceptiontext:
                if "perc" in line:
                    if line[0] != "#":
                        return True
        except:
            error("%s cannot be opened" % (path+"/.exceptions"), False)
            return False

    return False

def umask_to_perm(umask):
    return 0777-umask
    
def get_versions(application_path,needed_version="current",fatal=True):
    
    if type(application_path) == type([]):
        
        versions_list = []
        
        for application in application_path:
            version = get_versions(application,needed_version,fatal)
            if (version != (application +"/" + needed_version)) & (version != None):
                versions_list.append(version)

        return versions_list
        
    elif type(application_path) == type(""):
        
        if os.path.isfile(application_path+"/versions"):

            try:
                file = open(application_path+"/versions")
            except:
                error("%s/versions: error opening file" % application_path,fatal)
                return

            lines = file.readlines()
            file.close()
            
            
            version = ""
            for line in lines:
                line =  line.split(":",1)
                line[-1] = line[-1].strip()
                line[-1] = line[-1].strip("\n") 
                
                if needed_version in line[0]:
                    version = line[-1]
                    break
                else:
                    version = ""

            if version != "":
                version = application_path + "/" + version.split(":")[-1]
            else:
                return application_path+"/"+needed_version

            if not os.path.isdir(version):
                error("%s does not exist. Update %s with a valid version number" % (version, application_path+"/versions"),fatal)
        else:
            error("%s does not exist" % (application_path+"/versions"),fatal)
            return

        return version 

    

def no_wildcards(word, field):
    if "*" in word:
        error("%s : * not a valid option for %s" % (word, field))
    if "!" in word:
        error("%s : ! not a valid option for %s" % (word, field))
    return word


def return_message(path,rval):
    if rval == 0 :
        print "%-50s : passed (0)" % path
    elif rval == 1 :
        print "%-50s : failed (1)" % path
    elif rval == 2 :
        print "%-50s : batch submitted (2)" % path
    elif rval == 3:
        print "%-50s : probably an unmodified template (3)" % path
    else :
        print "error: %s has unknown return value (%s)" % (path,rval)


def make_owner_file(destination_path):
    try:
        ownerfile = open(destination_path+"/.owners","w")
        ownerfile.write(getpass.getuser())
        ownerfile.close()
        os.chmod(destination_path+"/.owners",0664)
    except:
        error("cannot create %s" % (destination_path+"/.owners"))

def make_check4newver_file(application_path):
    try:
        check4newver_file = open(application_path+"/.check4newver","w")
        today = datetime.date.today()
        days_until_check = today + datetime.timedelta(90)
        check4newver_file.write("%s: new version installed\n%s: next check of %s on %s\n" % (today,today,application_path,days_until_check))
        check4newver_file.close()
        os.chmod(application_path+"/.check4newver",0664)
    except:
        error("cannot create %s" % (destination_path+"/.check4newver"))
        
def usage():
    return "You do not need to specify an absolute path. The root and machine name are set automatically by the script.\n\nCorrect: %prog -a hdf5\nIncorrect: %prog -a /sw/xt/hdf5"

# http://mail.python.org/pipermail/python-list/2007-May/442739.html

class Tee(object):
    def __init__(self, name, mode):
        self.file = open(name, mode)
        self.stdout = sys.stdout
        sys.stdout = self
    def close(self):
        if self.stdout is not None:
            sys.stdout = self.stdout
            self.stdout = None
            if self.file is not None:
                self.file.close()
                self.file = None
    def write(self, data):
        self.file.write(data)
        self.stdout.write(data)
    def flush(self):
        self.file.flush()
        self.stdout.flush()
    def __del__(self):
        self.close()


def debug(text,DEBUGFLAG):
    if DEBUGFLAG:
        print "debug: %s" % text


def checkstatus(build):
    try:
        file = open(build + "/status")
    except:
        return "?"
    
    status = file.readline()
    status = status.strip()
    status = status.strip("\n")
    file.close()
    
    if status == "verified":
        return "v"
    elif status == "unverified":               
        return "u"
    else:
        return "?"

# ---------------------------------------------------------------------------
def outplex(msg, flist):
    '''
    Write msg (a string) to each of the file objects in flist.
    '''

    for f in flist:
        f.write(msg)
        
