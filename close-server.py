
import os

def get_filename(path):
	return path.replace("\\","/").split("/")[-1]


local_dir = os.path.dirname(os.path.realpath(__file__))
dir_name = get_filename(local_dir)
command_file = local_dir+"/command-stack.txt"

f_out = open(command_file, "w")
f_out.write("stop\n")
f_out.close()

