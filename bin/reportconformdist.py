#!/usr/bin/python
'''
NAME
    reportconformdist.py

SYNOPSIS

    import reportconformdist

DESCRIPTION

    The text will be buffered under each owners name.
    'swmeister' owns everything.
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

import unittest

from optparse import *

# ---------------------------------------------------------------------------
def main(architecture,application,version,build,recurse,long,tstat='FILE'):
    '''
    Main: iterate over architectures, then compose reports and send them.
    '''
    # print('main: args = (%s, %s, %s, %s, %s, %s, %s)' % 
    #       (architecture, application, version, build, recurse, long, tstat))
    args = {}
    args['recurse'] = recurse
    args['long'] = long

    tstatus(set=True, value=tstat)
    
    # Architecture defaults to *; we also support all
    # print("long = %s" % str(args['long']))
    if (architecture != "*") & (architecture != "all") :
        architectures = glob.glob(swroot()+"/"+architecture)

        if architectures == []:
            error("invalid architecture")
            
    else:
        # Otherwise, use the architectures that are defined in sw_config
        architectures = []
        for currentarchitecture in valid_architectures():
            archpath = glob.glob(swroot()+"/"+currentarchitecture)
            if archpath != []:
                architectures.append(archpath[0])
            else:
                error("invalid architectures defined in sw_config (%s)"
                      % currentarchitecture)

    # print("main: architectures = ", architectures)
    # Iterate over architectures generating a report for each
    reports = []
    for currentarchitecture in architectures:
        r = Report(currentarchitecture, 'arch')
        r.target('swmeister')
        args['parent_report'] = r
        # See if the defined archtitecture is a valid directory
        
        if os.path.isdir(currentarchitecture):
            p = check_dir_permissions(currentarchitecture)
            if p != '':
                r.buffer('/' + os.path.basename(currentarchitecture) + p)
                r.make_reportable()
            
        applications = get_application_list('%s/%s'
                                            % (currentarchitecture,
                                               application))
       
        # Iterate over applications, compiling reports as appropriate
        for currentapplication in applications:
            # print 'main: handling %s' % currentapplication
            handle_application(currentapplication, version, build, r, args)

        reports.append(r)

    # Compose reports
    m = {}
    m['swmeister'] = Message('swmeister')
    for r in reports:
        # swmeister gets all reports
        m['swmeister'].add(r.compose())
        for sr in r.subreports:
            # sub reports go to application and build owners
            for recip in sr.recipient_list():
                try:
                    m[recip].add(sr.compose(parent=r))
                except KeyError:
                    m[recip] = Message(recip)
                    m[recip].add(sr.compose(parent=r))

    # Send the reports
    mlr = Mailer()
    # print "Message keys: ", m.keys()
    for recip in m.keys():
        mlr.send(m[recip])
    mlr.close()
    
# ---------------------------------------------------------------------------
# collect app information in a dict named 'args'
#
def handle_application(app_path, version, build, parent_rpt, args):
    r = Report(app_path, 'app')
    parent_rpt.add_subreport(r)
    perms = check_dir_permissions(app_path)
    # print("handle_application: perms = %s" % perms)
    if perms != '':
        r.make_reportable()

    args['supportstatus'] = read_supportfile(app_path)
    r.target(get_owners(app_path))
    
    if os.path.isdir(app_path):
        r.buffer("(support status: " + args['supportstatus']
                 + ")" + check_dir_permissions(app_path))

        if module_folder_missing(app_path, args['supportstatus']):
            r.buffer("no modulefiles folder")  # tested
            r.make_reportable()

        if out_of_date(app_path, args['supportstatus'], r):
            r.make_reportable()
            
        # Look for missing files

        for file in application_required_files():
            if not os.path.isfile(app_path+"/"+file):
                r.buffer("%s is missing" % file)  # tested
                r.make_reportable()
            else:
                myfile = open(app_path+"/"+file)
                lines = myfile.readlines()
                if lines == []:
                    r.buffer("%s is empty" % file)  # tested
                    r.make_reportable()
                    
                perms = check_dir_permissions(app_path+"/"+file)
                     
                if perms != "" :
                    r.buffer(file + perms)
                    r.make_reportable()
                
        # Validate owner files if any exist here (not required)
        vl = validate_owner_file(app_path)
        for v in vl:
            r.buffer(v)
            
        # Make sure the templates have been modified
        cmd = "diff %s/description %s/description > /dev/null 2>&1" % (
            app_path,
            template_directory())
        rval = subprocess.call(cmd, shell=True)
        if rval == 0:
            r.buffer("description is unchanged from the template") # tested
            r.make_reportable()
        
    # Print versions
        
    versions = glob.glob(app_path+"/"+version)
    versions.sort()

    for currentversion in versions:
#mrf:start
        # check if .notverdirs file exists and if so
        # skip all directory names it contains
        if not os.path.isdir(currentversion) \
               or notverdirs(app_path, os.path.basename(currentversion)):
            continue
#mrf:end
        handle_version(currentversion, build, r, args)

# ---------------------------------------------------------------------------
def handle_version(currentversion, build, parent_rpt, args):
    r = Report(currentversion, 'ver')
    parent_rpt.add_subreport(r)
    
    app_path = os.path.dirname(currentversion)
    
#     if args['long']:
#         pass
        # stdoutver = sys.stdout
        # sys.stdout = StringIO.StringIO()

    perms = check_dir_permissions(currentversion)
    if perms != "":
        r.make_reportable()
    if os.path.isdir(currentversion):
        r.buffer(perms.strip(": "))   # tested
           
        if module_file_missing(app_path,
                               currentversion,
                               args['supportstatus']):
            r.buffer("version does not have modulefile") # tested
            r.make_reportable()
            
    builds = glob.glob(currentversion+"/"+build)

    for currentbuild in builds:
        if not os.path.isdir(currentbuild):
            builds.remove(currentbuild)

    for currentbuild in builds:
        handle_build(currentbuild, r, args)
            
# ---------------------------------------------------------------------------
def handle_build(currentbuild, parent_rpt, args):
    # print("handle_build: %s, %s, %s"
    #       % (currentbuild, str(parent_rpt), str(args)))
    r = Report(currentbuild, 'build')
    parent_rpt.add_subreport(r)
    # if args['long']:
    #     pass
        # stdoutbuild = sys.stdout
        # sys.stdout = StringIO.StringIO()
                
    perms = check_dir_permissions(currentbuild)
    if perms != "":
        r.buffer(perms.strip(": "))
        r.make_reportable()
                
    if "is missing either gX or oX" in perms:
        # !@! add test - untriggerable for now
        r.buffer(perms + ' foozle')    # UNtested

    # currentbuild is always a dir -- handle_build is never called
    # for non directories
    if os.path.isdir(currentbuild):
        r.target(get_owners(currentbuild))
        vl = validate_owner_file(currentbuild, required=True)
        for v in vl:
            r.buffer(v)
                
        files = glob.glob(currentbuild+"/*")

        for file in files:
            p = check_permissions(file, '', True)
            if p:
                r.buffer(p)
                r.make_reportable()
            
        files = build_required_files() 
                    
        if os.path.isfile(currentbuild+"/.lock"):
            r.buffer("Lockfile present")
            r.make_reportable()
                
        for file in files:
            if not os.path.isfile(currentbuild+"/"+file):
                r.buffer("%s is missing" % file)
                r.make_reportable()
                                
        for file in ["rebuild","relink","retest"]:
            if os.path.isfile(currentbuild+"/"+file):
                try:
                    myfile = open(currentbuild+"/"+file)
                except:
                    r.buffer("%s could not be opened" % file)    # UNtested
                    r.make_reportable()
                    continue
                    
                lines = myfile.readlines()
                myfile.close()
                    
                for line in lines:
                    if "#" not in line:
                        if "exit 3" in line:
                            r.buffer("%s contains an exit 3" % (file))
                            r.make_reportable()

        # print("recurse = %s" % args['recurse'])
        if args['recurse']:
            reportable = False
            now = datetime.date.today().isoformat()
            tbuf = []
            space = ''
            for root, dirs, files in os.walk(currentbuild):
                if root != currentbuild:
                    ppath = root.replace(currentbuild, '')
                    steps = string.count(ppath, '/')
                    p = check_dir_permissions(root)
                    if p != '':
                        tbuf.append('%s/%s' % (space,
                                               os.path.basename(root)))
                        reportable = True
                        
                    space = space + '  '
                    for f in files:
                        p = check_permissions(root+'/'+f, quiet=True)
                        if any_in(['not gR', 'not gW', 'not oR', 'oW'], p):
                            tbuf.append('%s%s : ' % (space, p.rstrip(' :')))
                            reportable = True
            if reportable:
                r.make_reportable()
                for line in tbuf:
                    r.buffer(line)
            
# ---------------------------------------------------------------------------
def any_in(needle_list, haystack):
    for needle in needle_list:
        if needle in haystack:
            return True
    return False

# ---------------------------------------------------------------------------
def default_domain():
    if tstatus() != 'LIVE':
        domain = 'mailinator.com'
    else:
        domain = 'ccs.ornl.gov'
    return domain
                                    
# ---------------------------------------------------------------------------
def out_of_date(currentapplication, supportstatus, r):

    # Apps with only 'vendor' support cannot get out of date
    
    if re.match(r'^\s*vendor\s*$', supportstatus):
        return False
    
    # Open check4newver

    try:
        file = open(currentapplication+"/.check4newver")
        lastline = file.readlines()[-1]
        file.close()
    except:
        r.buffer("error: %s is empty or cannot be read"
                 % (currentapplication+"/.check4newver"))    # UNtested
        lastline = ""
        r.make_reportable()

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
        # r.buffer('           .check4newver: no "next check" in last line')
        r.buffer('.check4newver: no "next check" in last line')
        duedate = datetime.date(3000,1,1)
        r.make_reportable()
        
    if (datetime.date.today() > duedate):
        r.buffer("this software is out of date")
        r.make_reportable()

# ---------------------------------------------------------------------------
def read_supportfile(app_path):
    '''
    Read the support file at app_path and return its contents.
    '''
    try:
        supportfile = open(app_path+"/support")
        rval = supportfile.readlines()[0].strip("\n")
        supportfile.close()
    except Exception, e:
        rval = "support file cannot be read"
        
    return rval

# ---------------------------------------------------------------------------
def contents(filename):
    '''
    Contents of filename in a list, one line per element. If filename does
    not exist or is not readable, an IOError is thrown.
    '''
    f = open(filename, 'r')
    rval = f.readlines()
    f.close()
    return rval

# ---------------------------------------------------------------------------
def get_application_list(globbable):
    '''
    Build and return a list of applications based on globbable.
    Globbable is a path including an architecture and either an app
    name or an app specification with wildcards. For example,
    '/sw/xt5/*metis', or '/sw/xt5/*'.
    '''
    rv = glob.glob(globbable)

    # remove exceptions
    exceptions = application_exceptions()

    arch = os.path.dirname(globbable)
    for exc in exceptions:
        if (arch+"/"+exc) in rv:
            rv.remove(arch+"/"+exc)
       
    rv.sort()
    return rv

# ---------------------------------------------------------------------------
def get_owners(path):
    '''
    Collect usernames from the files .owner and .owners in path.
    Return the list.
    '''
    rv = []
    for name in ['.owner', '.owners']:
        fpath = '%s/%s' % (path, name)
        try:
            x = ''.join(contents(fpath))
        except IOError:
            x = ''
        # print('get_owners: "%s"' % x)
        for o in re.split(r'\s*,\s*|\s+', x):
            if o != '':
                rv.append(o)
    return rv

# ---------------------------------------------------------------------------
def validate_owner_file(path, required=False):
    '''
    Validate the .owner and/or .owners file(s) in path.

    .owner or .owners is required at build level. Both are allowed.
    .owner or .owners is allowed but not required at the app level.
    '''
    rv = []
    atleastone  = False
    for name in ['.owner', '.owners']:
        fpath = '%s/%s' % (path, name)
        if os.path.exists(fpath):
            atleastone = True
            try:
                f = open(fpath, 'r')
                f.close()
            except:
                rv.append("can't open %s" % name)
    if required and not atleastone:
        rv.append("can't open .owner")

    return rv

# ---------------------------------------------------------------------------
def swroot(set=False, value=''):
    '''
    If value is unset or empty, return software_root()
    Otherwise, return swroot_value
    If set is true, update swroot_value from value
    '''
    global swroot_value
    
    if set:
        swroot_value = value

    try:
        rv = swroot_value
    except NameError:
        rv = software_root()

    return rv

# ---------------------------------------------------------------------------
def tstatus(set=False, value=''):
    '''
    If this function returns 'LIVE', e-mail will be sent to the
    package owner(s).
    return 'LIVE'         => send mail to staff members
    return 'TBARRON'      => send mail to tbarron@ornl.gov
    return 'MAILINATOR'   => send mail to WHOEVER@mailinator.com
    return 'FILE'         => put mail message in local files for review
    '''
    global tstat_value

    if set:
        tstat_value = value

    try:
        rval = tstat_value
    except NameError:
        tstat_value = 'FILE'
        rval = tstat_value
        
    return rval

# ---------------------------------------------------------------------------
class Mailer:
    '''
    A Mailer object knows how to push sendables out over an SMTP link.
    '''
    # -----------------------------------------------------------------------
    def __init__(self):
        '''
        Mailer constructor.

        Initialize the connected flag to False and cache our testing status.
        '''
        self.connected = False
        self.sink = tstatus()
        
    # -----------------------------------------------------------------------
    def close(self):
        '''
        Shutdown the Mailer object.

        This only does something is self.connected is True.
        '''
        if self.connected:
            self.server.quit()
        else:
            print 'Mailer never connected -- closing without quit'

    # -----------------------------------------------------------------------
    def send(self, msg):
        '''
        Connect to SMTP if necessary and send the message.

        msg should be a Message object (i.e., something that has a
        sendable() attribute).
        '''
        s = msg.sendable()
        if s != None:
            if tstatus() in 'MAILINATOR TBARRON LIVE':
                if not self.connected:
                    print('Mailer.send: connecting to server')
                    self.server = smtplib.SMTP('localhost')
                    self.server.set_debuglevel(0)
                    self.connected = True

                print("not sending mail to %s" % msg.toaddr())
                self.server.sendmail(msg.fromaddr(),
                                     msg.toaddr(),
                                     msg.sendable())
            elif tstatus() == 'FILE':
                print("saving output to file %s" % msg.toaddr())
                f = open(msg.toaddr(), 'w')
                f.write(msg.sendable())
                f.close()

# ---------------------------------------------------------------------------
class Message:
    '''
    A Message object has a body, a recipient, and a sendable() method.
    '''
    
    # -----------------------------------------------------------------------
    def __init__(self, recipient):
        '''
        Unless testing status is 'LIVE', we're going to munge the to
        address so we don't send spam to anybody.
        '''
        domain = default_domain()
            
        if recipient == 'swmeister':
            self.recipient = 'tbarron@' + domain
        elif not '@' in recipient:
            self.recipient = recipient + '@' + domain
        else:
            self.recipient = recipient
            if tstatus() != 'LIVE':
                self.recipient = re.sub('@.*', '@%s' % domain, self.recipient)
        self.body = ''

    # -----------------------------------------------------------------------
    def add(self, input):
        '''
        Add text to the body of the message.
        '''
        # print "Message.add: adding '%s'" % input
        self.body = self.body + input

    # -----------------------------------------------------------------------
    def fromaddr(self):
        '''
        Return the default 'from' address.
        '''
        return 'swadm-no-reply@ccs.ornl.gov'

    # -----------------------------------------------------------------------
    def toaddr(self):
        '''
        Return the message recipient address.
        '''
        return self.recipient
    
    # -----------------------------------------------------------------------
    def sendable(self):
        '''
        Format the message for sending, unless it is empty.
        '''
        if self.body != '':
            msg = ("From: %s\r\n" % self.fromaddr()
                   + "To: %s\r\n" % self.toaddr()
                   + "Subject: SW Conformance Report\r\n\r\n"
                   + self.body)
            return msg
        else:
            return None
        
# ---------------------------------------------------------------------------
class Report:
    '''
    A Report object contains information about one level of the hierarchy.

    It may contain sub-reports (which are themselves Report objects)
    about lower levels. It also has a list of recipients, and a flag
    to indicate whether it is reportable or not. A Report is
    reportable if its reportable flag is set, or of the reportable
    flag of any of its children is set.
    '''
    # -----------------------------------------------------------------------
    def __init__(self, path=None, type=None):
        '''
        Report constructor.

        Initialize the members and handle invalid calling conditions (no
        path or type passed in).
        '''
        if path == None:
            raise Exception('Report path must be specified at creation')
        else:
            self.path = path
        if type == None:
            raise Exception('Report type must be specified at creation')
        else:
            self.type = type
        self.specific = []
        self.recipients = []
        self.subreports = []
        self.reportable = False
        # self.reportable = True
        
    # -----------------------------------------------------------------------
    def add_subreport(self, subrpt):
        '''
        Add a sub-report as a child of self.
        '''
        self.subreports.append(subrpt)
        
    # -----------------------------------------------------------------------
    def buffer(self, string):
        '''
        Add a line of text to the body of this report.
        '''
        # print("Report.buffer: appending '%s'" % string)
        self.specific.append(string)

    # -----------------------------------------------------------------------
    def child_reportable(self):
        '''
        Check whether any of self's children are reportable.
        '''
        rval = False
        for r in self.subreports:
            if r.reportable or r.child_reportable():
                rval = True
                break
        return rval
    
    # -----------------------------------------------------------------------
    def compose(self, indent='', parent=None):
        '''
        Format the report for display if reportable.

        Return a string containing the report.
        '''
        rv = ''
        phdr = ''
        if parent != None:
            phdr = parent.header() + '\n'
            indent = '        '
        if self.reportable or self.child_reportable():
            rv = rv + '%s/%s (%s)\n' % (indent,
                                        os.path.basename(self.path),
                                        self.recipients_str())
#             if parent != None:
#                 rv = rv + '\n%s/%s (%s)\n' % (parent.header(),
#                                               os.path.basename(self.path),
#                                               self.recipients_str())
#             else:
#                 rv = rv + '%s/%s (%s)\n' % (indent,
#                                             os.path.basename(self.path),
#                                             self.recipients_str())
            if self.reportable:
                # print self.specific
                for item in self.specific:
                    if item.strip() != '':
                        rv = rv + "%s        %s\n" % (indent, item)
            for subrpt in self.subreports:
                rv = rv + subrpt.compose('%s        ' % indent)
        if (rv.strip() != '') and (phdr != ''):
            rv = phdr + rv
        return rv
    
    # -----------------------------------------------------------------------
    def header(self):
        '''
        Return the header of this report, essentially the path it describes.
        '''
        rv = self.path
        # print "Report.header: ", self.specific
#         for item in self.specific:
#             if item.strip() != '':
#                 rv = rv + "        %s\n" % (item)
        # print("Report.header() returns '%s'" % rv)
        return rv
    
    # -----------------------------------------------------------------------
    def make_reportable(self):
        '''
        Make this report reportable.
        '''
        self.reportable = True

    # -----------------------------------------------------------------------
    def recipient_list(self):
        '''
        Return the recipient list as a list.

        Rolls up all recipients of all children.
        '''
        if self.subreports == []:
            return self.recipients
        else:
            rv = self.recipients
            for s in self.subreports:
                # rv.extend(s.recipient_list())
                for r in s.recipient_list():
                    if r not in rv:
                        rv.append(r)
            return rv
        
    # -----------------------------------------------------------------------
    def recipients_str(self):
        '''
        Return the recipient list as a string.

        Rolls up all recipients of all children.
        '''
        if self.recipients == []:
            rval = ''
        else:
            rval = ', '.join(self.recipient_list())
        return rval
    
    # -----------------------------------------------------------------------
    def summarize(self, indent=''):
        '''
        Return a string containing a summary version of the report.
        '''
        rv = ''
        if self.reportable or self.child_reportable():
            rv = '%s/%s (%s)\n' % (indent,
                                   os.path.basename(self.path),
                                   self.recipients_str())
            for subrpt in self.subreports:
                rv = rv + subrpt.summarize('%s     ' % indent)
        return rv
              
    # -----------------------------------------------------------------------
    def target(self, recip):
        '''
        Add one or more e-mail addrs to the recipient list without dups.
        '''
        if type(recip) == list:
            # self.recipients.extend(recip)
            for r in recip:
                if r not in self.recipients:
                    self.recipients.append(r)
                    # print('target: sending report %s to %s' % (str(self), r))
        elif type(recip) == str:
            if recip not in self.recipients:
                self.recipients.append(recip)
                # print('target: sending report %s to %s' % (str(self), recip))
        else:
            raise Exception('recip type must be list or string')

    # -----------------------------------------------------------------------
    def write(self, indent=''):
        '''
        Format and return a debug version of the report.
        '''
        rv = ''
        if self.reportable or self.child_reportable():
            rv = '%s/%s (%s)\n' % (indent,
                                   os.path.basename(self.path),
                                   self.recipients_str())
            if self.reportable:
                for item in self.specific:
                    item.strip()
                    if item != '':
                        rv = rv + "%s        %s\n" % (indent, item)
            for subrpt in self.subreports:
                rv = rv + subrpt.write('%s        ' % indent)
        return rv

# ---------------------------------------------------------------------------
testdir = "/tmp/reportconformdist_test/sw"
checkfile = '%s/.check4newver' % testdir
supportfile = '%s/support' % testdir
readfile = '%s/readme' % testdir
testapp = '%s/xt5/testapp' % testdir
testbuild = '%s/1.0/cnl2.1_gnu4.2.4' % testapp

# ---------------------------------------------------------------------------
class RCD_Test_Contents(unittest.TestCase):
    '''
    Tests for the routine contents().
    '''
    # -----------------------------------------------------------------------
    def test_badperms(self):
        '''
        Test contents() on a file with bad permissions.
        The function should raise an exception.
        '''
        prepare_tests()
        safe_unlink(readfile)
        open(readfile, 'w').close()
        os.chmod(readfile, 0)

        try:
            x = contents(readfile)
        except IOError, e:
            expectVSgot("[Errno 13] Permission denied: '%s/readme'" % testdir,
                        str(e))

        # x should not exist - the assignment should never have happened
        assert('x' not in locals().keys())
        os.unlink(readfile)
        
    # -----------------------------------------------------------------------
    def test_empty(self):
        '''
        Test contents() on an empty file.
        It should return an empty list.
        '''
        prepare_tests()

        if os.path.exists(readfile):
            unlink(readfile)
        open(readfile, 'w').close()

        x = contents(readfile)

        assert(x == [])
        
    # -----------------------------------------------------------------------
    def test_no_such_file(self):
        '''
        Test contents() on a file that does not exist.
        It should raise an excpetion.
        '''
        prepare_tests()
        safe_unlink(readfile)

        try:
            x = contents(readfile)
        except IOError, e:
            got = str(e)
            expect = ("[Errno 2] No such file or directory: '%s/readme'"
                      % testdir)
            expectVSgot(expect, got)
                   
        assert('x' not in locals().keys())
        
    # -----------------------------------------------------------------------
    def test_readable(self):
        '''
        Test contents on a readable file.
        It should return a list of lines, with line terminators.
        '''
        prepare_tests()

        f = open(readfile, 'w')
        f.write('one\ntwo\nthree\n')
        f.close()

        x = contents(readfile)

        assert(x == ['one\n', 'two\n', 'three\n'])

# ---------------------------------------------------------------------------
class RCD_Test_GetOwners(unittest.TestCase):
    '''
    Tests for routine get_owners().
    '''
    # -----------------------------------------------------------------------
    def test_both(self):
        '''
        Test get_owners().
        It should accumulate names across files .owner and .owners and
        return a flat list of all the owners found.
        '''
        prepare_tests()
        for f in ['.owner', '.owners']:
            safe_unlink(f)
        writefile('.owner', ['joe'])
        writefile('.owners', ['billy'])
        expected = ['billy', 'joe']
        got = get_owners('.')
        got.sort()
        expectVSgot(expected, got)
        
    # -----------------------------------------------------------------------
    def test_commas(self):
        '''
        Test get_owners().
        It should parse comma separated lists if they are present in the
        file(s).
        '''
        prepare_tests()
        for f in ['.owner', '.owners']:
            safe_unlink(f)
        writefile('.owner', ['joe\n', 'zach, betty\n'])
        writefile('.owners', ['billy, angela\n', 'wilma\n'])
        expected = ['angela', 'betty', 'billy', 'joe', 'wilma', 'zach']
        got = get_owners('.')
        got.sort()
        expectVSgot(expected, got)
        
    # -----------------------------------------------------------------------
    def test_empty_comma(self):
        '''
        Test get_owners().
        It should be smart about empty entries between commas and throw
        such entries away before building the list it will return.
        '''
        prepare_tests()
        for f in ['.owner', '.owners']:
            safe_unlink(f)
        writefile('.owner', ['joe ,   , sally \n', 'zach, betty\n'])
        writefile('.owners', ['andrew   ,\n', '\n', '  , pedro'])
        expected = ['andrew', 'betty', 'joe', 'pedro', 'sally', 'zach']
        got = get_owners('.')
        got.sort()
        expectVSgot(expected, got)
        
    # -----------------------------------------------------------------------
    def test_empty_file(self):
        '''
        Test get_owners().
        It should be smart about empty files and not include any entries
        for the empty file in the list returned.
        '''
        prepare_tests()
        for f in ['.owner', '.owners']:
            safe_unlink(f)
        writefile('.owner', ['joe\n', 'zach, betty\n'])
        writefile('.owners', [])
        expected = ['betty', 'joe', 'zach']
        got = get_owners('.')
        got.sort()
        expectVSgot(expected, got)
        
    # -----------------------------------------------------------------------
    def test_empty_line(self):
        '''
        Test get_owners().
        
        It should not generate any entries for an empty line in one of
        its input files.
        '''
        prepare_tests()
        for f in ['.owner', '.owners']:
            safe_unlink(f)
        writefile('.owner', ['joe\n', 'zach, betty\n'])
        writefile('.owners', ['andrew\n', '\n', 'pedro'])
        expected = ['andrew', 'betty', 'joe', 'pedro', 'zach']
        got = get_owners('.')
        got.sort()
        expectVSgot(expected, got)
        
    # -----------------------------------------------------------------------
    def test_extra_whitespace(self):
        '''
        Test get_owners().

        It should not be confused by extra whitespace in an input file.
        '''
        prepare_tests()
        for f in ['.owner', '.owners']:
            safe_unlink(f)
        writefile('.owner', ['joe ,   , \tsally \r\n', 'zach, betty\n'])
        writefile('.owners', ['andrew   ,\n', '\n', '  , pedro'])
        expected = ['andrew', 'betty', 'joe', 'pedro', 'sally', 'zach']
        got = get_owners('.')
        got.sort()
        expectVSgot(expected, got)
        
    # -----------------------------------------------------------------------
    def test_multiline(self):
        '''
        Test get_owners().

        Multi-line owner files are okay.
        '''
        prepare_tests()
        for f in ['.owner', '.owners']:
            safe_unlink(f)
        writefile('.owner', ['joe\n', 'zach\n'])
        writefile('.owners', ['billy\n', 'wilma\n'])
        expected = ['billy', 'joe', 'wilma', 'zach']
        got = get_owners('.')
        got.sort()
        expectVSgot(expected, got)
        
    # -----------------------------------------------------------------------
    def test_neither(self):
        '''
        Test get_owners().

        If no .owner or .owners files exists, return an empty list.
        '''
        prepare_tests()
        for f in ['.owner', '.owners']:
            safe_unlink(f)
        expected = []
        got = get_owners('.')
        expectVSgot(expected, got)
        
    # -----------------------------------------------------------------------
    def test_plural_only(self):
        '''
        Test get_owners().

        If only .owners exists, use it.
        '''
        prepare_tests()
        for f in ['.owner', '.owners']:
            safe_unlink(f)
        expected = ['sally']
        writefile('.owners', expected)
        got = get_owners('.')
        expectVSgot(expected, got)
        
    # -----------------------------------------------------------------------
    def test_single_only(self):
        '''
        Test get_owners().

        If only .owner exists, use it.
        '''
        prepare_tests()
        for f in ['.owner', '.owners']:
            safe_unlink(f)
        expected = ['sally']
        writefile('.owner', expected)
        got = get_owners('.')
        expectVSgot(expected, got)
        
# ---------------------------------------------------------------------------
class RCD_Test_GetApplicationList(unittest.TestCase):
    '''
    Tests for the routine get_application_list().
    '''
    # -----------------------------------------------------------------------
    def test_single_app_exception(self):
        '''
        Argument = '.../xt5/man' => list = []
        '''
        prepare_tests()
        write_sw_config(swroot=testdir)
        target = '%s/xt5/man' % testdir
        if not os.path.exists(target):
            os.mkdir(target)
        l = get_application_list(target)
        assert(l == [])
    
    # -----------------------------------------------------------------------
    def test_single_app_exists(self):
        '''
        Argument = '.../xt5/acml' => list = ['.../xt5/acml']
        '''
        prepare_tests()
        write_sw_config(swroot=testdir)
        target = '%s/xt5/acml' % testdir
        if not os.path.exists(target):
            os.mkdir(target)
        l = get_application_list(target)
        assert(l == [target])
    
    # -----------------------------------------------------------------------
    def test_single_app_notthere(self):
        '''
        Argument = '.../xt5/nosuchapp' => list = []
        '''
        prepare_tests()
        write_sw_config(swroot=testdir)
        target = '%s/xt5/nosuchapp' % testdir
        l = get_application_list(target)
        assert(l == [])
    
    # -----------------------------------------------------------------------
    def test_wildcard_app_exception(self):
        '''
        Argument = '.../xt5/*except*' => list = ['.../xt5/notanexception',
        '.../xt5/find_exceptions'] (excludes '.../xt5/isanexception',
        which exists and is in the exception list)
        '''
        prepare_tests()
        write_sw_config(swroot=testdir)
        targets = [x % testdir for x in ['%s/xt5/etc',
                                         '%s/xt5/not_except_etc',
                                         '%s/xt5/etcetera']]
        expecting = [x % testdir for x in ['%s/xt5/not_except_etc',
                                           '%s/xt5/etcetera']]
        globbable = '%s/xt5/*etc*' % testdir
        for t in targets:
            if not os.path.exists(t):
                os.mkdir(t)
        l = get_application_list(globbable)
        for item in expecting:
            assert(item in l)
    
    # -----------------------------------------------------------------------
    def test_wildcard_app_exists(self):
        '''
        Argument = '.../xt5/*metis' => list = ['.../xt5/metis',
        '.../xt5/parmetis']
        '''
        prepare_tests()
        write_sw_config(swroot=testdir)
        targets = [x % testdir for x in ['%s/xt5/metis',
                                         '%s/xt5/parmetis']]
        globbable = '%s/xt5/*metis*' % testdir
        for t in targets:
            if not os.path.exists(t):
                os.mkdir(t)
        l = get_application_list(globbable)
        expectVSgot(targets, l)
    
    # -----------------------------------------------------------------------
    def test_wildcard_app_notthere(self):
        '''
        Argument = '.../xt5/nosuchapp*'.
        Expected result: list = []
        '''
        prepare_tests()
        write_sw_config(swroot=testdir)
        globbable = '%s/xt5/*nosuchapp*' % testdir
        l = get_application_list(globbable)
        expectVSgot([], l)
    
# ---------------------------------------------------------------------------
class RCD_Test_Main(unittest.TestCase):
    '''
    Tests for the main() routine.
    '''
    # -----------------------------------------------------------------------
    def test_app_both_owner_okay(self):
        '''
        Files .owner, .owners exist and are accessible.

        Expected result: no owner complaints at app level
        '''
        prepare_tests()
        lfname = sys._getframe().f_code.co_name.replace('test_', '') + '.log'
        write_sw_config(swroot=testdir)
        safe_unlink(['%s/.owner' % testapp, '%s/.owners' % testapp,
                     '%s/.owner' % testbuild, '%s/.owners' % testbuild])
        [sfile, pfile] = [x % testapp for x in ['%s/.owner', '%s/.owners']]
        writefile(sfile, ['tpb'])
        writefile(pfile, ['vinod'])

        logfile(filename=lfname, start=True)
        main('*', '*', '*', '*', '', 'long', tstat='FILE')
        logfile(stop=True)

        x = ''.join(contents('%s/tpb@mailinator.com' % testdir))
        assert(("/testapp (tpb, vinod)" in x))
        assert(("\n%16scan't open .owner\n" % ' ') not in x)
        assert(("\n%16scan't open .owners\n" % ' ') not in x)
        
    # -----------------------------------------------------------------------
    def test_app_indent(self):
        '''
        App owner report should have application indented one level.
        '''
        prepare_tests()
        lfname = sys._getframe().f_code.co_name.replace('test_', '') + '.log'
        write_sw_config(swroot=testdir)

        safe_unlink(['%s/.owner' % testapp, '%s/.owners' % testapp,
                     '%s/.owner' % testbuild, '%s/.owners' % testbuild])
        writefile('%s/.owner' % testbuild, ['tpb'])
        writefile('%s/support' % testapp, ['vendor'])
        
        logfile(filename=lfname, start=True)
        main('*', '*', '*', '*', '', 'long', tstat='FILE')
        logfile(stop=True)
        
        x = ''.join(contents('%s/tpb@mailinator.com' % testdir))
        assert('\n%8s/testapp (tpb)' % ' ' in x)
        
    # -----------------------------------------------------------------------
    def test_app_perms(self):
        '''
        In handle_application(), trigger support status + app dir perms
        '''
        prepare_tests()
        lfname = sys._getframe().f_code.co_name.replace('test_', '') + '.log'
        write_sw_config(swroot=testdir)
        writefile('%s/.owner' % testbuild, ['tpb'])
        writefile('%s/support' % testapp, ['vendor'])
        logfile(filename=lfname, start=True)
        main('xt5', 'testapp', '*', '*', '', 'long', tstat='FILE')
        logfile(stop=True)
        
        x = ''.join(contents('%s/tbarron@mailinator.com' % testdir))
        assert('\n%16s(support status: vendor) : not gW \n' % ' ' in x)
        assert('/1.0 (tpb)\n%24snot gW' % ' ' in x)
        assert(('/cnl2.1_gnu4.2.4 (tpb)\n%32snot gW' % ' ') in x)
        
    # -----------------------------------------------------------------------
    def test_app_plural_owners_perm(self):
        '''
        .owners exists but not accessible => "can't open .owners" at app level
        '''
        prepare_tests()
        lfname = sys._getframe().f_code.co_name.replace('test_', '') + '.log'
        write_sw_config(swroot=testdir)
        filename = '%s/.owners' % testapp
        safe_unlink([x % testapp for x in ['%s/.owner', '%s/.owners']])
        writefile(filename, ['tpb'])
        os.chmod(filename, 0222)

        logfile(filename=lfname, start=True)
        main('*', '*', '*', '*', '', 'long', tstat='FILE')
        logfile(stop=True)

        x = ''.join(contents('%s/tpb@mailinator.com' % testdir))
        assert(("\n%16scan't open .owners" % ' ') in x)
        
    # -----------------------------------------------------------------------
    def test_app_req_empty(self):
        '''
        Trigger messages "<filename> is empty" for each file in
        application_required_files() list.
        '''
        prepare_tests()
        lfname = sys._getframe().f_code.co_name.replace('test_', '') + '.log'

        write_sw_config(swroot=testdir)

        writefile('%s/.owner' % testbuild, ['tpb'])
        paths = ['%s/%s' % (testapp, name)
                 for name in application_required_files()]
        for fpath in paths:
            safe_unlink(fpath)
            open(fpath, 'w').close()
        
        logfile(filename=lfname, start=True)
        main('*', '*', '*', '*', '', 'long', tstat='FILE')
        logfile(stop=True)
        
        x = ''.join(contents('%s/tpb@mailinator.com' % testdir))
        for name in application_required_files():
            assert(('%s is empty' % name) in x)
            assert(('%s : not gW' % name) in x)

    # -----------------------------------------------------------------------
    def test_app_req_missing(self):
        '''
        trigger messages "<filename> is missing" for each file in
        application_required_files() list.
        '''
        prepare_tests()
        lfname = sys._getframe().f_code.co_name.replace('test_', '') + '.log'
        write_sw_config(swroot=testdir)

        writefile('%s/.owner' % testbuild, ['tpb'])
        paths = ['%s/%s' % (testapp, name)
                 for name in application_required_files()]
        for fpath in paths:
            safe_unlink(fpath)
        
        logfile(filename=lfname, start=True)
        main('*', '*', '*', '*', '', 'long', tstat='FILE')
        logfile(stop=True)
        
        x = ''.join(contents('%s/tpb@mailinator.com' % testdir))
        for name in application_required_files():
            assert(('%s is missing' % name) in x)
        
    # -----------------------------------------------------------------------
    def test_app_single_owner_perm(self):
        '''
        .owner exists but not accessible => "can't open .owner" at app level
        '''
        prepare_tests()
        lfname = sys._getframe().f_code.co_name.replace('test_', '') + '.log'
        write_sw_config(swroot=testdir)
        filename = '%s/.owner' % testapp
        safe_unlink([x % testapp for x in ['%s/.owner', '%s/.owners']])
        writefile(filename, ['tpb'])
        os.chmod(filename, 0222)

        logfile(filename=lfname, start=True)
        main('*', '*', '*', '*', '', 'long', tstat='FILE')
        logfile(stop=True)

        x = ''.join(contents('%s/tpb@mailinator.com' % testdir))
        assert(("\n%16scan't open .owner\n" % ' ') in x)
        
    # -----------------------------------------------------------------------
    def test_arch_perms(self):
        '''
        In main(), check perms on arch directory.
        '''
        prepare_tests()
        lfname = sys._getframe().f_code.co_name.replace('test_', '') + '.log'
        write_sw_config(swroot=testdir)

        writefile('%s/.owner' % testbuild, ['tpb'])
        writefile('%s/support' % testapp, ['vendor'])
        os.chmod('%s/bgp' % testdir, 0733)
        os.chmod('%s/xt5' % testdir, 0755)
        
        logfile(filename=lfname, start=True)
        main('*', '*', '*', '*', '', 'long', tstat='FILE')
        logfile(stop=True)
        # restore_sw_config()
        
        x = ''.join(contents('%s/tbarron@mailinator.com' % testdir))
        sp16 = '                '
        assert('/xt5 : not gW \n' in x)
        assert('/bgp : not gR not oR oW' in x)
        
    # -----------------------------------------------------------------------
    def test_arch_all(self):
        '''
        In main(), test passing 'all' for architecture
        '''
        prepare_tests()
        lfname = sys._getframe().f_code.co_name.replace('test_', '') + '.log'
        write_sw_config(swroot=testdir)

        writefile('%s/.owner' % testbuild, ['tpb'])
        writefile('%s/support' % testapp, ['vendor'])
        os.chmod('%s/bgp' % testdir, 0733)
        os.chmod('%s/xt5' % testdir, 0755)
        
        logfile(filename=lfname, start=True)
        main('all', '*', '*', '*', '', 'long', tstat='FILE')
        logfile(stop=True)
        # restore_sw_config()
        
        x = ''.join(contents('%s/tbarron@mailinator.com' % testdir))
        sp16 = '                '
        assert('/xt5 : not gW \n' in x)
        assert('/bgp : not gR not oR oW' in x)
        assert('/ewok (swmeister)' in x)
        assert('/analysis-x64 (swmeister)' in x)
        assert('/smoky (swmeister)' in x)
        assert('/scibox (swmeister)' in x)

    # -----------------------------------------------------------------------
    def test_build_exit3(self):
        '''
        Trigger message "rebuild contains an exit 3" in build directory.
        '''
        prepare_tests()
        lfname = sys._getframe().f_code.co_name.replace('test_', '') + '.log'
        write_sw_config(swroot=testdir)
        # os.system('ls sw_config*')
        writefile('%s/.owner' % testbuild, ['tpb'])
        writefile('%s/support' % testapp, ['unsupported'])
        writefile('%s/dependencies' % testbuild, [])
        writefile('%s/rebuild' % testbuild, ['# this is a test\n',
                                             'exit 3\n'])
        safe_unlink('%s/relink' % testbuild)
            
        logfile(filename=lfname, start=True)
        main('xt5', 'testapp', '*', '*', '', 'long', tstat='FILE')
        logfile(stop=True)
        # restore_sw_config()
        
        x = ''.join(contents('%s/tbarron@mailinator.com' % testdir))
        assert('\n%32srebuild contains an exit 3' % ' ' in x)
        assert('\n%32srelink is missing' % ' ' in x)

    # -----------------------------------------------------------------------
    def test_build_lockfile(self):
        '''
        Trigger message "Lockfile present" in build directory.
        '''
        prepare_tests()
        lfname = sys._getframe().f_code.co_name.replace('test_', '') + '.log'
        write_sw_config(swroot=testdir)
        writefile('%s/.owner' % testbuild, ['tpb'])
        writefile('%s/support' % testapp, ['unsupported'])
        writefile('%s/dependencies' % testbuild, [])
        writefile('%s/.lock' % testbuild, [])
        safe_unlink('%s/relink' % testbuild)
            
        logfile(filename=lfname, start=True)
        main('xt5', 'testapp', '*', '*', '', 'long', tstat='FILE')
        logfile(stop=True)
        
        x = ''.join(contents('%s/tbarron@mailinator.com' % testdir))
        assert('\n%32sLockfile present' % ' ' in x)
        assert('\n%32srelink is missing' % ' ' in x)

    # -----------------------------------------------------------------------
    def test_build_no_ownerfiles(self):
        '''
        .owner, .owners don't exist at build level => "can't open
        .owner"
        '''
        prepare_tests()
        lfname = sys._getframe().f_code.co_name.replace('test_', '') + '.log'
        write_sw_config(swroot=testdir)
        
        [sfile, pfile] = [x % testbuild for x in ['%s/.owner', '%s/.owners']]
        safe_unlink([sfile, pfile])

        logfile(filename=lfname, start=True)
        main('*', '*', '*', '*', '', 'long', tstat='FILE')
        logfile(stop=True)

        x = ''.join(contents('%s/tbarron@mailinator.com' % testdir))
        assert(("\n%32scan't open .owner\n" % ' ') in x)
        
    # -----------------------------------------------------------------------
    def test_build_plural_owners_perm(self):
        '''
        .owners exists but not accessible => "can't open .owners" at build
        level
        '''
        prepare_tests()
        lfname = sys._getframe().f_code.co_name.replace('test_', '') + '.log'
        write_sw_config(swroot=testdir)
        
        [sfile, pfile] = [x % testbuild for x in ['%s/.owner', '%s/.owners']]
        safe_unlink([sfile, pfile])
        writefile(pfile, '[xyzzy]')
        os.chmod(pfile, 0222)
        
        logfile(filename=lfname, start=True)
        main('*', '*', '*', '*', '', 'long', tstat='FILE')
        logfile(stop=True)

        x = ''.join(contents('%s/tbarron@mailinator.com' % testdir))
        assert(("\n%32scan't open .owner\n" % ' ') not in x)
        assert(("\n%32scan't open .owners\n" % ' ') in x)

    # -----------------------------------------------------------------------
    def test_build_recurse(self):
        '''
        trigger message "Lockfile present" in build
        '''
        prepare_tests()
        lfname = sys._getframe().f_code.co_name.replace('test_', '') + '.log'
        write_sw_config(swroot=testdir)
        writefile('%s/.owner' % testbuild, ['tpb'])

        playdir = '%s/gromacs3.1/epsilon' % testbuild
        if not os.path.exists(playdir):
            os.makedirs(playdir)
        permfile('%s/notgR' % playdir, 0735)
        permfile('%s/notgW' % playdir, 0755)
        permfile('%s/notoR' % playdir, 0773)
        permfile('%s/oW'    % playdir, 0777)
        
        logfile(filename=lfname, start=True)
        main('xt5', 'testapp', '*', '*', 'recurse', 'long', tstat='FILE')
        logfile(stop=True)
        
        x = ''.join(contents('%s/tbarron@mailinator.com' % testdir))
        # lead = '%36s' % ' '
        assert('\n%36snotgR : not gR' % ' ' in x)
        assert('\n%36snotgW : not gW' % ' ' in x)
        assert('\n%36snotoR : not oR' % ' ' in x)
        assert('\n%36soW : oW' % ' ' in x)

    # -----------------------------------------------------------------------
    def test_build_single_owner_perm(self):
        '''
        .owner exists but not accessible => "can't open .owner" at build
        level
        '''
        prepare_tests()
        lfname = sys._getframe().f_code.co_name.replace('test_', '') + '.log'
        write_sw_config(swroot=testdir)
        
        [sfile, pfile] = [x % testbuild for x in ['%s/.owner', '%s/.owners']]
        safe_unlink([sfile, pfile])
        writefile(sfile, '[xyzzy]')
        os.chmod(sfile, 0222)

        logfile(filename=lfname, start=True)
        main('*', '*', '*', '*', '', 'long', tstat='FILE')
        logfile(stop=True)

        x = ''.join(contents('%s/tbarron@mailinator.com' % testdir))
        assert(("\n%32scan't open .owner\n" % ' ') in x)
        assert(("\n%32scan't open .owners\n" % ' ') not in x)

    # -----------------------------------------------------------------------
    def test_buildfile_perms(self):
        '''
        trigger permission messages for files in build
        '''
        prepare_tests()
        lfname = sys._getframe().f_code.co_name.replace('test_', '') + '.log'
        write_sw_config(swroot=testdir)
        writefile('%s/.owner' % testbuild, ['tpb'])
        writefile('%s/support' % testapp, ['unsupported'])
        writefile('%s/dependencies' % testbuild, [])
        writefile('%s/rebuild' % testbuild, ['# this is a test'])

        os.chmod('%s/rebuild' % testbuild, 0333)

        logfile(filename=lfname, start=True)
        main('xt5', 'testapp', '*', '*', '', 'long', tstat='FILE')
        logfile(stop=True)
        
        x = ''.join(contents('%s/tbarron@mailinator.com' % testdir))
        sp32 = '%32s' % ' '
        assert('\n%sdependencies : not gW' % sp32 in x)
        assert('\n%srebuild could not be opened' % sp32 in x)
        safe_unlink('%s/rebuild' % testbuild)

    # -----------------------------------------------------------------------
    def test_desc_unchanged(self):
        '''
        trigger message "description is unchanged from the template"
        '''
        prepare_tests()
        lfname = sys._getframe().f_code.co_name.replace('test_', '') + '.log'
        write_sw_config(swroot=testdir)

        safe_unlink('%s/.owner' % testbuild)
        writefile('%s/.owner' % testbuild, ['tpb'])
        os.system('cp %s/description %s' % (template_directory(), testapp))
        logfile(filename=lfname, start=True)
        main('*', '*', '*', '*', '', 'long', tstat='FILE')
        logfile(stop=True)

        x = ''.join(contents('%s/tbarron@mailinator.com' % testdir))
        assert('description is unchanged from the template' in x)
        assert(('/1.0 (tpb)\n%24snot gW' % ' ') in x)
        
    # -----------------------------------------------------------------------
    def test_invalid_arch(self):
        '''
        Trigger message "invalid architecture".
        '''
        prepare_tests()
        lfname = sys._getframe().f_code.co_name.replace('test_', '') + '.log'
        logfile(filename=lfname, start=True)
        try:
            main('nosucharch', '*', '*', '*', '', 'long', tstat='FILE')
        except SystemExit, e:
            logfile(stop=True)
            assert(str(e) == '2')
        logfile(stop=True)
        expected = ['  error:  invalid architecture  \n']
        got = contents(lfname)
        try:
            assert(got == expected)
        except AssertionError, e:
            print "got '%s'" % got
            print "expected '%s'" % expected
            raise e

    # -----------------------------------------------------------------------
    def test_invalid_arch_def(self):
        '''
        trigger message "invalid architectures defined in sw_config"
        '''
        write_sw_config(swroot=testdir, machines='zebedee:matterhorn')

        lfname = sys._getframe().f_code.co_name.replace('test_', '') + '.log'
        logfile(filename=lfname, start=True)
        try:
            main('*', '*', '*', '*', '', 'long', tstat='FILE')
        except SystemExit, e:
            logfile(stop=True)
            assert(str(e) == '2')
        logfile(stop=True)

        expected = ['  error:  invalid architectures defined'
                    + ' in sw_config (matterhorn)  \n']
        got = contents(lfname)
        expectVSgot(expected, got)

    # -----------------------------------------------------------------------
#     def test_missing_gXoX(self):
#         '''
#         In handle_application(), trigger 'is missing either gX or oX'

