'''
log.py

Log a report about an installation.

By default, the user is presented a template with the information to be
provided in an editor selected by $EDITOR, '/usr/bin/vi', or '/usr/bin/vim'.

With the option '-d' or '--dialog', the user will be asked questions in
a dialog format to fill out the report template.

HISTORY

    2009-05-20 - Updated the editor determination code to find
                 '/usr/bin/vim' on machines that don't have a
                 '/usr/bin/vi' binary.

    2009-07-16 - Scan $PATH looking for editor.

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

from config import *
import getpass
import smtplib
import sys

# ---------------------------------------------------------------------------
def main(dialog):

    username = getpass.getuser()
    if dialog:
        (subject, msg) = use_dialog(username)
    else:
        (subject, msg) = use_editor(username)

    send_message(username, subject, msg)

# ---------------------------------------------------------------------------
def filter_hashes(orig):
    rval = [re.sub(r'^#.*\n', 'DELETEME', x) for x in orig]
    while 'DELETEME' in rval:
        rval.remove('DELETEME')
    return rval
    
# ---------------------------------------------------------------------------
def find_editor():
    editor = os.getenv('EDITOR')
    if editor != None:
        candidate = editor.split()[0]
        for dir in os.getenv('PATH').split(':'):
            cpath = '%s/%s' % (dir, candidate)
            if os.access(cpath, os.X_OK):
                return editor
    
    for candidate in ['/usr/bin/vi', '/usr/bin/vim']:
        if os.access(candidate, os.X_OK):
            editor = candidate
            break

    return editor

# ---------------------------------------------------------------------------
def send_message(username, subjtxt, body):
#    uaddr = "%s@nics.utk.edu % username
    uaddr = "swadm@nics.utk.edu"
#    rtaddr = "rt-software@ccs.ornl.gov"
    rtaddr = "swadm@nics.utk.edu"

    to = "To: %s\n" % rtaddr
    fromfield = "From: %s\n" % uaddr

    subject = "Subject: %s\n\n" % subjtxt
    
    # Make the message a single string
    msg = to + fromfield + subject + body
    
    # Send the message using smtplib
    server = smtplib.SMTP("mail.nics.utk.edu")
    server.sendmail(uaddr, rtaddr, msg)
    server.quit()
    
# ---------------------------------------------------------------------------
def use_editor(username):
    logname = "/tmp/sw.%s.%s.log" % (username, os.getpid())
    editor = find_editor()

    cmd = "cp %s/tools/templates/log %s" % (software_root(), logname)
    print cmd
    os.system(cmd)

    done = False
    while not done:
        cmd = "%s %s" % (editor, logname)
        print cmd
        os.system("%s %s" % (editor, logname))

        f = open(logname, "r")
        l = filter_hashes(f.readlines())
        f.close()

        body = ''.join(l)
        done = True
        if '@' in body:
            answer_complete = False
            while not answer_complete:
                print "There are still @'s in the log entry."
                print "Do you want to"
                print "    (c) continue editing the entry,"
                print "    (a) abort this entry, or"
                print "    (s) send the entry as it is?"
                answer = sys.stdin.readline()
                answer_complete = True
                if re.search(r'\s*[aA].*', answer):
                    os.unlink(logname)
                    sys.exit()
                elif re.search(r'\s*[cC].*', answer):
                    done = False
                elif re.search(r'\s*[sS].*', answer):
                    done = True
                else:
                    answer_complete = False

    (app) = re.findall(r'Application:\s*(\S+)', body)
    (version) = re.findall(r'Version:\s*(\S+)', body)
    (machine) = re.findall(r'Machine\(s\):\s*(\S+)', body)
    subject = "Software Installed: %s %s on %s" % (app[0],
                                                   version[0],
                                                   machine[0])

    os.unlink(logname)
    return (subject, body)

# ---------------------------------------------------------------------------
def use_dialog(username):

    nametext = "Please enter your name:"
    print nametext
    name = sys.stdin.readline()

    apptext = "What application did you install:"
    print apptext
    app = sys.stdin.readline()
    
    versiontext = "What version was installed?:"
    print versiontext
    version = sys.stdin.readline()

    machinetext = "On what machines was it installed?:"
    print machinetext
    machine = sys.stdin.readline()

    compilerstext = "What compilers/build options were used?:"
    print compilerstext
    compilers = sys.stdin.readline()

    teststext = "Did the application pass all of its test? Why?:"
    print teststext
    tests = sys.stdin.readline()

    conformtext = "Did the application pass the conformance check? Why?:"
    print conformtext
    conform = sys.stdin.readline()

    descriptiontext = "Did you update the description file?:"
    print descriptiontext
    description = sys.stdin.readline()

    modulefiletext = "What did you name the modulefile?:"
    print modulefiletext
    modulefile = sys.stdin.readline()

    whotext = "Was this installed in response to a user (who) or just time to update?:"
    print whotext
    who = sys.stdin.readline()

    restrictionstext = "Are there any special restricitions on using this application/version/build?:"
    print restrictionstext
    restrictions = sys.stdin.readline()

#    livetext = "When should this application go live?:"
#    print livetext
#    live = sys.stdin.readline()

    body = "\nUsername: " + username + "\n"+ nametext + name + apptext + app + versiontext + version + machinetext + machine + compilerstext + compilers + teststext + tests + conformtext + conform + descriptiontext + description + modulefiletext + modulefile + whotext + who + restrictionstext + restrictions #+ livetext + live
    subject = "Software Installed: %s %s on %s\n" % (app.strip("\n"),
                                                     version.strip("\n"),
                                                     machine.strip("\n"))
    return (subject, body)

    
