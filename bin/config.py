#!/usr/bin/env python
'''
NAME
    config.py

SYNOPSIS

    from config import *

DESCRIPTION

    config.py contains all of the accessor functions for the swtools
    congiguration file, sw_config. The current implementation uses one
    accessor function per variable. The accessor functions name is
    generally very similar to the name of the variable.

HISTORY

    Implemented by Nick Jones, February 2008

    For questions or comments, please contact swadm@ornl.gov or nai@ornl.gov 

    
    2/13/2008 - config.py created
    3/31/2008 - rewrites and additional commenting
    2009.0313/tpb - moved machinename() here from swadm.py avoid a circular
                    dependency since swadm.py already depends on this file
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

import re
import socket
import sys
import os
import platform
import getpass
import datetime
import unittest
import ConfigParser
from difflib import SequenceMatcher

##############################################################################
# Generic functions used by config.py
##############################################################################

def read_config_file():
    '''
    This funtion reads sw_config and returns the string on the right hand side
    of VARIABLE=VALUE. This function does all of the nescessary newline and 
    whitespace stripping, and this funtion also handles comments.
    '''
    
    config = ConfigParser.ConfigParser()
    
    swt_root \
      = os.environ.get('SWT_ROOT', \
                       os.path.join(os.path.dirname(sys.argv[0]),'..'))
    
    sw_config \
      = os.environ.get('SW_CONFIG', \
                       config.read(os.path.join(swt_root, 'etc/', 'config')))
    
    config.read(sw_config)
    return config

##############################################################################
# Functions that read variables effecting all of the swtools
##############################################################################

def getarch(currentmachine=None):
    '''
    This function returns the architecture for the machine you are currently on.
    '''

    if currentmachine == None:
        currentmachine = machinename()
    
    config = read_config_file()
    machines = config.items('machines')
    
    r = 0.0
    for (mname, arch) in machines:
        if ( SequenceMatcher(None, currentmachine, mname).ratio() > r ):
            r = SequenceMatcher(None, currentmachine, mname).ratio()
            cur_arch = arch
    
    return os.environ.get('SW_ARCH', cur_arch)

def log_directory():
    '''
    Returns the log drectory defined in sw_config
    '''
    config = read_config_file()
    return os.path.abspath(config.get('locations', 'log'))


def machinename():
    hostname = re.sub(r'\..*', '', socket.gethostname())
    machinename = re.sub(r'\d*$', '', hostname)
    return machinename


def software_root():
    '''
    Returns the root directory as defined in sw_config
    '''
    config = read_config_file()
    return os.environ.get('SW_ROOT', \
                          os.path.abspath(config.get('locations', 'sw_root')))

def template_directory():
    '''
    Returns the template directory per arch as defined in sw_config
    '''
    config = read_config_file()
    arch = getarch()
    return os.path.join(config.get('locations', 'templates'), arch)

    
def valid_machines():
    '''
    This returns a list of machines that have been defined in sw_config
    '''
    
    config = read_config_files()
    machines = config.items('machines')
    
    valid_mach = []
    for (mname, arch) in machines:
      valid_mach.append(mname)
    
    return valid_mach


def valid_architectures():
    '''
    This returns a list of architectures that have been defined in sw_config
    '''
    
    config = read_config_files()
    machines = config.items('machines')
    
    valid_arch = []
    for (mname, arch) in machines:
      valid_arch.append(mname)
    
    return list(set(valid_arch))


##############################################################################
# Functions that read variables effecting addbuild/addpackage 
##############################################################################

def addbuild_templates():
    '''
    This returns the list of files to be copied when an addbuild is run.
    '''
    
    config = read_config_file()
    return config.items('build_templates')

def addpackage_templates():
    '''
    This returns the list of files to be copied when an addpackage is run
    '''
    
    config = read_config_file()
    return config.items('package_templates')

def builddir_perms():
    '''
    This returns an octal permissions string that the newly created build directory 
    wil be chmodded to
    '''
    config = read_config_file()
    return config.get('permissions', '_BUILDDIR')


def appdir_perms():
    '''
    This returns an octal permissions string that the newly created application directory 
    wil be chmodded to
    '''
    
    config = read_config_file()
    return config.get('permissions', '_APPDIR')

##############################################################################
# Functions that read variables effecting duplicate
##############################################################################

def duplicate_environment_variable():
    '''
    This returns the name of the environment variable to be used with duplicate
    '''
    return read_config_file("DUPLICATE_ENVVAR")

def duplicate_files():
    '''
    This returns a list of files to be modfied when doing a duplicate
    '''
    return read_config_file("DUPLICATE_MODIFIED_FILES").split(",")

def duplicate_start_flag():
    '''
    This returns the flag that should mark the beginning of the area from which
    text needs to be replaced.
    '''
    
    return read_config_file("DUPLICATE_MODIFY_START_FLAG")

def duplicate_end_flag():
    '''
    This returns the flag that should mark the end of the area from which text
    needs to be replaced.
    '''

    return read_config_file("DUPLICATE_MODIFY_END_FLAG")

##############################################################################
# Functions that read variables effecting rebuild/relink/retest
##############################################################################


def get_umask():
    '''
    When a rebuild/relink/retest is run, the umask is changed at the start of 
    script execution. This script gets the value of that umask.
    '''
    config = read_config_file()
    return config.get('permissions', 'UMASK')

def get_work_environment():
    
    config = read_config_file()
    return config.get('locations', 'workdir_env')

##############################################################################
# Functions that read variables effecting version
##############################################################################

def from_field():
    '''
    This returns the reply to address that should be used when sending email from
    the version module.
    '''
    
    return read_config_file("FROM_FIELD")

##############################################################################
# Functions that read variables effecting report
##############################################################################


def application_required_files():
    '''
    Returns a list of files that swreport should look for inside the application folder
    '''
    
    return read_config_file("APPLICATION_REQUIRED_FILES").split(",")

def build_required_files():
    '''
    This returns a list of files that swreport should look for inside the build folder
    '''
    
    return read_config_file("BUILD_REQUIRED_FILES").split(",")

def compilers(arch):
    '''
    This returns a list of compilers that should be displayed on the web
    for the architecture that is passed to this function
    '''
    
    text = read_config_file("COMPILERS")

    machine_strings = text.split(";")

    for machine_string in machine_strings:
        machine_compiler_string = machine_string.split(":")
        if machine_compiler_string[0] == arch:
            return machine_compiler_string[1].split(",")

    return []

def webhome():
    '''
    This returns the root directory for the reporthtml output
    '''
    return read_config_file("WEBHOME")

def webarchs():
    '''
    Returns a list of architectures that should be displayed on the web
    '''
    return read_config_file("WEBARCHS").split(",")

def get_show_os_on_web():
    return read_config_file("SHOW_OS_ON_WEB")

# ---------------------------------------------------------------------------
class ConfigTests(unittest.TestCase):
    # -----------------------------------------------------------------------
    def test_read_config_file(self):
        '''
        The function read_config_file() attempts to open
        SW_ROOT/sw_config and retrieves config values therefrom.
        SW_ROOT defaults to the directory where the executing program
        resides. It may be changed for testing by setting environment
        variable $SW_ROOT.

        !@! Passing in "#" causes read_config_file() to throw an IndexError
        '''
        try:
            del os.environ['SW_ROOT']
        except KeyError:
            pass

        droot = os.path.dirname(sys.argv[0])
        if not os.path.exists('%s/sw_config' % droot):
            raise Exception('File %s/sw_config does not exist.' % droot)
        else:
            vdict = {'MACHINES': self.validate_comma_colon_tuples,
                     'VALID_VERSIONS': self.validate_comma_list,
                     'TEMPLATE_DIRECTORY': self.validate_path,
                     'LOG_DIRECTORY': self.validate_path,
                     'SOFTWARE_ROOT': self.validate_path,
                     'ADDPACKAGE_TEMPLATES': self.validate_comma_colon_tuples,
                     'ADDBUILD_TEMPLATES': self.validate_comma_colon_tuples,
                     'BUILDDIR_PERMISSIONS': self.validate_octal_value,
                     'APPDIR_PERMISSIONS': self.validate_octal_value,
                     'DUPLICATE_MODIFIED_FILES': self.validate_comma_list,
                     'DUPLICATE_MODIFY_START_FLAG': self.validate_string,
                     'DUPLICATE_MODIFY_END_FLAG': self.validate_string,
                     'DUPLICATE_ENVVAR': self.validate_string,
                     'DEFAULT_UMASK': self.validate_octal_value,
                     'REBUILD_RELINK_RETEST_WORK_ENVVAR':
                        self.validate_string,
                     'FROM_FIELD': self.validate_email_address,
                     'APPLICATION_LEVEL_EXCEPTIONS': self.validate_comma_list,
                     'VERSION_LEVEL_EXCEPTIONS': self.validate_empty,
                     'BUILD_LEVEL_EXCEPTIONS': self.validate_empty,
                     'APPLICATION_REQUIRED_FILES': self.validate_comma_list,
                     'BUILD_REQUIRED_FILES': self.validate_comma_list,
                     'BUILD_EXIT3_FILES': self.validate_comma_list,
                     'WEBARCHS': self.validate_comma_list,
                     'WEBHOME': self.validate_path,
                     'COMPILERS': self.validate_semi_colon_comma_list,
                     'SHOW_OS_ON_WEB': self.validate_string}
            
            for var in vdict.keys():
                self.validate_read_config_file(var, vdict[var])
            
    # -----------------------------------------------------------------------
    def validate_read_config_file(self, var, validator):
        validator(read_config_file(var))

    # -----------------------------------------------------------------------
    def validate_comma_colon_tuples(self, val):
        for item in val.split(','):
            if ':' not in item:
                self.fail("item in list missing ':' (%s)" % item)
                     
    # -----------------------------------------------------------------------
    def validate_comma_list(self, val):
        for item in val.split(','):
            self.validate_string(item)
            
    # -----------------------------------------------------------------------
    def validate_email_address(self, val):
        if '@' not in val:
            self.fail("'@' missing from email address: %s" % val)

        (u, d) = val.split('@')
        if '.' not in d:
            self.fail("suspicious domain '%s' contains no dot" % d)
        
    # -----------------------------------------------------------------------
    def validate_empty(self, val):
        if val != '':
            self.fail("'%s' is not an empty string" % val)
            
    # -----------------------------------------------------------------------
    def validate_octal_value(self, val):
        for i in range(0, len(val)):
            if val[i] < '0' or '7' < val[i]:
                self.fail("Octal digit %c out of range" % val[i])
                
    # -----------------------------------------------------------------------
    def validate_path(self, val):
        self.validate_string(val)
        if '/' in val:
            for component in val.split('/'):
                self.validate_string(component)
            
    # -----------------------------------------------------------------------
    def validate_semi_colon_comma_list(self, val):
        for chunk in val.split(';'):
            (arch, clist) = chunk.split(':')
            self.validate_string(arch)
            for c in clist.split(','):
                self.validate_string(c)
                
    # -----------------------------------------------------------------------
    def validate_string(self, val):
        if type(val) != str:
            self.fail("%s should be a string but is %s"
                      % (str(val), type(val)))
            
    # -----------------------------------------------------------------------
    def test_getarch(self):
        '''
        We pass getarch() the name of a machine and expect back the
        machine architecture. For example, getarch("jaguar") should
        return "xt5".
        '''
        x = read_config_file('MACHINES')
        # print x
        t = {}
        for i in x.split(','):
            (k,v) = i.split(':')
            t[k] = v

        for k in t.keys():
            try:
                assert(getarch(k) == t[k])
            except:
                print 'getarch(%s) == %s' % (k, getarch(k))
                print 'expected %s' % t[k]
                raise
            
if __name__ == '__main__':
    unittest.main()
