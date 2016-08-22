'''
NAME

    duplicate.py

SYNOPSIS

    import duplicate

DESCRIPTION

    Duplicate supports two modes of operation:
        - copy current version of all applicatios into new machine tree
        - copy a single build into a new build directory within the same
          version directory

    Duplicate is very useful for testing and when you need to deploy new
    builds. It supports renaming using wildcards, and it also can automatically
    change the rebuild/retest/relink scripts
    when you copy the directories.

HISTORY

    2009.0318/tpb accept build and dup lists in the argument list
                  only generate our own lists if the passed in lists are
                    empty

                  handle --dryrun (-n) option
                  
                  updated edit_build_link_test() code to do the right
                    thing if a remodule file is present.

    2009.0413/tpb make log, debug, resume, dryun, and force arguments
                     attributes of a single arg, opts.
                  honor opts.force
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
import duplicate
import os
import shutil
import stat
import getpass


def main(application, version, build, build_path, destination, action, opts):
         # log, debug, resume, dryrun=False, force):

    # If resume is on, open the log file to read the resume data from
    
    if opts.resume != None:
        resumefile = open(opts.resume)
        resumetext = resumefile.readlines()
        resumefile.close()
    
    # If logging is enabled, use the Tee class to copy stdout to log
    
    if opts.log :
        # log_object = Tee(log_directory()+"/"+action+"/"+getarch()+"_"+machinename()+"_"+datetime.date.today().isoformat()+"_"+getpass.getuser(),"w")
        log_object = Tee("%s/%s/%s_%s_%s_%s"
                         % (log_directory(),
                            action,
                            getarch(),
                            machinename(),
                            datetime.date.today().isoformat(),
                            getpass.getuser()),
                         "w")

    # Generate the list of builds to process (unless it was passed in our
    # arguments).
    if build_path == []:
        build_path = make_build_list(application, version, build)
    
    if opts.dryrun:
        print "duplicate dryrun: would operate on the following builds:"
        for b in build_path:
            print "   %s" % b
        
    # Generate the list of destination builds to create
    destination_path = make_dup_list(build_path, build, destination)
    if opts.dryrun:
        print "duplicate dryrun: would make the following duplicates:"
        for dest in destination_path:
            print "   %s" % dest
        return

    # Copy the files

    for currentsource, currentdestination in zip(build_path,destination_path):
        
        resumeflag = False
        if opts.resume != None:
            for line in resumetext:
                if ("Duplicating %-45s %-10s %s" % (currentsource,"into",currentdestination)) in line:
                    resumeflag = True
            if resumeflag:
                print "Skipping %s" % currentsource
                continue
        elif os.path.exists(currentdestination):
            if opts.force:
                shutil.rmtree(currentdestination)
            else:
                # destination exists and we are not resuming -- skip it
                print("Destination %s already exists -- skipping"
                      % currentdestination)
                continue
        
        try:
            shutil.copytree(currentsource,currentdestination,True)
        except:
            error( "could not duplicate %-45s %-10s %s\n  Check to see if the destination directory already exists and make sure that you have the correct permissions" % (currentsource, "into",currentdestination),False)
            continue
            
        print "Duplicating %-45s %-10s %s" % (currentsource,"into",currentdestination)
        
        # Empty the status file
        
        file = open(currentdestination+"/status","w")
        file.close()

#        # Make the new owners file
#        make_owner_file(currentdestination)
#        #print "creating %s/.owners" % currentdestination
        
        # Replace the relevant sections of rebuild,relink, and retest 
        # duplicate_envrionment_variable is the name of the environment
        # variable with the name of the file with the text that needs
        # to be replaced

        edit_build_link_test(currentdestination)
        
#         environment_variable = os.getenv(duplicate_environment_variable())
# 
#         if environment_variable != None :
# 
#             # Go through the list of files
#             
#             for filename in duplicate_files():
#                 file = open(currentdestination+"/"+filename)
#                 lines = file.readlines()
#         
#             # Delete the text in between the start and end markers
#         
#                 for line in lines:
#                     # Find the start mark
#                     if line.find(duplicate_start_flag()) != -1:
#                         start = lines.index(line)+1
#                     
#                     # Find the end mark
#                     if line.find(duplicate_end_flag()) != -1:
#                         end = lines.index(line)
#     
#                 # Delete all the text in between the marks
#                 del lines[start:end]
#                 file.close()
#                 
#                 # Inject text between the start and end markers
#                 
#                 if os.path.isfile(environment_variable):
#                     file = open(environment_variable)
#                     environment_variable_lines = file.readlines()
#                 
#                     # Insert the text
#                     # There may be a more efficient way to do this operation..?
#                     for line in environment_variable_lines:
#                         lines.insert(start,line)
#                         start = start+1
#                 
#                 else:
#                     error("%s is not a file" % environment_variable)
#    
#                 file.close()
#                 file = open(currentdestination+"/"+filename,"w")
#                 file.writelines(lines)
    
    # Close the logging object
    
    if opts.log:
        log_object.close()
        
# ---------------------------------------------------------------------------
def edit_build_link_test(bpath):
    """
    Edit rebuild, relink, retest in directory bpath, replacing the env
    lines with the lines from the file <newlines>.

    In some cases, all three re* files will dot another file to set up
    the environment. If that's the case, we want to edit that file
    (sometimes called 'remodule') rather than editing the three files
    directly.
    """
    nlfile = os.getenv(duplicate_environment_variable())
    if (nlfile == None):
        return
    elif not os.path.isfile(nlfile):
        error("$SW_MODFILE is set but does not point to a valid file. It"
              + " should contain the path of a file with updated module"
              + " commands for the duplicate builds.")

    indirect_edit_done = False

    onlyupdateremodule = False

    for filename in duplicate_files():
        fpath = "%s/%s" % (bpath, filename)
        f = open(fpath, 'r')
        lines = []
        lines = f.readlines()
        f.close()

#mrf
        if (filename == "remodule") and (os.path.isfile(fpath)):   # assume remodule is listed first in config file
            remoduleexists = True

        if ((remoduleexists) and (filename == "remodule")) or ((not remoduleexists) and (filename != "remodule")):
           start, end = find_duplicate_start_end_flags(lines)
#mrf

           # I think the following could be rewritten possibly without the loop
           # can't quite figure out what Nick has it doing
           for i in range(start+1,end):
               q = re.findall(r'\. (\S+)', lines[end-1].strip())
               print q
               if (q != []) and (not indirect_edit_done):
                   edit_env_file(nlfile, editable='%s/%s' % (bpath, q[0].split("/")[-1] ))
                   indirect_edit_done = True
                   break

           try:
               if q == []:
                   edit_env_file(nlfile, editable=fpath, lines=lines)
           except UnboundLocalError:
               pass

    
# ---------------------------------------------------------------------------
def edit_env_file(nlfile, editable='', lines=[]):
    if editable == '':
        error("edit_env_file: editable == ''")
        
    if lines == []:
        f = open(editable, 'r')
        lines = f.readlines()
        f.close()

    start, end = find_duplicate_start_end_flags(lines)

    f = open(nlfile, 'r')
    updlines = f.readlines()
    f.close()

    updated = lines[0:start]
    updated.extend(updlines)
    updated.extend(lines[end:])

    os.rename(editable, '%s.old' % editable)
    
    f = open(editable, 'w')
    f.writelines(updated)
    f.close()

    # turn on the x bits on the new filex
    s = os.stat(editable)
    os.chmod(editable, s[stat.ST_MODE]
             | stat.S_IXUSR
             | stat.S_IXGRP
             | stat.S_IXOTH)

# ---------------------------------------------------------------------------
def find_duplicate_start_end_flags(lines):
    lc = 0
    end = start = -1
    for line in lines:
        if line.find(duplicate_start_flag()) != -1:
            start = lc + 1
        if line.find(duplicate_end_flag()) != -1:
            end = lc
        lc = lc + 1
    return start, end
    
