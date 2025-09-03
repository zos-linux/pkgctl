import os
import sys

def exitp(msg, mode, code):
	print(msg)
	if mode == "p":
		os.system("rm -rf /var/lock/pkgctl.lock")
	sys.exit(code)
