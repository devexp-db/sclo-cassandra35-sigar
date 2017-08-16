%{?scl:%scl_package sigar}
%{!?scl:%global pkg_name %{name}}

Name:		%{?scl_prefix}sigar
Version:	1.6.5
Release:	0.17.git58097d9%{?dist}
Summary:	System Information Gatherer And Reporter

%global sigar_suffix  0-g4b67f57
%global sigar_hash    58097d9

# Use the same directory of the main package for subpackage licence and docs
%global _docdir_fmt %{pkg_name}

License:	ASL 2.0
URL:		http://sigar.hyperic.com/

# Once 1.6.5 is released, we can use tarballs from GitHub:
#    Source0:	http://download.github.com/hyperic-sigar-{name}-{version}-{sigar_suffix}.tar.gz
#
# Until then the tarball can be re-generated with:
#    git clone git://github.com/hyperic/sigar.git
#    cd sigar
#    git archive --prefix=sigar-1.6.5/ 833ca18 | bzip2 > sigar-1.6.5-833ca18.tbz2
#
# The diff from 1.6.4 is too huge to contemplate cherrypicking from
Source0:	%{pkg_name}-%{version}-%{sigar_hash}.tbz2

# originally taken from http://repo1.maven.org/maven2/org/fusesource/sigar/1.6.4/sigar-1.6.4.pom
Source1:	%{pkg_name}-template-pom.xml

BuildRequires:	gcc
BuildRequires:	cmake
BuildRequires:	perl
BuildRequires:	%{?scl_prefix}cpptasks
BuildRequires:	%{?scl_prefix_maven}javapackages-local
BuildRequires:	%{?scl_prefix_java_common}ant
%if 0%{?fedora} > 20
BuildRequires:	log4j12
%else
BuildRequires:	%{?scl_prefix_java_common}log4j
%endif
%{?scl:Requires: %scl_runtime}

Patch100:	bz714249-1-cpu-count.patch
Patch101:	bz746288-1-cpu-count-arch.patch
# use system libraries
# build only linux jni libraries
Patch120:	%{pkg_name}-%{version}-java_build.patch

# AArch64 is 64-bit only so no -m64
Patch130:	aarch64-no-m64.patch

%description
The Sigar API provides a portable interface for gathering system
information such as:
- System memory, swap, CPU, load average, uptime, logins
- Per-process memory, CPU, credential info, state, arguments,
  environment, open files
- File system detection and metrics
- Network interface detection, configuration info and metrics
- Network route and connection tables

This information is available in most operating systems, but each OS
has their own way(s) providing it. SIGAR provides developers with one
API to access this information regardless of the underlying platform.

#The core API is implemented in pure C with bindings currently
#implemented for Java, Perl and C#.

%package devel 
License:	ASL 2.0
Group:		Development/Libraries
Summary:	SIGAR Development package - System Information Gatherer And Reporter
Requires:	%{pkg_name} = %{version}-%{release}
BuildArch:	noarch

%description devel
Header files for developing against the Sigar API

%package java
Summary:	SIGAR Java bindings

%description java
This package contains the Java bindings SIGAR.

%package javadoc
Summary:	Javadoc for SIGAR Java bindings
BuildArch:	noarch

%description javadoc
This package contains javadoc for SIGAR Java bindings.

%prep
# When using the GitHub tarballs, use:
# setup -q -n hyperic-{name}-{sigar_hash}
%setup -q -n %{pkg_name}-%{version}

%patch100 -p1
%patch101 -p1

%patch120 -p1
%patch130 -p1
# clean up
find . -name "*.class" -delete
find . -name "*.jar" -delete
cp -p %{SOURCE1} bindings/java/pom.xml
sed -i "s|@VERSION@|%{version}|" bindings/java/pom.xml
%if 0%{?fedora} > 20
sed -i.log4j12 "s|log4j.jar|log4j12-1.2.17.jar|" bindings/java/build.xml
%endif

%{?scl:scl enable %{scl_maven} %{scl} - << "EOF"}
%if 0%{?fedora} > 20
build-jar-repository bindings/java/lib log4j12-1.2.17
%else
build-jar-repository bindings/java/lib log4j
%endif
build-jar-repository bindings/java/lib ant/ant
build-jar-repository bindings/java/hyperic_jni/lib/ ant/cpptasks
%{?scl:EOF}

%build

# Fix lib directory
sed -i 's|DESTINATION lib|DESTINATION %{_lib}|' src/CMakeLists.txt

mkdir build
pushd build
# FIXME: Package suffers from c11/inline issues
# Workaround by appending --std=gnu89 to CFLAGS
# Proper fix would be to fix the source-code
CFLAGS="${RPM_OPT_FLAGS} --std=gnu89"
%cmake ..
make %{?_smp_mflags}
popd