#         This error is difficult to trigger because it reports a
#         situation where some component of the path above the leaf is
#         unscannable. But if a path component is unscannable, the
#         script can't get past it to ask about items at a lower level.
#         Thus, by the time this message would be triggered, the script
#         has already stumbled on the offending directory as a leaf
#         rather than as an internal path component.
#         '''
#         prepare_tests()
#         lfname = sys._getframe().f_code.co_name.replace('test_', '') + '.log'
#         write_sw_config(swroot=testdir)

#         writefile('%s/.owner' % testbuild, ['tpb'])
#         writefile('%s/support' % testapp, ['vendor'])

#         try:
#             os.symlink('%s/1.0/nothingthere' % testapp,
#                        '%s/1.0/danglink' % testapp)
#         except OSError, e:
#             if 'File exists' not in str(e):
#                 raise e

        
#         logfile(filename=lfname, start=True)
#         os.chmod(testdir, 0600)
#         main('xt5', 'testapp', '1.0', '*', '', 'long', tstat='FILE')
#         logfile(stop=True)

#         os.chmod(testdir, 0755)
        
#         x = ''.join(contents('%s/tbarron@mailinator.com' % testdir))
#         assert('is missing either gX or oX' in x)

    # -----------------------------------------------------------------------
    def test_module_folder_missing(self):
        '''
        Report should show that module folder is  missing.
        '''
        prepare_tests()
        lfname = sys._getframe().f_code.co_name.replace('test_', '') + '.log'
        write_sw_config(swroot=testdir)

        writefile('%s/.owner' % testbuild, ['tpb'])
        writefile('%s/support' % testapp, ['nccs'])
        
        logfile(filename=lfname, start=True)
        main('*', '*', '*', '*', '', 'long', tstat='FILE')
        logfile(stop=True)
        
        x = ''.join(contents('%s/tpb@mailinator.com' % testdir))
        assert('no modulefiles folder' in x)
        assert('version does not have modulefile' in x)
        
    # -----------------------------------------------------------------------
    def test_no_next_check(self):
        '''
        Report should show "no next check" message.

        This test verifies the amount of indentation at the beginning
        of the error message.
        '''
        prepare_tests()
        lfname = sys._getframe().f_code.co_name.replace('test_', '') + '.log'
        write_sw_config(swroot=testdir)

        writefile('%s/.owner' % testbuild, ['tpb'])
        writefile('%s/support' % testapp, ['nccs'])
        writefile('%s/.check4newver' % testapp,
                  ['2008-09-23: new version installed\n'])
        
        logfile(filename=lfname, start=True)
        main('*', '*', '*', '*', '', 'long', tstat='FILE')
        logfile(stop=True)
        
        x = ''.join(contents('%s/tpb@mailinator.com' % testdir))
        assert('\n%16s.check4newver: no "next check" in last line' % ' ' in x)
        
    # -----------------------------------------------------------------------
    def test_out_of_date(self):
        '''
        Report should show that app is out of date.
        '''
        prepare_tests()
        lfname = sys._getframe().f_code.co_name.replace('test_', '') + '.log'
        write_sw_config(swroot=testdir)

        writefile('%s/.owner' % testbuild, ['tpb'])
        writefile('%s/support' % testapp, ['nccs'])
        writefile('%s/.check4newver' % testapp,
                  ['2008-09-23: new version installed\n',
                   '2008-09-23: next check of /sw/xt5/swig on 2008-12-22\n'])
        
        logfile(filename=lfname, start=True)
        main('*', '*', '*', '*', '', 'long', tstat='FILE')
        logfile(stop=True)
        
        x = ''.join(contents('%s/tpb@mailinator.com' % testdir))
        assert('\n%16sthis software is out of date' % ' ' in x)
        
    # -----------------------------------------------------------------------
    def test_swmeister_extra_arch(self):
        '''
        Report for swmeister should not show extra indented arch.
        '''
        prepare_tests()
        lfname = sys._getframe().f_code.co_name.replace('test_', '') + '.log'
        write_sw_config(swroot=testdir)

        os.chmod('%s/xt5' % testdir, 0775)

        logfile(filename=lfname, start=True)
        main('*', '*', '*', '*', '', 'long', tstat='FILE')
        logfile(stop=True)

        x = ''.join(contents('%s/tbarron@mailinator.com' % testdir))
        assert('\n/xt' in x)
        assert('\n%8s/xt' % ' ' not in x)
        
