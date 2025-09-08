#!/usr/bin/env python3

import os
import sys
import argparse

RESET = "\033[0m"
RED = "\033[31m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
BLUE = "\033[34m"
BRIGHT_BLUE = "\033[94m"

if os.path.exists("/usr/share/pkgctl/modules/exitp.py") == False:
    print(f"{RED}ERROR: {BRIGHT_BLUE}set-default cannot work without exitp module.{RESET}")
    sys.exit(1)

sys.path.append("/usr/share/pkgctl/modules")
from exitp import exitp

pversion = "pkgctl set-default 1.1.2\n\nDeveloped with <3 by Chruścik.\nLicensed under GNU General Public License v3.\nzOS and pkgctl comes with ABSOLUTELY NO WARRANTY, to the extent permitted by applicable law."

class MultiLineVersion(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        print(pversion)
        parser.exit()

def parse_p(path):
    config = {}
    with open(path, "r") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if ":" not in line:
                continue
            key, spath = line.split(":", 1)
            config[key.strip()] = spath.strip()
    return config

cfg = parse_p("/etc/pkgctl/set-default.conf")

dbdir = "/var/db/pkgctl"
dbpackages = [f for f in os.listdir(dbdir) if os.path.isdir(os.path.join(dbdir, f))]
packages = list()

for pkg in dbpackages:
    if os.path.exists(os.path.join("/var/db/pkgctl", pkg, "PROVIDES")):
        packages.append(pkg)
    else:
        continue

parser = argparse.ArgumentParser(description="")
parser.add_argument("--list", "-l", type=str, help="List avalaible LIST providers")
parser.add_argument("--set", "-s", type=str)
parser.add_argument("--unset", "-u", type=str)
parser.add_argument("--package", "-p", type=str)
parser.add_argument("--version", "-v", nargs=0, action=MultiLineVersion)

args = parser.parse_args()

if args.list != None:
	print(f"{GREEN}Checking...")
	listp = list()
	
	for p in packages:
		provides = parse_p(os.path.join("/var/db/pkgctl", p, "PROVIDES"))
		if args.list in provides:
	 		listp.append(p)
		else:
			continue
			
	if not listp:
		exitp(f"{BRIGHT_BLUE}There are no providers for {GREEN}{args.list}{RESET}", "s", 0)
	print(f"{BRIGHT_BLUE}Avalaible providers for {GREEN}{args.list}:{RESET}")
	for i in listp:
		print(f"{i}")
	exitp("", "s", 0)
	 		 	
if args.package != None:
	if args.set != None:
		if os.path.exists(os.path.join("/var/db/pkgctl", args.package, "PROVIDES")) == False:
			exitp(f"{RED}ERROR: {BRIGHT_BLUE}Package '{args.package}' is not installed or does not provide anything.{RESET}", "s", 1)
		p = parse_p(os.path.join("/var/db/pkgctl", args.package, "PROVIDES"))
		if args.set in p:
			ret = os.system(f"ln -sf {p[args.set]} {cfg[args.set]}")
			if ret != 0:
				exitp(f"{RED}ERROR: {BRIGHT_BLUE}Child-process failed with code:{RESET} {ret >> 8}", "s", 1)
			else:
				exitp(f"{BRIGHT_BLUE}Successfully set {YELLOW}{args.package} {BRIGHT_BLUE}as default {YELLOW}{args.set}{RESET}", "s", 1)
		else:
			exitp(f"{RED}ERROR: {GREEN}{args.package}{BRIGHT_BLUE}does not provide {args.set}{RESET}", "s", 1)

if args.unset != None:
	if args.unset in cfg:
		if os.path.exists(cfg[args.unset]) == False:
			exitp(f"{RED}ERROR: {GREEN}{args.unset}{BRIGHT_BLUE} is not set{RESET}", "s", 1)
		os.system(f"rm -rf {cfg[args.unset]}")
		exitp(f"{GREEN}Task completed successfully", "s", 0)
