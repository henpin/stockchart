#! /usr/bin/python

import os
import sys
import importlib

"""
calculate usermodule path and insert that to sys.path
"""

# The Part of Logic
def get_usermodule_directory():
	""" calculate and return user-module path """
	home_dir = os.getenv("HOME")
	if home_dir is None :
		raise Exception("The Environment 'Home' (that should indicates homedirectory-path) is not Defined")

	usermodule_dir = os.path.join(home_dir,"module")
	if not os.path.isdir(usermodule_dir) :
		raise Exception("UserModulePath (that auto-calculated) '%s' is not exist as directory" % usermodule_dir)

	return usermodule_dir

def check_overlapping_of_modulenames(module_dir):
	""" Check Module Names """
	for modulename in os.listdir(module_dir):
		is_package = ( os.path.isdir(modulename) and "__init__.py" in os.listdir(os.path.join(module_dir,modulename)) )
		is_pythoncode = modulename.endswith(".py")
		# the check of overlapping of ModuleNames
		if is_package or is_pythoncode :
			try :
				importlib.import_module(modulename.rstrip(".py"))
			except ImportError :
				pass
			else :
				print "*"*100
				print "Caution : UserModuleName '%s' is defined yet (so that will be overwritten )" % modulename
				print "*"*100


# Setting Module-serching path
def main():
	usermodule_dir = get_usermodule_directory()
	check_overlapping_of_modulenames(usermodule_dir)
	sys.path.insert(0,usermodule_dir)

main()