# ---------------------------------------------------------------------------
class RCD_Test_Message(unittest.TestCase):
    '''
    Tests for the Message class.
    '''
    # -----------------------------------------------------------------------
    def test_add(self):
        '''
        Test routine Message.add().
        '''
        m = Message('swmeister')
        domain = default_domain()
        assert(m.recipient == ('tbarron@%s' % domain))
        assert(m.body == '')

        m.add('this is a test message')
        
        assert(m.body == 'this is a test message')
        
    # -----------------------------------------------------------------------
    def test_empty_sendable(self):
        '''
        Ask Message to generate an empty sendable.
        
        Expected result: the python value None
        '''
        m = Message('swmeister')
        domain = default_domain()
        s = m.sendable()
        assert(s == None)

    # -----------------------------------------------------------------------
    def test_fromaddr(self):
        '''
        Message.fromaddr() should generate a standard no reply address.
        '''
        m = Message('swmeister')
        assert(m.fromaddr() == 'swadm-no-reply@ccs.ornl.gov')
        
    # -----------------------------------------------------------------------
    def test_full_sendable(self):
        '''
        Ask Message to generate a sendable with something in it.
        '''
        m = Message('swmeister')
        domain = default_domain()
        m.add('this is a test message')
        s = m.sendable()
        expected = ''.join(['From: swadm-no-reply@ccs.ornl.gov\r\n',
                            'To: tbarron@%s\r\n' % domain,
                            'Subject: SW Conformance Report\r\n\r\n',
                            'this is a test message'])
        assert(s == expected)
        
    # -----------------------------------------------------------------------
    def test_to_emailaddr(self):
        '''
        If tstatus() does not return 'LIVE', we use mailinator addresses.
        '''
        m = Message('fontana@silvercreek.org')
        domain = default_domain()
        if tstatus() != 'LIVE':
            assert(m.recipient == 'fontana@mailinator.com')
        else:
            assert(m.recipient == 'fontana@silvercreek.org')
        
    # -----------------------------------------------------------------------
    def test_to_nameonly(self):
        '''
        Generate a message with just a to address and verify it.
        '''
        m = Message('sinbad')
        domain = default_domain()
        assert(m.recipient == ('sinbad@%s' % domain))
        assert(m.body == '')
        
    # -----------------------------------------------------------------------
    def test_to_swmeister(self):
        '''
        Generate a message to the swmeister and verify its empty body.
        '''
        m = Message('swmeister')
        domain = default_domain()
        assert(m.recipient == ('tbarron@%s' % domain))
        assert(m.body == '')
        
    # -----------------------------------------------------------------------
    def test_toaddr(self):
        '''
        Generate a message to the swmeister and verify its to address.
        '''
        m = Message('swmeister')
        domain = default_domain()
        assert(m.toaddr() == ('tbarron@%s' % domain))
        
