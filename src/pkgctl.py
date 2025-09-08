#!/usr/bin/env python3

#
# pkgctl 1.1.2
# zOS default package manager written with <3 by Chruścik.
#
# Licensed under GNU General Public License v3.
# zOS and pkgctl comes with ABSOLUTELY NO WARRANTY, to the extent permitted by applicable law.
#

import re
import subprocess
from pathlib import Path
import argparse
import os
import sys

pversion = "pkgctl 1.1.2\n\nDeveloped with <3 by Chruścik.\nLicensed under GNU General Public License v3.\nzOS and pkgctl comes with ABSOLUTELY NO WARRANTY, to the extent permitted by applicable law."

RESET   = "\033[0m"
RED 	= "\033[31m"
GREEN	= "\033[32m"
YELLOW	= "\033[33m"
BLUE	= "\033[34m"
BRIGHT_BLUE = "\033[94m"

if os.path.exists("/usr/share/pkgctl/modules/exitp.py") == False:
	print(f"{RED}ERROR: {BRIGHT_BLUE}pkgctl cannot work properly without exitp module")
	sys.exit(1)

if os.path.exists("/usr/share/pkgctl/modules/fetch.py") == False:
	print(f"{RED}ERROR: {BRIGHT_BLUE}pkgctl cannot work properly without fetch module")
	sys.exit(1)

sys.path.append("/usr/share/pkgctl/modules")
import exitp
import fetch

