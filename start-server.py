#!/usr/bin/python3
'''
This script will do the following operations:

1. zip game directory for distribution and put it in the dist folder

2. make a wep-page in the dist folder with list of mods and credits for them 
and download link

3. start an HTTP server in the dist folder on port 8080 so that your friends 
can download the modpack over the internet from your computer

4. copy mods and config folders (and contents of server-files) into server folder

5. creates a command-stack empty text file

6. starts the server

7. constantly polls the command-stack file timestamp for changes and runs commands 
on the server if the file changes (like a pipe, but OS independant)

8. exits when server exits (when the process terminates)

'''

import os
import threading
from http.server import HTTPServer, SimpleHTTPRequestHandler
import shutil
import subprocess
import time

def get_filename(path):
	return path.replace("\\","/").split("/")[-1]

print ("Initializing...")
ram = "4G"
local_dir = os.path.dirname(os.path.realpath(__file__))
dir_name = get_filename(local_dir)
dist_dir = local_dir+"/dist"
web_dir = dist_dir
temp_dir = dist_dir+"/"+dir_name
server_dir = local_dir+"/server"
server_mods_dir = server_dir+"/mods"
server_config_dir = server_dir+"/config"
command_file = local_dir+"/command-stack.txt"
command_file_timestamp = 0
pid_file = local_dir+"/pid"
if os.path.exists(command_file):
	os.remove(command_file)
if not os.path.exists(dist_dir):
	os.mkdir(dist_dir)
if not os.path.exists(web_dir):
	os.mkdir(web_dir)


# zip (most of) this folder into the dist folder
print ("Packaging game directory for distribution...")
include_folders = ["config","mods","server-files","resourcepacks"]
include_files = ["mod-list.txt","options.txt","start-server.py", "close-server.py"]
if os.path.exists(temp_dir):
	shutil.rmtree(temp_dir)
os.mkdir(temp_dir)
for source in include_folders:
	shutil.copytree(local_dir+"/"+source, temp_dir+"/"+get_filename(source))
for source in include_files:
	shutil.copy(local_dir+"/"+source, temp_dir)
shutil.make_archive(dist_dir+"/"+dir_name,"zip",temp_dir)
shutil.rmtree(temp_dir)

# make webpage
print ("Creating web page...")
mod_data = []
f_in = open(local_dir+"/mod-list.txt","r")
for row in f_in:
	cells = row.split("\t")
	if(len(cells) >= 4):
		mod_data.append(cells)
f_in.close()
mod_data.sort()
table = "<table border=\"3\">\n"
table += "<tr><th>Mod</th><th>Author</th><th>Website</th><th>License/Redistribution Policy</th></tr>\n"
for mod_entry in mod_data:
	table += "<tr>"
	table += "<td>"
	table += mod_entry[0]
	table += "</td><td>"
	table += mod_entry[1]
	table += "</td><td><a href=\""
	table += mod_entry[3]
	table += "\">"
	table += mod_entry[3]
	table += "</a></td><td>"
	table += mod_entry[2]
	table += "</td>"
	table += "</tr>\n"
table += "</table><br>\n"
html_file = ""
html_file += "<html>\n<head>\n<title>"
html_file += dir_name
html_file += "</title>\n"
html_file += "<body>\n"
html_file += "<h1>"
html_file += "Minecraft Server: "
html_file += dir_name
html_file += "</h1>\n<br><hr><p>\n"
html_file += "<h3>Download</h3><br>\n"
html_file += "<a href=\""
html_file += dir_name+".zip"
html_file += "\" download>Download the modpack game directory</a><p>\n"
html_file += "<hr><br><h3>Instructions</h3>\n<ol>\n"
html_file += "<li>Install the Forge mod loader</li>\n"
html_file += "<li>Download this modpack (from provided link above)</li>\n"
html_file += "<li>Extract the modpack zip file</li>\n"
html_file += "<li>Launch Minecraft and create a new profile in the profile editor</li>\n"
html_file += "<li>Set the <b>game directory</b> for the new profile to the filepath of the folder that you extracted from the .zip file</li>\n"
html_file += "<li>Set the <b>Minecraft version</b> to the correct Forge version</li>\n"
html_file += "<li>Save the profile</li>\n"
html_file += "<li>Select the new profile and then play Minecraft</li>\n"
html_file += "</ol>\n<br><hr><br>\n<h3>Mods</h3>\n"
html_file += table
html_file += "\n</body></html>"
f_out = open(web_dir+"/index.html","w")
f_out.write(html_file)
f_out.close()

# web server
print ("Starting distribution webserver...")
def web_server():
	os.chdir(web_dir)
	httpd = HTTPServer(('', 8080), SimpleHTTPRequestHandler)
	httpd.serve_forever()
thread_webserver = threading.Thread(target=web_server)
thread_webserver.daemon = True
thread_webserver.start()

# create server
print ("Creating server from game directory...")
if not os.path.exists(server_dir):
	shutil.copytree(local_dir+"/server-files", server_dir)
if os.path.exists(server_mods_dir):
	shutil.rmtree(server_mods_dir)
shutil.copytree(local_dir+"/mods", server_mods_dir)
if os.path.exists(server_config_dir):
	shutil.rmtree(server_config_dir)
shutil.copytree(local_dir+"/config", server_config_dir)

# command stack
print("Creating command execution queue file...")
f_out = open(command_file, "w")
f_out.write("")
f_out.close()
command_file_timestamp = os.path.getmtime(command_file)
print("\t","Commands will be read from pipe-like file ", command_file)

# start the minecraft server
print("Starting Minecraft server...")
files = os.listdir(server_dir)
for F in files:
	fname = get_filename(F)
	if(fname.startswith("forge") and fname.endswith(".jar")):
		jar_file = server_dir+"/"+F
		print("\tFound Forge .jar file ",F)
		break
command_list = ["java", "-jar", "-Xmx"+ram, str(jar_file), "nogui"]
print("\tProcess command:",command_list)
process = subprocess.Popen(command_list,cwd=server_dir, stdin=subprocess.PIPE, stdout=None, stderr=None)
pid = process.pid
print("\tProcess ID (pid) = ",str(pid))
f_out = open(pid_file, "w")
f_out.write(str(pid))
f_out.close()
def command_watcher():
	while(os.path.exists(command_file)):
		new_timestamp = os.path.getmtime(command_file)
		if(new_timestamp != command_file_timestamp):
			time.sleep(1) # wait an extra second to avoid some potential file locking issues
			commands = []
			f_in2 = open(command_file, "r")
			for c in f_in2:
				commands.append(c)
			f_in2.close()
			for c in commands:
				print("\tSending command to server:",c)
				process.communicate(input=bytes(c, 'utf-8'))
			f_out2 = open(command_file, "w")
			f_out2.write("")
			f_out2.close()
		time.sleep(1)
print("...Minecraft server started.")
thread_com = threading.Thread(target=command_watcher)
thread_com.daemon = True
thread_com.start()
process.wait()
time.sleep(2)
os.remove(command_file)
os.remove(pid_file)
print("...Minecraft server terminated.")
