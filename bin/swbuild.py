'''
Driver for calling rebuild on apps in /sw tree.

See rebuild_retest_relink.py for details on implementation.

HISTORY

    2009.0318/tpb added empty build list to match the update to
                  rebuild_retest_relink.main()
    
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
import parse
import rebuild_retest_relink
from swadm import *
from config import *

enforce_requirements()


# Parse options using a modified optparse. The modifications are implemented in
# parse.py

usage = "swbuild -a APPLICATION -v VERSION -b BUILD\nExample: swbuild -a hdf5 -v 1.6.5 -b cnl2.0_pgi6.2.5"
parser = parse.OptionParser(usage=usage)
parser.add_option("-a","--app",default=None,help="Application")
parser.add_option("-v","--version",default="current",help="Version")
parser.add_option("-b","--build",default=None,help="Build")
parser.add_option("--debug",action="store_true")
parser.add_option("-l","--log",action="store_true",default=False,help="Turn on logging. Logs are output to " + log_directory() )
parser.add_option("-s","--stdout",action="store_true",default=False,help="Enable stdout from the build scripts")
parser.add_option("-r","--resume",default=None)

(opts, args) = parser.parse_args()

parser.check_required("-a")
parser.check_required("-b")

rebuild_retest_relink.main(opts.app, opts.version, opts.build, [],
                           opts.log, opts.stdout, "rebuild", opts.debug,
                           opts.resume)