# ---------------------------------------------------------------------------
class RCD_Test_OutOfDate(unittest.TestCase):
    '''
    Tests for the out_of_date() routine.
    '''
    # -----------------------------------------------------------------------
    def test_nccs_no_next_check(self):
        '''
        Simulate an app with 'nccs' support status that is out of date.
        '''
        prepare_tests()

        f = open(checkfile, 'w')
        f.write('2008-09-23: new version installed\n')
        # f.write('2008-09-23: next check of /sw/xt5/swig on 2008-12-22\n')
        f.close()

        r = Report(testdir, 'test')
        rv = out_of_date(testdir, 'nccs', r)

        assert(rv == None)
        # assert('this software is out of date' in r.specific)
        assert('.check4newver: no "next check" in last line'
               in r.specific)
        assert(r.path == testdir)
        assert(r.type == 'test')
        assert(r.reportable == True)
        assert(r.recipients == [])
        assert(r.subreports == [])
        
    # -----------------------------------------------------------------------
    def test_nccs_out_of_date(self):
        '''
        Simulate an app with 'nccs' support status that is out of date.
        '''
        prepare_tests()

        f = open(checkfile, 'w')
        f.write('2008-09-23: new version installed\n')
        f.write('2008-09-23: next check of /sw/xt5/swig on 2008-12-22\n')
        f.close()

        r = Report(testdir, 'test')
        rv = out_of_date(testdir, 'nccs', r)

        assert(rv == None)
        assert('this software is out of date' in r.specific)
        assert(r.path == testdir)
        assert(r.type == 'test')
        assert(r.reportable == True)
        assert(r.recipients == [])
        assert(r.subreports == [])
        
    # -----------------------------------------------------------------------
    def test_nccs_vendor_in_date(self):
        '''
        Simulate an app with 'nccs+vendor' support status that is
        not out of date.
        '''
        prepare_tests()

        f = open(checkfile, 'w')
        yesterday = time.strftime('%Y-%m-%d',
                                  time.localtime(time.time() - 86400))
        future = time.strftime('%Y-%m-%d',
                               time.localtime(time.time() + 90*86400))
        f.write('%s: new version installed' % yesterday)
        f.write('%s: next check of /sw/xt5/swig on %s' % (yesterday, future))
        f.close()

        r = Report(testdir, 'test')
        rv = out_of_date(testdir, 'nccs+vendor', r)

        assert(rv == None)
        assert(r.specific == [])
        assert(r.path == testdir)
        assert(r.type == 'test')
        assert(r.reportable == False)
        assert(r.recipients == [])
        assert(r.subreports == [])

    # -----------------------------------------------------------------------
    def test_unsupported_empty(self):
        '''
        Simulate an app with 'unsupported' support status and empty
        .check4newver file.
        '''
        prepare_tests()
        safe_unlink(checkfile)
        open(checkfile, 'w').close()

        r = Report(testdir, 'test')
        rv = out_of_date(testdir, 'unsupported', r)

        assert(rv == None)
        assert('error: %s/.check4newver is empty or cannot be read' % testdir \
               in r.specific)
        assert('.check4newver: no "next check" in last line' \
               in r.specific)
        assert(r.path == testdir)
        assert(r.type == 'test')
        assert(r.reportable == True)
        assert(r.recipients == [])
        assert(r.subreports == [])

    # -----------------------------------------------------------------------
    def test_unsupported_missing(self):
        '''
        Simulate an app with 'unsupported' support status and missing
        .check4newver file.
        '''
        prepare_tests()
        safe_unlink(checkfile)

        r = Report(testdir, 'test')
        rv = out_of_date(testdir, 'unsupported', r)

        assert(rv == None)
        assert(r.path == testdir)
        assert(r.type == 'test')
        assert(r.reportable == True)
        assert(r.recipients == [])
        assert(r.subreports == [])
        assert('error: %s/.check4newver is empty or cannot be read' % testdir \
               in r.specific)
        assert('.check4newver: no "next check" in last line' \
               in r.specific)
        
    # -----------------------------------------------------------------------
    def test_vendor_only(self):
        '''
        Apps with only 'vendor' support status cannot get out of date.
        '''
        prepare_tests()
            
        r = Report(testdir, 'test')
        rv = out_of_date(testdir, 'vendor', r)
        s = r.write()
        assert(s == '')     # not reportable
        assert(rv == False)
        assert(r.path == testdir)
        assert(r.type == 'test')
        assert(r.reportable == False)
        assert(r.recipients == [])
        assert(r.subreports == [])
        
