'''
NAME
    reporthtml.py

SYNOPSIS

    import reporthtml

DESCRIPTION

    reporthtml is a tool for generating html reports based on available system information

    I apologize if this code looks like spaghetti -- unfortunately there are lots of things that this script has to do
    and lots of exeptions to every rule
    

HISTORY

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
import shutil
import StringIO
from types import ListType

def main(architecture,hidestatus,hidesupport,debug):

    # Capture the current umask and set a new umask based on sw_config
    old_umask = os.umask(get_umask())
    
    # Initializa archs to empty
    archs= []
    
    # Get the arches from the config file
    for arch in webarchs():
        if os.path.isdir(software_root()+"/"+arch):
            archs.append(software_root()+"/"+arch)
        else:
            error(software_root()+"/"+arch+ " is not a valid architecture")
    
    if architecture != "*":
        if os.path.isdir(software_root()+"/"+architecture):
            archs = [software_root()+"/"+architecture]
            file = StringIO.StringIO()
        else:
            error("invalid architecture")
    else:
        # Begin writing the alphabetical table for all machines
        file = open(webhome()+"/alphabetical.html","w")
    
    # Start writing out the table
    file.write("<h2>Applications</h2>")
    file.write('Click here for the <a href="?&view=category">Category View</a>')
    file.write('<table class="inline">\n')
    file.write("\n<tr>\n")
    file.write("\t<th></th>\n")

    # Initialize the dicitionary of apps to empty
    apps =[]
    
    # Set the initial table width to 0
    width = 0

    # Loop through the architectures
    for arch in archs:
        if debug:
            print arch 
        # Set the table width, and write out the architectures across the top of the table
        if os.path.isdir(arch):
            file.write("\t<th>"+arch.split("/")[-1]+"</th>\n") 
            width = width +1
     
        # If the application isn't already in the list of apps, add it to the list
        for line in glob.glob(arch +"/*"):
            if not noweb(line):
                if line.split("/")[-1] not in apps:
                    apps.append(line.split("/")[-1])
        
        # Remove any exceptions (Like the modulefiles folder) -- read from sw_config
        for exception in application_exceptions():
            if exception in apps:
                apps.remove(exception)

    # Sort the list so that it's alphabetical
    apps.sort() 

    # Close out the row
    file.write("</tr>\n\n")

    #Initialize the list of categories to empty
    primary = {}


    # Write out the machine specific listing of apps
    for arch in archs:
        
        machineprimary = {}
        
        # Create the machine specific listing of applications (A list, not a table)
        if not os.path.isdir(webhome()+"/"+arch.split("/")[-1]):
            os.mkdir(webhome()+"/"+arch.split("/")[-1])

        machinefile = open(webhome()+"/"+arch.split("/")[-1]+"/alphabetical.html","w")
        machinefile.write('<a href="?&view=category">[switch to Category View]</a>')
        machinefile.write('<ul class="sw">')

        for app in apps:       # Nick's implementation
            if os.path.isdir(arch+"/"+app):
 
#             Check for noweb again, because some apps will be in 
#             apps list that should not be shown.
#             Example: 
#                 xt/petsc            means petsc will be in list
#                 bgp/petsc/.noweb    should not be in list for bgp, but
#                                     is in master app list because of xt
              if not noweb(arch+"/"+app):  # skip noweb apps

                ###############
                ###############
                # Machine specific page links
                ###############
                machinefile.write('\n<li><a href="?&software='+app+'">'+app+'</a></li>')
 
                # Suck the text out of the application description file
                try:
                    original_descripfile = open(arch+"/"+app+"/description","r")
                    text = original_descripfile.readlines()
                    original_descripfile.close()

                    # Travere the lines of text in the description file to parse out the categorys
                    for line in text:
                        
                        # If the lines contains the Category keyword
                        if "Category" in line:
                            if len(line.split(":")) >= 2:

                                # Get the first field after the colon with all whitespace and newlines removed
                                key = ((line.split(":")[1]).strip("\n").split("-")[0]).strip(" ").rstrip("_")

                                # Get the second field after the colon with all whitespace and newlines removed
                                try:
                                    key2 = ((line.split(":")[1]).strip("\n").split("-")[1]).strip(" ").rstrip("_")
                                except:
                                    key2 = "Uncategorized"
                                    
                                if key == "":
                                    key = "As Yet Uncategorized"
                                    key2 = "Uncategorized"

                                if key2 =="":
                                    key2 = "Uncategorized"
                                
                                # If primary category isn't in list, add it to the list
                                if machineprimary.has_key(key) == False :
                                    machineprimary[key] = {key2:[app]}
                                else:
                                    # Primary category is in list add the app to the appropriate sublist
                                    list = machineprimary[key]
                                    if key2 not in list.keys():
                                        list[key2] = [app]
                                        machineprimary[key] = list
                                    else:
                                        if app not in list[key2]:
                                            list[key2].append(app)
                                        machineprimary[key] = list
                except:
                    print arch+"/"+app+"/description does not exist or cannot be opened"

         
        keys = machineprimary.keys()
        keys.sort()
        
        # Write out the machine specific categorical listing of applications
        
        machinedescripfile = open(webhome()+"/"+arch.split("/")[-1]+"/category.html","w")
        #machinedescripfile.write('<a href="../software/">Alphabetical View</a>')
        machinedescripfile.write('<a href="?&view=alphabetical">[switch to Alphabetical View]</a>')
        machinedescripfile.write('<ul class="sw">') 
        for key in keys:
                machinedescripfile.write("<li>"+key+"</li>\n")
                
                list = machineprimary[key]
                key2s = list.keys()
                key2s.sort()
               
                for key2 in key2s:
                    if key2 != "Uncategorized":
                        machinedescripfile.write('<ul class="sw"><li>'+key2+'</li>\n')    
                    list2 = list[key2]
                    
                    machinedescripfile.write('<ul class="sw">')
                    for app in list2:
                        machinedescripfile.write('<li>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<a href="?&software='+app+'">'+app+'</a></li>\n')
                    
                    machinedescripfile.write('</ul>\n')
                                        
                    machinedescripfile.write('</ul>\n') 
        
        machinedescripfile.write('</ul>\n')
        machinedescripfile.close()
        
        machinefile.write("</ul>")
        machinefile.close()
    
        #if architecture != "*":
            #return

#mrf:start   
    # get showos setting (set in sw_config)
    showos = get_show_os_on_web()
#mrf:end

    # Traverse the list of apps (all machnes)
    for app in apps:

        # The first cell of each row has an app name
        file.write("<tr>\n\t<th>"+app+"</th>\n")
       
        # Fill in the remaining columns with Xs as appropriate
        for i in range(0,width):
            # If the app dir exists, put an X
            if os.path.isdir(archs[i]+"/"+app): 
                
                ####################
                ####################
                # Links for the table of all machines
                ####################
                ####################
                file.write('\t<td><a href="?&arch='+archs[i].rsplit("/",1)[1]+'&software='+app+'">X</a></td>\n') 
                
                # If the machines directory doees not exist in the webhome, create it
                if not os.path.isdir(webhome()+"/"+archs[i].split("/")[-1]):
                    os.mkdir(webhome()+"/"+archs[i].split("/")[-1])
                
                descripfile = open(webhome()+"/"+archs[i].split("/")[-1]+"/"+app+".html","w")    
                #if debug:
                  #print "file is:"+ webhome()+"/"+archs[i].split("/")[-1]+"/"+app+".html"    
                
                # Suck the text out of the application description file
                try:
                    original_descripfile = open(archs[i]+"/"+app+"/description","r")
                    text = original_descripfile.readlines()
                    original_descripfile.close()

                    # Travere the lines of text in the description file to parse out the categorys
                    for line in text:
                        descripfile.write(line)
                        
                        # If the lines contains the Category keyword
                        if "Category" in line:
                            if len(line.split(":")) >= 2:

                                # Get the first field after the colon with all whitespace and newlines removed
                                key = ((line.split(":")[1]).strip("\n").split("-")[0]).strip(" ").rstrip("_")

                                # Get the second field after the colon with all whitespace and newlines removed
                                try:
                                    key2 = ((line.split(":")[1]).strip("\n").split("-")[1]).strip(" ").rstrip("_")
                                except:
                                    key2 = "Uncategorized"
                                    
                                if key == "":
                                    key = "As Yet Uncategorized"
                                    key2 = "Uncategorized"

                                if key2 =="":
                                    key2 = "Uncategorized"
                                
                                # If primary category isn't in list, add it to the list
                                if primary.has_key(key) == False :
                                    primary[key] = {key2:[app]}
                                else:
                                    # Primary category is in list add the app to the appropriate sublist
                                    list = primary[key]
                                    if key2 not in list.keys():
                                        list[key2] = [app]
                                        primary[key] = list
                                    else:
                                        if app not in list[key2]:
                                            list[key2].append(app)
                                        primary[key] = list
                except:
                    print archs[i]+"/"+app+"/description does not exist or cannot be opened"
               
                # If hidesupport is off, print the support status
                if not hidesupport:
                
                    try:
                        supportfile = open(archs[i]+"/"+app+"/support","r")
                        support = supportfile.readlines()[0].strip("\n")
                        supportfile.close()
                    except:
                        print archs[i]+"/"+app+"/support cannot be opened"
                       
                    if support == "unsupported":
                        support = "Unsupported"
                    else:
                        support = "Supported"
                                            
                    descripfile.write('\n<h2>Support</h2>')
                    descripfile.write('<p>This package has the following support level : ' + support)
               

                # If there is a vendor exception at the app level, don't display the builds table
                if vendor(archs[i]+"/"+app):
                    descripfile.write('\n<br>\n<h2>Available Versions</h2>')
                    descripfile.write('\n<p>All versions of this software are provided by the system vendor.')
                    continue
               
                # Write out the build table
                descripfile.write('\n<br>\n<h2>Available Versions</h2>')
                
                descripfile.write('\n\n<table class="inline">')
                descripfile.write("\n<tr>")
                descripfile.write('\n\t<th rowspan = "2">Version</th>')
                descripfile.write('\n\t<th colspan = "'+str(len(compilers(archs[i].split("/")[-1]))+1)+'">Available Builds</th> </tr><tr>')
               
                # Get the list of valid compilers for this machine
             
                for compiler in compilers(archs[i].split("/")[-1]):
                    descripfile.write("\n\t<th>"+compiler+"</th>")
              
                descripfile.write("\n\t<th>Other</th>")
                
                descripwidth = len(compilers(archs[i].split("/")[-1]))+2
               
                vers = glob.glob(archs[i]+"/"+app+"/*")
                vers.sort(reverse=True)

                for ver in vers:
#mrf:start
                    # check if .notverdirs file exists and if so
                    # skip all directory names it contains
                    shortver = ver.split('/')
                    if notverdirs(archs[i]+"/"+app,shortver[4]):
                       continue
#mrf:end
                    if os.path.isdir(ver):
                        descripfile.write("\n<tr>")
                        descripfile.write("\n\t<th>"+ver.rsplit("/")[-1]+"</th>") 
                       
                        uniques = glob.glob(ver+"/*")
                        if vendor(ver):
                            uniques.append("vendor")
#mrf:start - for those builds provided by perc team (very one-off)
                        if perc(ver):
                            uniques.append("perc")
#mrf:end

                     
                        for compiler in compilers(archs[i].split("/")[-1]):
                            compilerbuilds = glob.glob(ver+"/*"+compiler+"*")
                      
                            if compilerbuilds != []:    
                                descripfile.write('\n\t<td><table class="inline">')
                                for build in compilerbuilds:
                                    try:
                                        uniques.remove(build)
                                    except:
                                        error("%s resolves to multiple compilers" % build, False)
                                    status = checkstatus(build)
                                    build = build.rsplit("/",1)[-1]
#mrf:start
                                    if showos == "no":
                                    # if you want to see only the compiler, set showos to yes in sw_config file 
                                        build = build.split("_",1)[-1]
#mrf:end
#                                    #build = build.replace(compiler,"")
                                    
                                    if hidestatus:
                                        descripfile.write('<tr>'+build+'</tr>')
                                    else:
                                        descripfile.write('<tr><td class="hidden">'+build+'</td><td class="hidden2">' + status +'</td></tr>')
                                        
                                descripfile.write("</table></td>")
                            else:
                                descripfile.write("\n\t<td></td>")
                       
                        if uniques != []:
                                descripfile.write('\n\t<td><table class="inline">')
                                for build in uniques:
#mrf:start
                                    # check if .notbuilddirs file exists 
                                    # skip all directory names it contains
                                    # this should only happen in the uniques 
                                    # loops
                                    if notbuilddirs(ver,build.split("/")[-1]):
                                       continue
#mrf:end
                                    if os.path.isdir(build):
                                        status = checkstatus(build)
                                        build = build.rsplit("/",1)[-1]
#mrf:start
                                        if showos == "no":
                                        # if you want to see only the compiler, set showos to yes in sw_config file 
                                            build = build.split("_",1)[-1]
#mrf:end
                                        
                                        if hidestatus:
                                            descripfile.write('<tr>'+build+'</tr>')
                                        else:
                                            descripfile.write('<tr><td class="hidden">'+build+'</td><td class="hidden2">'+ status+'</td><tr>')
                                    else:
                                        if build == "vendor": 
                                            descripfile.write('<tr>vendor</tr>')
                                        if build == "perc": 
                                            descripfile.write('<tr>perc</tr>')
                                
                                descripfile.write("</table></td>")       
                        else:
                            descripfile.write("\n\t<td></td>")
                        descripfile.write("\n</tr>") 
                
                descripfile.write("\n\n</table>")
               
            else:
                file.write("\t<td></td>\n")
                
        file.write("</tr>\n\n")    
    file.write("</table>\n")
   
    file.close()
  
    file = open(webhome()+"/category.html","w")
  
    file.write('Click here for the <a href="./">Alphabetical View</a>')    
    keys = primary.keys()
    keys.sort()
    
    
    for key in keys:
            file.write("<h2>"+key+"</h2>")
            file.write('<table class="inline">')
            file.write('<tr><th></th>')
            
            for arch in archs:
                if os.path.isdir(arch):
                    file.write("\t<th>"+arch.split("/")[-1]+"</th>\n")
                        
            file.write('</tr>')
            
            list = primary[key]
            key2s = list.keys()
            key2s.sort()
           
            for key2 in key2s:
                if key2 != "Uncategorized":
                    file.write("<tr><th><b>"+key2+"</b></th>")
                    for i in range(0,width):
                        file.write("<td></td>\n")
                    file.write("</tr>")
                
                list2 = list[key2]
                for app in list2:
                    file.write("<tr><th>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;"+app+"</th>")
                    for k in range(0,width):
                        if os.path.isdir(archs[k]+"/"+app):
                            file.write('\t<td><a href="?&arch='+archs[k].rsplit("/",1)[1]+'&software='+app+'">X</a></td>\n')
                        else:
                            file.write("<td></td>")
                                                                                                                                                                    
            file.write('</table>') 
        
    os.umask(old_umask)