pushd bindings/java
%{?scl:scl enable %{scl_maven} %{scl} - << "EOF"}
%mvn_file org.fusesource:%{pkg_name} %{pkg_name}
%ant build javadoc
%mvn_artifact pom.xml %{pkg_name}-bin/lib/%{pkg_name}.jar
%{?scl:EOF}
popd

%install

pushd build
%cmake ..
make install DESTDIR=%{buildroot}
popd

pushd  bindings/java
%{?scl:scl enable %{scl_maven} %{scl} - << "EOF"}
%mvn_install -J build/javadoc
%{?scl:EOF}
mkdir -p %{buildroot}%{_libdir}/%{pkg_name}
install -pm 755 %{pkg_name}-bin/lib/libsigar-*.so \
  %{buildroot}%{_libdir}/%{pkg_name}/
popd

%post -p /sbin/ldconfig

%postun -p /sbin/ldconfig

%files
%license LICENSE
%doc ChangeLog README NOTICE AUTHORS
%{_libdir}/libsigar.so

%files devel
%{_includedir}/sigar*.h
%license LICENSE
%doc NOTICE AUTHORS

%files java -f bindings/java/.mfiles
%{_libdir}/%{pkg_name}
%license LICENSE
%doc NOTICE

%files javadoc -f bindings/java/.mfiles-javadoc
%license LICENSE
%doc NOTICE bindings/java/examples

%changelog
* Wed Nov 16 2016 Tomas Repik <trepik@redhat.com> - 1.6.5-0.17.git58097d9
- scl conversion

* Thu Feb 04 2016 Fedora Release Engineering <releng@fedoraproject.org> - 1.6.5-0.16.git58097d9
- Rebuilt for https://fedoraproject.org/wiki/Fedora_24_Mass_Rebuild

* Mon Jun 22 2015 Ralf Corsépius <corsepiu@fedoraproject.org> - 1.6.5-0.15.git58097d9
- Append --std=gnu89 to CFLAGS (Work-around to c11/inline compatibility
  issues. Fix FTBFS).

* Fri Jun 19 2015 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 1.6.5-0.14.git58097d9
- Rebuilt for https://fedoraproject.org/wiki/Fedora_23_Mass_Rebuild

* Mon Jan 19 2015 Marcin Juszkiewicz <mjuszkiewicz@redhat.com> - 1.6.5-0.13.git58097d9
- fixed fix to build on aarch64 (#1183634)

* Fri Sep 05 2014 gil cattaneo <puntogil@libero.it> 1.6.5-0.12.git58097d9
- Added java bindings sub packages (rhbz#872103)
- Minor changes to current guideline
- Make -devel and -docs subpackages noarch

* Mon Aug 18 2014 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 1.6.5-0.11.git58097d9
- Rebuilt for https://fedoraproject.org/wiki/Fedora_21_22_Mass_Rebuild

* Sun Jun 08 2014 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 1.6.5-0.10.git58097d9
- Rebuilt for https://fedoraproject.org/wiki/Fedora_21_Mass_Rebuild

* Sun Aug 04 2013 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 1.6.5-0.9.git58097d9
- Rebuilt for https://fedoraproject.org/wiki/Fedora_20_Mass_Rebuild

* Thu Feb 14 2013 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 1.6.5-0.8.git58097d9
- Rebuilt for https://fedoraproject.org/wiki/Fedora_19_Mass_Rebuild

* Sat Jul 21 2012 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 1.6.5-0.7.git58097d9
- Rebuilt for https://fedoraproject.org/wiki/Fedora_18_Mass_Rebuild

* Sat Jan 14 2012 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 1.6.5-0.6.git58097d9
- Rebuilt for https://fedoraproject.org/wiki/Fedora_17_Mass_Rebuild

* Fri Oct 21 2011 Zane Bitter <zbitter@redhat.com> - 1.6.4-0.5.git833ca18
- Get correct CPU counts on non-x86 architectures

* Mon Aug 29 2011 Zane Bitter <zbitter@redhat.com> - 1.6.5-0.4.git833ca18
- Get CPU counts from /proc/cpuinfo
  Resolves: #714249

* Wed Feb 09 2011 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 1.6.5-0.2.git833ca18
- Rebuilt for https://fedoraproject.org/wiki/Fedora_15_Mass_Rebuild

* Thu Dec 16 2010 Andrew Beekhof <andrew@beekhof.net> - 1.6.5-0.1.git833ca18
- Incorporate review feedback
  + Add calls to ldconfig
  + Fix package group
  + Resolve rpmlint warnings
  + Added LICENSE, NOTICE and AUTHORS to the doc list
  + Document how the tarball was generated
  + Update version number to be a .5 pre-release snapshot

* Wed Dec 1 2010 Andrew Beekhof <andrew@beekhof.net> - 1.6.4-1
- Initial checkin