# ---------------------------------------------------------------------------
class RCD_Test_ReadSupportfile(unittest.TestCase):
    '''
    Various tests of the read_supportfile() routine.
    '''
    # -----------------------------------------------------------------------
    def test_supportfile_badperm(self):
        '''
        Test read_supportfile() on a file we don't have permission to read.
        '''
        prepare_tests()

        f = open(supportfile, 'w')
        f.write('nccs')
        f.close()

        os.chmod(supportfile, 0)
        
        r = read_supportfile(testdir)
        assert(r == 'support file cannot be read')
        os.unlink(supportfile)
        
    # -----------------------------------------------------------------------
    def test_supportfile_empty(self):
        '''
        Test read_supportfile() on an empty input file.
        '''
        prepare_tests()

        open(supportfile, 'w').close()

        r = read_supportfile(testdir)
        assert(r == 'support file cannot be read')

    # -----------------------------------------------------------------------
    def test_supportfile_missing(self):
        '''
        Test read_supportfile() on a nonexistent input file.
        '''
        prepare_tests()
        safe_unlink(supportfile)

        r = read_supportfile(testdir)
        assert(r == 'support file cannot be read')
    
    # -----------------------------------------------------------------------
    def test_supportfile_nolinefeed(self):
        '''
        Test read_supportfile() on an input file with no line terminator.
        '''
        prepare_tests()

        f = open(supportfile, 'w')
        f.write('nccs')
        f.close()

        r = read_supportfile(testdir)
        assert(r == 'nccs')
    
    # -----------------------------------------------------------------------
    def test_supportfile_readable(self):
        '''
        Test read_supportfile() on a 'typical' input file.
        '''
        prepare_tests()

        f = open(supportfile, 'w')
        f.write('nccs\n')
        f.close()

        r = read_supportfile(testdir)
        assert(r == 'nccs')
    
