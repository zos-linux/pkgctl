#!/usr/bin/env python3

#
# Fetching module for pkgctl
# Written by Chruścik with <3
#
# zOS and pkgctl comes with ABSOLUTELY NO WARRANTY, to the extent permitted by applicable law.
# Licensed under GNU General Public License v3
#

import os
import sys
import argparse
import tqdm
import requests
import certifi
from requests.exceptions import HTTPError, RequestException

if os.path.exists("/usr/share/pkgctl/modules/exitp.py") == False:
	print("This program cannot work without exitp module")
	sys.exit(1)

sys.path.append("/usr/share/pkgctl/modules")
import exitp

pversion = "pkgctl fetch 1.1.1\n\nDeveloped with <3 by Chruścik.\nLicensed under GNU General Public License v3.\nzOS and pkgctl comes with ABSOLUTELY NO WARRANTY, to the extent permitted by applicable law."

class MultiLineVersion(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        print(pversion)
        parser.exit()

RESET   = "\033[0m"
RED     = "\033[31m"
GREEN   = "\033[32m"
YELLOW  = "\033[33m"
BLUE    = "\033[34m"
BRIGHT_BLUE = "\033[94m"

def fetch(filename, dest, url, mode):
	try:
		response = requests.get(url, stream=True, verify=certifi.where(), timeout=10)
		response.raise_for_status()

		if filename == "":
			filename = None
			if "Content-Disposition" in response.headers:
				content_disp = response.headers["Content-Disposition"]
				if "filename=" in content_disp:
					filename = content_disp.split("filename=")[1].strip('"')

			if not filename :
				filename = url.split("/")[-1] or "dwd_data"

		total = int(response.headers.get("content-length", 0))
		block_size = 1024

		if dest == "":
			dest = os.getcwd()
			
		with open(os.path.join(dest, filename), "wb") as f, tqdm.tqdm(total=total, unit="B", unit_scale=True, desc=filename, ascii=" =") as bar:
			for chunk in response.iter_content(block_size):
				f.write(chunk)
				bar.update(len(chunk))

		if mode == "i":
			print(f"{BRIGHT_BLUE}File downloaded as {os.path.join(dest, filename)}")

	except HTTPError as e:
		print(f"{RED}ERROR: {BRIGHT_BLUE}HTTP Error: {RESET}{e}")
	except RequestException as e:
		print(f"{RED}ERROR: {BRIGHT_BLUE}Download error: {RESET}{e}")
	
if __name__ == "__main__":
	parser = argparse.ArgumentParser(description="")

	parser.add_argument("--output", "-o", type=str, help=" Output filename")
	parser.add_argument("--destdir", "-d", type=str, help=" Pretty self-explanatory")
	parser.add_argument("--url", "-u", type=str, help=" Pretty self-explanatory")
	parser.add_argument("--force", "-f", action="store_true", help=" Pretty self-explanatory")
	parser.add_argument("--version", "-v", nargs=0, action=MultiLineVersion, help=" Shows version and exits.")

	args = parser.parse_args()

	if args.destdir != None:
		if os.path.exists(args.destdir) == False:
			if args.force == False:
				exitp.exitp(f"{RED}ERROR: {BRIGHT_BLUE}Directory {args.destdir} doesn't exist!", "i", 1)
			else:
				os.makedirs(args.destdir)
	else:
		args.destdir = ""

	if args.output != None:
		if os.path.exists(os.path.join(args.destdir, args.output)) == True:
			if args.force == False:
				exitp.exitp(f"{RED}ERROR: {BRIGHT_BLUE}File {args.output} at {args.destdir} already exists!", "i", 1)
	else:
		args.output = ""
	
	fetch(args.output, args.destdir, args.url, "i")
    print(f{RESET})