class MultiLineVersion(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        print(pversion)
        parser.exit()

def parse_pkginfo(path):
	variables = {}
	sections = {}
	current_section = None
	buffer = []

	with open(path, "r") as f:
		for line in f:
			line = line.strip()
			if not line or line.startswith("#"):
				continue

			if line.endswith("=("):
				current_section = line.split("=")[0].strip()
				buffer = []
				continue

			if line == ")":
				if current_section:
					sections[current_section] = buffer
				current_section = None
				buffer = []
				continue

			if current_section:
				buffer.append(line)
				continue

			if "=" in line:
				key, value = line.split("=", 1)
				variables[key.strip()] = value.strip()

	return variables, sections


def run_commands(commands, variables):
    for cmd in commands:
        for k, v in variables.items():
            cmd = cmd.replace(f"${k}", v)
        print(f"\n{BRIGHT_BLUE}==>> Running: {RESET}{cmd}")
        try:
            subprocess.run(
                cmd,
                shell=True,
                check=True,
                stdout=sys.stdout,
                stderr=sys.stderr
            )
        except subprocess.CalledProcessError as e:
            exitp.exitp(f"{RED}ERROR: {BRIGHT_BLUE}Child-process failed with error code{RESET} {e.returncode}: {cmd}", "p", 1)
        except Exception as e:
            exitp.exitp(f"{RED}ERROR: {BRIGHT_BLUE}Child-process {RESET}'{cmd}' {BRIGHT_BLUE}failed{RESET}: {e}", "p", 1)


if os.path.exists("/etc/pkgctl.conf") == True:

	conf = {}
	with open("/etc/pkgctl.conf", "r") as f:
		for line in f :
			line = line.strip()
			if not line or line.startswith("#"):
				continue
			if "=" in line:
				key, value = line.split("=", 1)
				key = key.strip()
				value= value.strip().strip('"').strip("'")
				conf[key] = value
else:
	exitp.exitp(f"{RED}ERROR: {BRIGHT_BLUE}/etc/pkgctl.conf does not exist!{RESET}", "p", 1)

def install_package(package, rootdir, mode):
	pkginfo = os.path.join("/usr/ports", package, "PKGINFO")
	if os.path.exists(pkginfo) == False:
		exitp.exitp(f"{RED}ERROR: {BRIGHT_BLUE}Specified package doesn't exist!{RESET}", "p", 1)

	variables, sections = parse_pkginfo(pkginfo)
    if "MAKEOPTS" in conf:
        variables["MAKEOPTS"] = conf["MAKEOPTS"]
    if "CFLAGS" in conf:
        variables["CFLAGS"] = conf["CFLAGS"]
    if "CXXFLAGS" in conf:
        variables["CXXFLAGS"] = conf["CXXFLAGS"]
    if "BUILDOPTS" in conf:
        variables["BUILDOPTS"] = conf["BUILDOPTS"]

	pkgdb = os.path.join(rootdir, "var/db/pkgctl", package)
	cachedir = os.path.join(rootdir, "var/cache/pkgctl")
	builddir = os.path.join(cachedir, "build")

	if os.path.exists(pkgdb) == True:
		with open(os.path.join(pkgdb, "VERSION"), "r") as f:
			ver = f.read()
		if ver == variables["PKGVERSION"]:
			print(f"{RED}ERROR: {BRIGHT_BLUE}{package} is already installed! (version: {ver}){RESET}")
			return

	if mode == "i":
		print("Name			Version			")
		print(f"{variables['PKGNAME']}			{variables['PKGVERSION']}")
		if args.yes == True:
			confirm = "y"
		else:
			confirm = input(f"{YELLOW}Correct? (y/n): {RESET}")
		if confirm != "y":
			exitp.exitp("Aborting", "p", 0)

	if mode == "i":
		if "DEPENDSON" in variables:
			deps = variables["DEPENDSON"]
			if isinstance(deps, str):
				deps = deps.strip("[]").split(",")
				deps = [d.strip() for d in deps]
			for dep in deps:
				if os.path.exists(os.path.join(rootdir, "var/db/pkgctl", dep)):
			   		continue
				else:
					install_package(dep, rootdir, "i")

	os.system(f"rm -rf {os.path.join(rootdir, 'var/cache/pkgctl/*')}")
	os.makedirs(cachedir, exist_ok=True)
	os.makedirs(builddir, exist_ok=True)

	if "fetch" in sections:
		print(f"{BRIGHT_BLUE}==>> Fetching... {RESET}")
		fetch.fetch("", cachedir, variables["URL"], "p")

	if "build" in sections:
		print(f"{BRIGHT_BLUE}==>> Building... {RESET}")
		os.chdir(builddir)
		run_commands(sections["build"], variables)

	if "strip" in sections:
		print(f"{BRIGHT_BLUE}==>> Stripping binaries... {RESEET}")
		os.chdir(builddir)
		run_commands(sections["strip"], variables)

	if "install" in sections:
		print(f"{BRIGHT_BLUE}==>> Installing... {RESET}")
		os.chdir(builddir)
		run_commands(sections["install"], variables)

	if os.path.exists(pkgdb) == False:
		os.makedirs(pkgdb)
	os.system(f"cp -f {os.path.join('/usr/ports', package, 'FILES')} {os.path.join(pkgdb, 'FILES')}")
	with open(os.path.join(pkgdb, "VERSION"), "w") as v:
		v.write(variables['PKGVERSION'])
	with open(os.path.join(pkgdb, "PKGNAME"), "w") as p:
		p.write(variables['PKGNAME'])
	if os.path.exists(os.path.join("/usr/ports", package, "PROVIDES")):
		os.system(f"cp -f {os.path.join('/usr/ports', package, 'PROVIDES')} {os.path.join(pkgdb, 'PROVIDES')}")
	os.system(f"cp -f {os.path.join('/usr/ports', package, 'CATEGORY')} {os.path.join(pkgdb, 'CATEGORY')}")

parser = argparse.ArgumentParser(description="Example")

#parser.add_argument("-B", "--build", type=str, action="store", help="Build only, do not install (WIP)")
#parser.add_argument("-v", "--verbose", action="store_true", help="Verbose mode")
#parser.add_argument("-q", "--quiet", action="store_true", help="Quiet mode")
parser.add_argument("-r", "--remove", type=str, action="store", help="Remove package")
#parser.add_argument("-R", "--rootdir", type=str, action="store", help="Path to custom rootdir")
parser.add_argument("-u", "--update", action="store_true", help="Update package index")
parser.add_argument("-U", "--upgrade", action="store_true", help="Perform system upgrade")
parser.add_argument("-V", "--version", nargs=0, action=MultiLineVersion, help="Print pkgctl version")
parser.add_argument("-I", "--install", type=str, action="store", help="Install package")
parser.add_argument("-y", "--yes", action="store_true", help="Yes on all questions")
parser.add_argument("-l", "--list", action="store_true", help="List all installed packages")

args = parser.parse_args()

if os.geteuid() != 0:
	print(f"{RED}ERROR: {BRIGHT_BLUE}You must run this program as root{RESET}")
	sys.exit(1)

if os.path.exists("/var/lock/pkgctl.lock") == True:
	print(f"{RED}ERROR: {BRIGHT_BLUE}/var/lock/pkgctl.lock exists, cannot continue.{RESET}")
	sys.exit(1)

if os.path.exists("/var/cache/pkgctl/") == False:
	os.makedirs("/var/cache/pkgctl")

if os.path.exists("/var/db/pkgctl") == False:
	os.makedirs("/var/db/pkgctl")

if args.rootdir != None:
	rootdir = args.rootdir
else:
	rootdir = "/"

if args.update == True:
	os.system("touch /var/lock/pkgctl.lock")
	if os.path.exists("/etc/pkgctl/mirror.conf") != True:
		exitp.exitp(f"{RED}ERROR: {BRIGHT_BLUE}/etc/pkgctl/mirror.conf doesn't exist!{RESET}", "p", 1)
	with open("/etc/pkgctl/mirror.conf", "r") as mirrorcfg:
		mirror = str(mirrorcfg.read())
	os.system(f"rm -rf {os.path.join("/usr/ports/*")}")
	os.system("git clone {mirror} /var/cache/pkgctl/index")
	os.system(f"mv /var/cache/pkgctl/index/* /usr/ports")
	exitp.exitp(f"{GREEN}Task completed successfully!{RESET}", "p", 0)

elif args.remove != None:
	os.system("touch /var/lock/pkgctl.lock")
	if os.path.exists(os.path.join(rootdir, "var/db/pkgctl", args.remove)) == False:
		exitp.exitp(f"{RED}ERROR: {BRIGHT_BLUE}Specified package doesn't exist!{RESET}", "p", 1)
	else:
		with open(os.path.join(rootdir, "var/db/pkgctl", args.remove, "FILES"), "r") as rpkg:
			print("Name			Version			")
			print(f"{open(os.path.join(rootdir, 'var/db/pkgctl', args.remove, 'PKGNAME')).read()}			{open(os.path.join(rootdir, 'var/db/pkgctl', args.remove, 'VERSION')).read()}")
			if args.yes == False:
				confirm = input(f"{YELLOW}Correct? (y/n): {RESET}")
			else:
				confirm = "y"
			if confirm != "y":
				exitp.exitp("Aborting", "p", 0)
			if open(os.path.join(rootdir, 'var/db/pkgctl', args.remove, 'CATEGORY')).read() == "base":
				confirm = input(f"{RED}WARNING: {RESET}{args.remove} {YELLOW}is a base package. Are you sure you want to remove {args.remove}{YELLOW}? (y/n): {RESET}")
				if confirm != "y":
					exitp.exitp("Aborting", "p", 0)
			print(f"{BRIGHT_BLUE}==>> Deinstalling {args.remove}...{RESET}")
			os.system(f"rm -rf {rpkg.read()}")
			os.system(f"rm -rf {os.path.join(rootdir, 'var/db/pkgctl', args.remove)}")
			exitp.exitp(f"{GREEN}Task completed succesfully!{RESET}", "p", 0)
			
#elif args.build != None:
#	os.system("touch /var/lock/pkgctl.lock")
#	if os.path.exists(os.path.join("/usr/ports", args.build, "PKGINFO")) == True:
#		variables, sections = parse_pkginfo(os.path.join("/usr/ports", args.build, "PKGINFO"))
#		print("Name			Version			")
#		print(f"{variables['PKGNAME']}			{variables['PKGVERSION']}")
#		for sec in ("fetch", "build"):
#			if sec in sections:
#				run_commands(sections[sec], variables)
#		exitp.exitp(f"{GREEN}Task completed successfully!{RESET}", "p", 0)
#	else:
#		exitp.exitp(f"{RED}ERROR: {BRIGHT_BLUE}Specified package doesn't exist!{RESET}", "p", 1)

elif args.install != None:
	os.system("touch /var/lock/pkgctl.lock")
	install_package(args.install, rootdir, "i")
	exitp.exitp(f"{GREEN}Task completed successfully{RESET}", "p", 0)

elif args.upgrade == True:
	os.system("touch /var/lock/pkgctl.lock")

	pkgdb = os.path.join(rootdir, "var/db/pkgctl")
	
	folder = [f for f in os.listdir(pkgdb) if os.path.isdir(os.path.join(pkgdb, f))]
	upgradable = []
	for pkg in (folder):
		variables, sections = parse_pkginfo(os.path.join("/usr/ports", pkg, "PKGINFO"))
		ver = open(os.path.join(pkgdb, pkg, "VERSION")).read()
		if variables["PKGVERSION"] != ver:
			upgradable.append(pkg)
		else:
			continue
	upgradablelist = list(dict.fromkeys(upgradable))

	if not upgradablelist:
		exitp.exitp(f"{BRIGHT_BLUE}All packages are up to date", "p", 0)

	print("Name			Version			")
	for pkg in (upgradablelist):
		variables, sections = parse_pkginfo(os.path.join("/usr/ports", pkg, "PKGINFO"))
		print(f"{pkg}			{variables['PKGVERSION']}")

	if args.yes == "y":
		confirm = "y"
	else:
		confirm = input(f"{YELLOW}Correct? (y/n): {RESET}")
	if confirm != "y":
		exitp.exitp("Aborting", "p", 0)

	for pkg in (upgradablelist):
		install_package(pkg, rootdir, "u")
		
elif args.list == True:
	pkgdb = os.path.join(rootdir, "var/db/pkgctl")

	folder = [f for f in os.listdir(pkgdb) if os.path.isdir(os.path.join(pkgdb, f))]
	print("Name			Version			")
	for pkg in (folder):
		print(f"{pkg}			{open(os.path.join(pkgdb, pkg, 'VERSION')).read()}")