# ---------------------------------------------------------------------------
class RCD_Test_Report(unittest.TestCase):
    '''
    Various tests of the Report class.
    '''
    # -----------------------------------------------------------------------
    def test_add_subreport(self):
        '''
        Test routine Report.add_subreport().
        '''
        r = Report(path=testapp, type='app')
        assert(r.subreports == [])
        v = Report(path='%s/1.0', type='version')
        r.add_subreport(v)
        assert(v in r.subreports)

    # -----------------------------------------------------------------------
    def test_buffer(self):
        '''
        Test routine Report.buffer().
        '''
        r = Report(path=testapp, type='app')
        assert(r.specific == [])
        r.buffer('This is a test of the Report class')
        assert(r.specific == ['This is a test of the Report class'])
        r.buffer('This is the second line')
        assert(r.specific == ['This is a test of the Report class',
                              'This is the second line'])

    # -----------------------------------------------------------------------
    def test_child_reportable(self):
        '''
        Test routine Report.child_reportable().
        '''
        r = Report(testapp, 'app')
        v = Report('%s/1.0' % testapp, 'version')
        b = Report('%s/1.0/cnl2.2_gnu4.2.4' % testapp, 'build')
        v.add_subreport(b)
        r.add_subreport(v)
        b.buffer("can't open ownerfile")
        b.make_reportable()
        assert(r.child_reportable())

    # -----------------------------------------------------------------------
    def test_compose_arptble(self):
        '''
        Test Report.compose() for a reportable app.
        '''
        r = Report(testapp, 'app')
        v = Report('%s/1.0' % testapp, 'version')
        b = Report('%s/1.0/cnl2.2_gnu4.2.4' % testapp, 'build')
        v.add_subreport(b)
        r.add_subreport(v)
        r.buffer('description is unchanged from the template')
        r.make_reportable()
        s = r.compose()
        expected = ('/testapp ()\n'
                    + '        description is unchanged from the template\n')
        assert(s == expected)

    # -----------------------------------------------------------------------
    def test_compose_brptble(self):
        '''
        Test Report.compose() for a reportable build.
        '''
        r = Report(testapp, 'app')
        v = Report('%s/1.0' % testapp, 'version')
        b = Report('%s/1.0/cnl2.2_gnu4.2.4' % testapp, 'build')
        v.add_subreport(b)
        r.add_subreport(v)
        b.buffer("can't open ownerfile")
        b.make_reportable()
        s = r.compose()
        expected = ('/testapp ()\n'
                    + '        /1.0 ()\n'
                    + '                /cnl2.2_gnu4.2.4 ()\n'
                    + "                        can't open ownerfile\n")
        assert(s == expected)

    # -----------------------------------------------------------------------
    def test_compose_vrptble(self):
        '''
        Test Report.compose() for a reportable version.
        '''
        r = Report(testapp, 'app')
        v = Report('%s/1.0' % testapp, 'version')
        b = Report('%s/1.0/cnl2.2_gnu4.2.4' % testapp, 'build')
        v.add_subreport(b)
        r.add_subreport(v)
        v.buffer('version does not have modulefile')
        v.make_reportable()
        s = r.compose()
        expected = ('/testapp ()\n'
                    + '        /1.0 ()\n'
                    + '                version does not have modulefile\n')
        assert(s == expected)

    # -----------------------------------------------------------------------
    def test_header(self):
        '''
        Test Report.header().
        '''
        r = Report(testapp, 'app')
        r.buffer('support = whatever')
        r.buffer('another item')
        r.buffer('yet another item')
        got = r.header()
        expected = ('%s/xt5/testapp' % testdir)
        try:
            assert(got == expected)
        except AssertionError, e:
            print "expected '%s'" % expected
            print "got '%s'" % got
            raise e
        
    # -----------------------------------------------------------------------
    def test_init_00(self):
        '''
        Test Report constructor called with no path or type.

        It should throw an exception.
        '''
        success = False
        try:
            r = Report()
        except Exception, e:
            assert(str(e) == 'Report path must be specified at creation')
            success = True
        assert(success)

    # -----------------------------------------------------------------------
    def test_init_01(self):
        '''
        Test Report constructor called with a type but no path.

        It should throw an exception.
        '''
        success = False
        try:
            r = Report(type='build')
        except Exception, e:
            assert(str(e) == 'Report path must be specified at creation')
            success = True
        assert(success)

    # -----------------------------------------------------------------------
    def test_init_10(self):
        '''
        Test Report constructor called with path but no type.

        It should throw an exception.
        '''
        success = False
        try:
            r = Report(path=testapp)
        except Exception, e:
            assert(str(e) == 'Report type must be specified at creation')
            success = True
        assert(success)

    # -----------------------------------------------------------------------
    def test_init_11(self):
        '''
        Test Report constructor called with both type and path.

        It should return an object with no exceptions.
        '''
        success = True
        try:
            r = Report(path=testapp, type='build')
        except Exception, e:
            success = False
        assert(success)
        assert(r.path == testapp)
        assert(r.type == 'build')
        assert(r.specific == [])
        assert(r.recipients == [])
        assert(r.subreports == [])
        assert(r.reportable == False)
        
    # -----------------------------------------------------------------------
    def test_make_reportable(self):
        '''
        Test Report.make_reportable().
        '''
        r = Report(testapp, 'app')
        assert(r.reportable == False)
        r.make_reportable()
        assert(r.reportable == True)

    # -----------------------------------------------------------------------
    def test_recipient_list(self):
        '''
        Test Report.recipient_list().
        '''
        r = Report(path=testapp, type='app')
        r.target('alpha@olympus.org')
        v = Report(path='%s/1.0' % testapp, type='version')
        v.target('bucephalos@olympus.org')
        b = Report(path='%s/1.0/cnl2.2_gnu4.2.4' % testapp, type='build')
        b.target('lysistrata@attic.geo')
        assert(r.recipient_list() == ['alpha@olympus.org'])

    # -----------------------------------------------------------------------
    def test_recipients_str(self):
        '''
        Test Report.recipients_str().
        '''
        r = Report(path=testapp, type='app')
        r.target('alpha@olympus.org')
        v = Report(path='%s/1.0' % testapp, type='version')
        v.target('bucephalos@olympus.org')
        b = Report(path='%s/1.0/cnl2.2_gnu4.2.4' % testapp, type='build')
        b.target('lysistrata@attic.geo')
        assert(r.recipients_str() == 'alpha@olympus.org')

    # -----------------------------------------------------------------------
    def test_summarize_child_reportable(self):
        '''
        Test Report.summarize() for an object with a reportable child.
        '''
        r = Report(path=testapp, type='app')
        assert(r.subreports == [])
        v = Report(path='%s/1.0', type='version')
        r.add_subreport(v)
        assert(v in r.subreports)
        v.make_reportable()
        s = r.summarize()
        assert(s == '/testapp ()\n     /1.0 ()\n')

    # -----------------------------------------------------------------------
    def test_summarize_not_reportable(self):
        '''
        Test Report.summarize() for a non-reportable object.
        '''
        r = Report(path=testapp, type='app')
        assert(r.subreports == [])
        v = Report(path='%s/1.0', type='version')
        r.add_subreport(v)
        s = r.summarize()
        assert(s == '')

    # -----------------------------------------------------------------------
    def test_summarize_parent_reportable(self):
        '''
        Test Report.summarize() for a top level report with a non-reportable
        child.
        '''
        r = Report(path=testapp, type='app')
        assert(r.subreports == [])
        v = Report(path='%s/1.0', type='version')
        r.add_subreport(v)
        assert(v in r.subreports)
        r.make_reportable()
        s = r.summarize()
        assert(s == '/testapp ()\n')

    # -----------------------------------------------------------------------
    def test_target_list(self):
        '''
        Test Report.target().

        It should add listed recipients without adding duplicates.
        '''
        r = Report(testapp, 'app')
        r.target(['lucy@metropole.com', 'sally@peanuts.toon'])
        assert(r.recipients == ['lucy@metropole.com', 'sally@peanuts.toon'])
        r.target(['bozo@circus.org', 'lucy@metropole.com'])
        assert(r.recipients == ['lucy@metropole.com',
                                'sally@peanuts.toon',
                                'bozo@circus.org'])
        
    # -----------------------------------------------------------------------
    def test_target_other(self):
        '''
        Test Report.target() called with the wrong type of argument.

        It should throw an exception.
        '''
        r = Report(testapp, 'app')
        success = False
        try:
            r.target(25)
        except Exception, e:
            assert(str(e) == 'recip type must be list or string')
            success = True
        assert(success)

    # -----------------------------------------------------------------------
    def test_target_str(self):
        '''
        Test Report.target() called with a string.

        Verify that it does not store duplicates.
        '''
        r = Report(testapp, 'app')
        r.target('sam@gnoodle.org')
        assert(r.recipients == ['sam@gnoodle.org'])
        r.target('sam@gnoodle.org')
        assert(r.recipients == ['sam@gnoodle.org'])

    # -----------------------------------------------------------------------
    def test_write_child_reportable(self):
        '''
        Test Report.write() on a object with a reportable child.
        '''
        r = Report(path=testapp, type='app')
        assert(r.subreports == [])
        v = Report(path='%s/1.0', type='version')
        r.add_subreport(v)
        assert(v in r.subreports)
        v.make_reportable()
        s = r.write()
        assert(s == '/testapp ()\n        /1.0 ()\n')

    # -----------------------------------------------------------------------
    def test_write_not_reportable(self):
        '''
        Test Report.write() on an non-reportable object.
        '''
        r = Report(path=testapp, type='app')
        assert(r.subreports == [])
        v = Report(path='%s/1.0', type='version')
        r.add_subreport(v)
        s = r.write()
        assert(s == '')

    # -----------------------------------------------------------------------
    def test_write_parent_reportable(self):
        '''
        Test Report.write() with only the top level being reportable.
        '''
        r = Report(path=testapp, type='app')
        assert(r.subreports == [])
        v = Report(path='%s/1.0', type='version')
        r.add_subreport(v)
        assert(v in r.subreports)
        r.make_reportable()
        s = r.write()
        assert(s == '/testapp ()\n')

