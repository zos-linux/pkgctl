SRCDIR = /home/chruscik/apache/zos/pkgctl
DESTDIR = /
PREFIX = /usr/local
PKGCTLBIN = $(SRCDIR)/src/pkgctl.py
FILES = $(SRCDIR)/FILES
VERSION = 1.0
PKGNAME = pkgctl

all:
	echo "Run make install as root to install pkgctl ^_^"

install:
	cp -v $(PKGCTLBIN) $(DESTDIR)/$(PREFIX)/bin/
	mkdir -p $(DESTDIR)/var/db/pkgctl/pkgctl
	cp $(FILES) $(DESTDIR)/var/db/pkgctl/pkgctl/FILES
	echo $(VERSION) > $(DESTDIR)/var/db/pkgctl/pkgctl/VERSION
	echo $(PKGNAME) > $(DESTDIR)/var/db/pkgctl/pkgctl/PKGNAME
