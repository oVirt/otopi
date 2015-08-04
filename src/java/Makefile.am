#
# otopi -- plugable installer
# Copyright (C) 2012-2013 Red Hat, Inc.
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA
#

artifact=otopi
generate=otopi.constants

targetdir=$(abs_top_builddir)/target
jarname=$(artifact)-$(PACKAGE_MAVEN_VERSION).jar
targetjar=$(targetdir)/$(jarname)

MAINTAINERCLEANFILES = \
	$(srcdir)/Makefile.in \
	$(NULL)
CLEANFILES = \
	tmp.generated \
	$(targetjar) \
	$(NULL)

EXTRA_DIST = \
	.gitignore \
	$(NULL)

dist_noinst_DATA = \
	Event.java \
	MANIFEST.MF \
	MachineDialogParser.java \
	MachineDialogParserTest.java \
	SoftError.java \
	$(NULL)

if JAVA_SDK

if JAVA_SDK_COMPILE
all-local:	\
		$(targetjar) \
		$(NULL)
else
all-local:	\
		sources \
		$(NULL)
endif

clean-local:
	rm -fr src target tmp.*

if WITH_MAVEN

$(targetjar):	\
		sources \
		pom.xml \
		$(NULL)
	rm -f "$(targetjar)"
	$(MKDIR_P) "$(targetdir)"
	$(MVN) \
		-D altDeploymentRepository=install::default::file://$(targetdir)/maven \
		deploy
	cp "$(targetdir)/maven/org/ovirt/$(PACKAGE_NAME)/$(artifact)/$(PACKAGE_MAVEN_VERSION)$(MAVEN_VERSION_SNAPSHOT)"/$$(echo $(jarname) | sed 's/\.jar/*.jar/') "$(targetdir)"

else

$(targetjar):	\
		sources \
		$(NULL)
	rm -f "$(targetjar)"
	$(MKDIR_P) "$(targetdir)"
	$(MKDIR_P) target
	$(JAVAC) -source 1.5 -target 1.5 -cp $(COMMONS_LOGGING_JAR):$(JUNIT_JAR) -d target `find src -name '*.java'`
	$(JAR) -cmf $(srcdir)/MANIFEST.MF "$(targetjar)" -C target .

endif

sources: \
	tmp.generated \
	src/main/java/org/ovirt/otopi/dialog/Event.java \
	src/main/java/org/ovirt/otopi/dialog/MachineDialogParser.java \
	src/main/java/org/ovirt/otopi/dialog/SoftError.java \
	src/test/java/org/ovirt/otopi/dialog/MachineDialogParserTest.java \
	$(NULL)

# TODO: kill __main__ when python-2.6 gone
tmp.generated:
	rm -f tmp.generated
	PYTHONPATH="$(top_srcdir)/src:${PYTHONPATH}" $(PYTHON) \
		-m otopi.codegen.__main__ \
		src/main/java \
		org.ovirt \
		$(generate)
	PYTHONPATH="$(top_srcdir)/src:$(top_srcdir)/src/plugins/otopi:${PYTHONPATH}" $(PYTHON) \
		-m otopi.codegen.__main__ \
		src/main/java \
		org.ovirt.otopi \
		dialog.constants
	touch tmp.generated

src/main/java/org/ovirt/otopi/dialog/Event.java: $(srcdir)/Event.java
	mkdir -p src/main/java/org/ovirt/otopi/dialog
	cp "$(srcdir)/Event.java" src/main/java/org/ovirt/otopi/dialog/Event.java

src/main/java/org/ovirt/otopi/dialog/SoftError.java: $(srcdir)/SoftError.java
	mkdir -p src/main/java/org/ovirt/otopi/dialog
	cp "$(srcdir)/SoftError.java" src/main/java/org/ovirt/otopi/dialog/SoftError.java

src/main/java/org/ovirt/otopi/dialog/MachineDialogParser.java: $(srcdir)/MachineDialogParser.java
	mkdir -p src/main/java/org/ovirt/otopi/dialog
	cp "$(srcdir)/MachineDialogParser.java" src/main/java/org/ovirt/otopi/dialog/MachineDialogParser.java

src/test/java/org/ovirt/otopi/dialog/MachineDialogParserTest.java: $(srcdir)/MachineDialogParserTest.java
	mkdir -p src/test/java/org/ovirt/otopi/dialog
	cp "$(srcdir)/MachineDialogParserTest.java" src/test/java/org/ovirt/otopi/dialog/MachineDialogParserTest.java

endif