# ---------------------------------------------------------------------------
class RCD_Test_ValidateOwnerFile(unittest.TestCase):
    '''
    Tests for routine validate_owner_file().
    '''
    # -----------------------------------------------------------------------
    def test_app_both_00(self):
        '''
        Test routine validate_owner_file() with no owner files in place.
        In this test, they are not required.
        '''
        prepare_tests()
        [sfile, pfile] = [x % testapp for x in ['%s/.owner', '%s/.owners']]
        safe_unlink([sfile, pfile])
        writefile(sfile, ['psmith'])
        writefile(pfile, ['oral'])
        os.chmod(sfile, 0222)
        os.chmod(pfile, 0222)
        rv = validate_owner_file(testapp, required=False)
        expectVSgot(["can't open .owner", "can't open .owners"], rv)
        
    # -----------------------------------------------------------------------
    def test_app_both_01(self):
        '''
        Test routine validate_owner_file() with both files in place
        but the singular file unreadable. The owner files are not
        required. The result should be a complaint about the singular
        file.
        '''
        prepare_tests()
        [sfile, pfile] = [x % testapp for x in ['%s/.owner', '%s/.owners']]
        safe_unlink([sfile, pfile])
        writefile(sfile, ['psmith'])
        writefile(pfile, ['oral'])
        os.chmod(sfile, 0222)
        rv = validate_owner_file(testapp, required=False)
        expectVSgot(["can't open .owner"], rv)
        
    # -----------------------------------------------------------------------
    def test_app_both_10(self):
        '''
        Test routine validate_owner_file() with both files in place
        but the plural file unreadable due to permissions. The owner
        files are not required. The result should be a complaint about
        the plural file.
        '''
        prepare_tests()
        [sfile, pfile] = [x % testapp for x in ['%s/.owner', '%s/.owners']]
        safe_unlink([sfile, pfile])
        writefile(sfile, ['psmith'])
        writefile(pfile, ['oral'])
        os.chmod(pfile, 0222)
        rv = validate_owner_file(testapp, required=False)
        expectVSgot(["can't open .owners"], rv)
        
    # -----------------------------------------------------------------------
    def test_app_both_11(self):
        '''
        Test routine validate_owner_file() with both files in place
        and readable. The owner files are not required. The result
        should be no complaints.
        '''
        prepare_tests()
        [sfile, pfile] = [x % testapp for x in ['%s/.owner', '%s/.owners']]
        safe_unlink([sfile, pfile])
        writefile(sfile, ['psmith'])
        writefile(pfile, ['oral'])
        rv = validate_owner_file(testapp, required=False)
        expectVSgot([], rv)
        
    # -----------------------------------------------------------------------
    def test_app_no_owner_files(self):
        '''
        Test routine validate_owner_file() with neither file in place.
        When they are not required, the result should be no complaints.
        '''
        prepare_tests()
        [sfile, pfile] = [x % testapp for x in ['%s/.owner', '%s/.owners']]
        safe_unlink([sfile, pfile])
        rv = validate_owner_file(testapp, required=False)
        expectVSgot([], rv)
        
    # -----------------------------------------------------------------------
    def test_app_perms(self):
        '''
        Test validate_owner_file() with only the plural file in place
        but with the permissions set so that it is unreadable. The
        files are not required in this scenario. The result should be
        a complaint about not being able to open the file.
        '''
        prepare_tests()
        [sfile, pfile] = [x % testapp for x in ['%s/.owner', '%s/.owners']]
        safe_unlink([sfile, pfile])
        writefile(pfile, ['anderson'])
        os.chmod(pfile, 0222)
        rv = validate_owner_file(testapp, required=False)
        expectVSgot(["can't open .owners"], rv)
        
    # -----------------------------------------------------------------------
    def test_app_plural(self):
        '''
        Test validate_owner_file() with only the plural file in place
        in a directory where owner files are not required. Result
        should be no complaint.
        '''
        prepare_tests()
        [sfile, pfile] = [x % testapp for x in ['%s/.owner', '%s/.owners']]
        safe_unlink([sfile, pfile])
        writefile(pfile, ['oral'])
        rv = validate_owner_file(testapp, required=False)
        expectVSgot([], rv)
        
    # -----------------------------------------------------------------------
    def test_app_singular(self):
        '''
        Test validate_owner_file() with only the singular file in
        place in a directory where owner files are not required.
        Result should be no complaint.
        '''
        prepare_tests()
        [sfile, pfile] = [x % testapp for x in ['%s/.owner', '%s/.owners']]
        safe_unlink([sfile, pfile])
        writefile(sfile, ['oral'])
        rv = validate_owner_file(testapp, required=False)
        expectVSgot([], rv)
        
    # -----------------------------------------------------------------------
    def test_app_singular_perm(self):
        '''
        Test validate_owner_file() with only the singular file in
        place, perms set to make it unreadable, and owner files not
        required. Result should be a complaint that we can not open
        the file.
        '''
        prepare_tests()
        [sfile, pfile] = [x % testapp for x in ['%s/.owner', '%s/.owners']]
        safe_unlink([sfile, pfile])
        writefile(sfile, ['oral'])
        os.chmod(sfile, 0222)
        rv = validate_owner_file(testapp, required=False)
        expectVSgot(["can't open .owner"], rv)
        
    # -----------------------------------------------------------------------
    def test_build_both_00(self):
        '''
        Test validate_owner_file() at the build level (owner files are
        required) with both files present and unreadable. Result
        should be a complaint about each file.
        '''
        prepare_tests()
        [sfile, pfile] = [x % testbuild for x in ['%s/.owner', '%s/.owners']]
        safe_unlink([sfile, pfile])
        writefile(sfile, ['johnson'])
        writefile(pfile, ['mcgillicudy'])
        os.chmod(pfile, 0222)
        os.chmod(sfile, 0222)
        rv = validate_owner_file(testbuild, required=True)
        expectVSgot(["can't open .owner", "can't open .owners"], rv)
        
    # -----------------------------------------------------------------------
    def test_build_both_01(self):
        '''
        Test validate_owner_file() at the build level (owner files
        required) with both files present and the singular file
        unreadable. Result should be a complaint about not being able
        to open the file.
        '''
        prepare_tests()
        [sfile, pfile] = [x % testbuild for x in ['%s/.owner', '%s/.owners']]
        safe_unlink([sfile, pfile])
        writefile(sfile, ['johnson'])
        writefile(pfile, ['mcgillicudy'])
        os.chmod(sfile, 0222)
        rv = validate_owner_file(testbuild, required=True)
        expectVSgot(["can't open .owner"], rv)
        
    # -----------------------------------------------------------------------
    def test_build_both_10(self):
        '''
        Test validate_owner_file() at the build level (owner files
        required) with both files present and the plural file
        unreadable. Result should a complaint about not being able to
        open the unreadable file.
        '''
        prepare_tests()
        [sfile, pfile] = [x % testbuild for x in ['%s/.owner', '%s/.owners']]
        safe_unlink([sfile, pfile])
        writefile(sfile, ['johnson'])
        writefile(pfile, ['mcgillicudy'])
        os.chmod(pfile, 0222)
        rv = validate_owner_file(testbuild, required=True)
        expectVSgot(["can't open .owners"], rv)
        
    # -----------------------------------------------------------------------
    def test_build_both_11(self):
        '''
        Test validate_owner_file() at the build level (owner files
        required) with both files present and readable. Result should
        be no complaints.
        '''
        prepare_tests()
        [sfile, pfile] = [x % testbuild for x in ['%s/.owner', '%s/.owners']]
        safe_unlink([sfile, pfile])
        writefile(sfile, ['johnson'])
        writefile(pfile, ['mcgillicudy'])
        rv = validate_owner_file(testbuild, required=True)
        expectVSgot([], rv)
        
    # -----------------------------------------------------------------------
    def test_build_no_owner_files(self):
        '''
        Test validate_owner_file() at the build level (owner files
        required) with no owner files in place. Result should be a
        complaint about not being able to open .owner.
        '''
        prepare_tests()
        [sfile, pfile] = [x % testbuild for x in ['%s/.owner', '%s/.owners']]
        safe_unlink([sfile, pfile])
        rv = validate_owner_file(testbuild, required=True)
        expectVSgot(["can't open .owner"], rv)
        
    # -----------------------------------------------------------------------
    def test_build_perms(self):
        '''
        Test validate_owner_file() at the build level (owner files
        required) with the singular file in place but unreadable.
        Result should be a complaint that .owner cannot be opened.
        '''
        prepare_tests()
        [sfile, pfile] = [x % testbuild for x in ['%s/.owner', '%s/.owners']]
        safe_unlink([sfile, pfile])
        writefile(sfile, ['johnson'])
        os.chmod(sfile, 0222)
        rv = validate_owner_file(testbuild, required=True)
        expectVSgot(["can't open .owner"], rv)
        
    # -----------------------------------------------------------------------
    def test_build_plural(self):
        '''
        Test validate_owner_file() at the build level (owner files
        required) with the plural file in place and readable. Result
        should be no complaints.
        '''
        prepare_tests()
        [sfile, pfile] = [x % testbuild for x in ['%s/.owner', '%s/.owners']]
        safe_unlink([sfile, pfile])
        writefile(pfile, ['johnson'])
        rv = validate_owner_file(testbuild, required=True)
        expectVSgot([], rv)
        
    # -----------------------------------------------------------------------
    def test_build_plural_perm(self):
        '''
        Test validate_owner_file() at the build level (owner files
        required) with only the plural file in place and unreadable.
        Resutl should be a complaint about not being able to open
        .owers.
        '''
        prepare_tests()
        [sfile, pfile] = [x % testbuild for x in ['%s/.owner', '%s/.owners']]
        safe_unlink([sfile, pfile])
        writefile(pfile, ['johnson'])
        os.chmod(pfile, 0222)
        rv = validate_owner_file(testbuild, required=True)
        expectVSgot(["can't open .owners"], rv)
        
    # -----------------------------------------------------------------------
    def test_build_singular(self):
        '''
        Test validate_owner_file() at the build level (owner files
        required) with only the singular file in place and readable.
        Result should be no complaint.
        '''
        prepare_tests()
        [sfile, pfile] = [x % testbuild for x in ['%s/.owner', '%s/.owners']]
        safe_unlink([sfile, pfile])
        writefile(sfile, ['johnson'])
        rv = validate_owner_file(testbuild, required=True)
        expectVSgot([], rv)
        
# ---------------------------------------------------------------------------
def all_tests():
    '''
    Return a list of all the tests available in this script.
    '''
    testclasses = []
    cases = []
    for item in dir(this):
        if item.startswith('RCD_Test_'):
            testclasses.append(item)
    for c in testclasses:
        cobj = globals()[c]
        for case in unittest.TestLoader().getTestCaseNames(cobj):
            cases.append('%s.%s' % (c, case))
    return cases

