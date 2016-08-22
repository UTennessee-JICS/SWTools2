'''
Driver for calling multiple actions on apps in /sw tree.

HISTORY

    2009.0318/tpb added --dryrun (-n) option
                  added duplicate alone in the validopts table
                  call make_build_list(), make_dup_list() before
                    processing actions so only the duplicates are
                    processed by downstream actions
                  updated the action routines to accept a list of builds
                    to process
    2009.0413/tpb collapse log, debug, resume, dryrun into single argument
                    to duplicate.py
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

enforce_requirements()

import parse
import duplicate
import rebuild_retest_relink
import report

# Parse options using a modified optparse. The modifications are implemented in
# parse.py


usage = '''swdriver action [options]
actions: duplicate, rebuild, retest, relink, report-conform, report-html
'''

parser = parse.OptionParser(usage=usage)
parser.add_option("-a","--app",
                  default=None,
                  help="application name")
parser.add_option("-v","--version",
                  default="current",
                  help="version number")
parser.add_option("-b","--build",
                  default=None,
                  help="build name")
parser.add_option("-d","--dest",
                  default=None,
                  help="destination directory")
parser.add_option("-l","--log",
                  action="store_true",default=False,
                  help="Logging")
parser.add_option("--debug",
                  action="store_true",
                  help="debugging")
parser.add_option("-s","--stdout",
                  action="store_true",default=False,
                  help="enable stdout")
parser.add_option("-m","--architecture",
                  default=getarch(),
                  help="Specify a machine")
parser.add_option("-r","--resume",
                  default=None)
parser.add_option("-n", "--dryrun",
                  default=False, action="store_true",
                  help="show what would happen but don't do anything")

(opts, args) = parser.parse_args()

if opts.app == None:
    opts.app = "*"

if opts.version == None:
    opts.version = "*"

if opts.build == None:
    opts.build = "*"

if opts.dest == None:
    opts.dest = "*"


if opts.log:
    log_object = Tee("%s/swdriver/%s_%s_%s_%s" %
                     (log_directory(),
                      getarch(),
                      machinename(),
                      datetime.date.today().isoformat(),
                      getpass.getuser()),
                     "w")

if len(args) == 0 :
    error("You must specify an action\n\n%s" % usage)

validopts =[ ["duplicate","build","test"],
             ["duplicate","build"],
             ["duplicate"],
             ["build","test"],
             ["duplicate","link","test"],
             ["duplicate","link"],
             ["link","test"] ]

if args not in validopts:
    msg = "invalid combination; valid combinations are:\n"
    for x in validopts:
        msg = msg + "    %s\n" % x
    error(msg)
  
build_list = make_build_list(opts.app, opts.version, opts.build)
dup_list = []
if 'duplicate' in args:
    dup_list = make_dup_list(build_list, opts.build, opts.dest)

for action in args:

    printaction = action
    
    while len(printaction) <= 80:
        printaction = "-"+printaction+"-"
   
    print printaction
    
    if action == "duplicate":
        parser.check_required("-a")
        parser.check_required("-b")
        parser.check_required("-d")
        opts.force = False
        opts.log = False
        duplicate.main(opts.app,
                       opts.version,
                       opts.build,
                       build_list,
                       opts.dest,
                       action,
                       opts)
        oldbuild = opts.build.strip("*")
        opts.build = opts.build.replace(oldbuild,opts.dest)
  
    elif action  == "build":
        parser.check_required("-a")
        parser.check_required("-b")
        if dup_list != []:
            list_to_build = dup_list
        else:
            list_to_build = build_list
        rebuild_retest_relink.main(opts.app,
                                   opts.version,
                                   opts.build,
                                   list_to_build,
                                   False,
                                   opts.stdout,
                                   "rebuild",
                                   opts.debug,
                                   opts.resume,
                                   opts.dryrun)
    
    elif action == "test":
        parser.check_required("-a")
        parser.check_required("-b")
        if dup_list != []:
            list_to_test = dup_list
        else:
            list_to_test = build_list
        rebuild_retest_relink.main(opts.app,
                                   opts.version,
                                   opts.build,
                                   list_to_test,
                                   False,
                                   opts.stdout,
                                   "retest",
                                   opts.debug,
                                   opts.resume,
                                   opts.dryrun)
    
    elif action == "link":
        parser.check_required("-a")
        parser.check_required("-b")
        if dup_list != []:
            list_to_link = dup_list
        else:
            list_to_link = build_list
        rebuild_retest_relink.main(opts.app,
                                   opts.version,
                                   opts.build,
                                   list_to_link,
                                   False,
                                   opts.stdout,
                                   "relink",
                                   opts.debug,
                                   opts.resume,
                                   opts.dryrun)
    
    else:
        error("error: %s is not a valid action" % action)