# ---------------------------------------------------------------------------
def cleanup_tests():
    '''
    Delete the test directory.
    '''
    rmf(testdir)
    
# ---------------------------------------------------------------------------
def safe_unlink(path):
    '''
    Unlink the files listed in path.

    The argument may be a string containing a single file path or a
    list containing many. The unlinks are done in such a way that no
    exceptions are raised for missing files.
    '''
    if type(path) == str:
        if os.path.exists(path):
            os.unlink(path)
    elif type(path) == list:
        for item in path:
            if os.path.exists(item):
                os.unlink(item)
    else:
        raise Exception('safe_unlink: argument must be str or list')
        
# ---------------------------------------------------------------------------
def expectVSgot(expected, got):
    '''
    Compare expected to got and report if they are different. If they
    are not different, this routine is silent.
    '''
    try:
        assert(expected == got)
    except AssertionError, e:
        print "EXPECTED '%s'" % expected
        print "GOT      '%s'" % got
        raise e
            
# ---------------------------------------------------------------------------
def list_tests(a, final, testlist):
    '''
    Display the list of tests in testlist or a, depending on their values.

    If a has one or fewer elements, print the list in testlist.
    Otherwise, print the list of tests in a[1:].
    '''
    if len(a) <= 1:
        for c in testlist:
            print c
            if final != '' and final in c:
                break
    else:
        for arg in a[1:]:
            for c in testlist:
                if arg in c:
                    print c
                if final != '' and final in c:
                    break
    
# ---------------------------------------------------------------------------
def logfile(filename='', start=False, stop=False):
    '''
    Start and stop logging and set the log file name.
    '''
    global loghandle
    global save_stdout
    global save_stderr

    if start and stop:
        raise Exception('logfile: start=True, stop=True incompatible')
    elif start and not stop and filename == '':
        raise Exception('must have filename to start logging')
    elif start and not stop and filename != '':
        save_stdout, save_stderr = sys.stdout, sys.stderr
        loghandle = open(filename, 'w')
        sys.stdout, sys.stderr = loghandle, loghandle
    elif not start and stop and filename == '':
        if loghandle == None:
            return
        if (save_stdout != None) and (save_stderr != None):
            sys.stdout, sys.stderr = save_stdout, save_stderr
        if loghandle != None:
            loghandle.close()
        save_stdout, save_stderr, loghandle = None, None, None
    elif not start and stop and filename != '':
        raise Exception('logfile: stop=True, filename != "" incompatible')
    elif not start and not stop:
        raise Exception('call logfile(start=True, filename=NAME)'
                       + ' to start logging')
    
# ---------------------------------------------------------------------------
def permfile(path, perms):
    '''
    Create file path with permissions perms.
    '''
    writefile(path, [])
    os.chmod(path, perms)
    
# ---------------------------------------------------------------------------
def prepare_tests():
    '''
    Get ready to run the tests.

    This routine is idempotent -- if the test environment is already
    set up, it does nothing.
    '''
    if not os.path.exists(testdir):
        os.makedirs(testdir)
        os.mkdir('%s/ewok' % testdir)
        os.mkdir('%s/analysis-x64' % testdir)
        os.mkdir('%s/smoky' % testdir)
        os.mkdir('%s/bgp' % testdir)
        os.mkdir('%s/scibox' % testdir)
        os.makedirs(testbuild)
    if not os.path.isdir(testdir):
        raise Exception('Cannot create directory %s' % testdir)
    swroot(set=True, value=testdir)
    os.environ['SW_ROOT'] = testdir
    if os.getcwd() != testdir:
        os.chdir(testdir)
        
# ---------------------------------------------------------------------------
def rmf(dirname):
    '''
    Do the equivalent of 'rm -rf' on dirname.

    That is, delete a tree from the file system.
    '''
    for root, dirs, files in os.walk(dirname, topdown=False):
        for name in files:
            os.unlink(os.path.join(root, name))
        for name in dirs:
            os.rmdir(os.path.join(root, name))
    if os.path.isdir(dirname):
        os.rmdir(dirname)
    
# ---------------------------------------------------------------------------
def run_tests(a, final, testlist):
    '''
    Run a set of tests based on the command line.
    '''
    if len(a) <= 1:
        # suite = unittest.TestLoader().loadTestsFromModule(this)
        suite = unittest.TestSuite()
        for c in testlist:
            s = unittest.TestLoader().loadTestsFromName(c, this)
            suite.addTest(s)
            if final != '' and final in c:
                break
    else:
        suite = unittest.TestSuite()
        for arg in a[1:]:
            for c in testlist:
                if arg in c:
                    s = unittest.TestLoader().loadTestsFromName(c, this)
                    suite.addTest(s)        
                if final != '' and final in c:
                    break
                
    unittest.TextTestRunner(verbosity=volume).run(suite)
    
# ---------------------------------------------------------------------------
def write_sw_config(swroot='', machines=''):
    '''
    Create the file sw_config in the test environment directory.
    '''
    if swroot == '':
        swroot = swroot()
    if machines == '':
        machines = ('jaguarpf-login:xt5,chester-login:xt5,jaguar:xt5'
                    + ',rizzo:xt5,ewok:ewok,lens:analysis-x64'
                    + ',everest:analysis-x64,smokylogin:smoky'
                    + ',eugene:bgp,fatman:scibox')
#    if not os.path.exists('sw_config.prod') and os.path.exists('sw_config'):
#        os.system('cp -p sw_config sw_config.prod')
    f = open('sw_config.test', 'w')
    f.writelines(['# SW TOOLS CONFIG FILE\n',
                  '# Version 1.0\n',
                  '# Generated by reportconformdist.py\n',
                  '\n',

                  '# NO TRAILING SLASHES on the directorys please\n',
                  '\n',
                  
                  '# General Settings\n',
                  '\n',
                  
                  'MACHINES=%s\n' % machines,
                  '# Valid tags for use with the versions files\n',
                  'VALID_VERSIONS=current,new,dev,old,dep\n',
                  'TEMPLATE_DIRECTORY=/sw/tools/templates\n',
                  'LOG_DIRECTORY=/sw/tools/logs\n',
                  'SOFTWARE_ROOT_DIRECTORY=%s\n' % swroot,
                  '\n',
                  '\n',
                  '\n',
                  
                  '# Addbuild / Addpackage settings\n',
                  '\n',
                  
                  '# The templates that will be copied along with the '
                  + 'corresponding octal permissions string\n',
                  'ADDPACKAGE_TEMPLATES=support:0664,description:0664'
                  + ',versions:0664,.exceptions:0644\n',
                  'ADDBUILD_TEMPLATES=relink:0774,rebuild:0774,retest:0774'
                  + ',status:0664,build-notes:0664,dependencies:0664\n',
                  'BUILDDIR_PERMISSIONS=775\n',
                  'APPDIR_PERMISSIONS=775\n',
                  '\n',
                  '\n',
                  '\n',
                  '\n',
                  
                  '# Duplicate Settings\n',
                  '\n',

                  '# Files to be modified when a duplicate is performed'
                  + ' and SW_ENVFILE is defined\n',
                  'DUPLICATE_MODIFIED_FILES=rebuild,retest,relink\n',
                  '\n',

                  '# Flags to signify what text should be replaced when'
                  + ' using SW_ENVFILE\n',
                  'DUPLICATE_MODIFY_START_FLAG=### Set Environment\n',
                  'DUPLICATE_MODIFY_END_FLAG=### End Environment\n',
                  '\n',
                  
                  '# The name of the environment variable that\n',
                  'DUPLICATE_ENVVAR=SW_MODFILE\n',
                  '\n',
                  '\n',
                  '\n',
                  '\n',
                  
                  '# Rebuild / Relink / Retest Settings\n',
                  'DEFAULT_UMASK=0002\n',
                  'REBUILD_RELINK_RETEST_WORK_ENVVAR'
                  + '=SW_WORKDIR\n',
                  '\n',
                  '\n',
                  '\n',
                  '\n',
                  
                  '# Version Settings\n',
                  '\n',
                  
                  '# Who should the emails come from?\n',
                  'FROM_FIELD = swadm@ornl.gov\n',
                  '\n',
                  
                  '# Report Settings\n',
                  '\n',
                  
                  '# We do not use architecture level exceptions\n',
                  '# This is because report will only do run on'
                  + ' architectures\n',
                  '# defined in MACHINES using the hostname:architecture'
                  + ' format\n',
                  '\n',
                  '\n',
                  
                  '# Directories to ignore at the application level\n',
                  'APPLICATION_LEVEL_EXCEPTIONS=modulefiles,modulefiles-unused'
                  + ',bin,etc,share,includ e,man,info,lib,acct,visit\n',
                  'VERSION_LEVEL_EXCEPTIONS=\n',
                  'BUILD_LEVEL_EXCEPTIONS=\n',
                  '\n',
                  '\n',
                  
                  '# Files to look for when running report conform\n',
                  'APPLICATION_REQUIRED_FILES=support,description'
                  + ',.check4newver,versions\n',
                  'BUILD_REQUIRED_FILES=relink,rebuild,retest,status'
                  + ',dependencies,.owners\n',
                  '\n',
                  
                  '# Files to check for "exit 3" in\n',
                  'BUILD_EXIT3_FILES=rebuild,relink,retest\n',
                  '\n',
                  '\n',
                  
                  '# Architectures to appear online\n',
                  'WEBARCHS=xt5,xt,bgp,analysis-x64,smoky\n',
                  'WEBHOME=/sw/tools/www\n',
                  '\n',
                  
                  '# The list of compilers for each machine for the website\n',
                  'COMPILERS=xt5:pgi,pathscale,gnu'
                  + ';xt:pgi,pathscale,gnu'
                  + ';ewok:pgi,pathscale,gnu,gcc'
                  + ';bgp:gnu,xl'
                  + ';analysis-x64:pgi,pathscale,gnu'
                  + ';smoky:pgi,pathscale,gnu\n',
                  ])
    f.close()
    os.system('mv sw_config.test sw_config')
 
# ---------------------------------------------------------------------------
def writefile(filepath, lines):
    '''
    Write lines to filepath.

    The first argument is a string containing a file path. The second
    argument is a list of lines to be written to the file. If line
    terminators are desired, they must already be in place at the end
    of each line in lines.
    '''
    f = open(filepath, 'w')
    f.writelines(lines)
    f.close()
    
# ---------------------------------------------------------------------------
if __name__ == '__main__':
    p = OptionParser()
    p.add_option('-k', '--keep',
                 action='store_true', default=False, dest='keep',
                 help='keep files')
    p.add_option('-l', '--list',
                 action='store_true', default=False, dest='list',
                 help='list tests')
    p.add_option('-q', '--quiet',
                 action='store_true', default=False, dest='quiet',
                 help='quieter')
    p.add_option('-t', '--to',
                 action='store', default='', dest='final',
                 help='run all tests up to this one')
    p.add_option('-v', '--verbose',
                 action='store_true', default=False, dest='verbose',
                 help='louder')
    (o, a) = p.parse_args(sys.argv)

    if o.verbose:
        volume = 2
    elif o.quiet:
        volume = 0
    else:
        volume = 1
        
    this = sys.modules[__name__]

    testlist = all_tests()
    if o.list:
        list_tests(a, o.final, testlist)
    else:
        run_tests(a, o.final, testlist)
        if not o.keep:
            cleanup_tests()

        
'''
Notes:

[DONE] must call validate_owner_file() at app level

[DONE] swroot is set incorrectly in a number of tests -- should be
    testdir everywhere

[DONE] logfile name should be computed from test name in all cases (see
    test_app_req_missing)

[DONE] write main test for bad owner file(s) at app level

[DONE] call get_owners() at app level?

[DONE] write tests for get_application_list()

[DONE] '.check4newver: no "next check" in last line' is over-indented

!@! document all test cases

'''
