%define version	0.2.17
%define release	1
%define name 	xmlindent

Summary: a XML stream reformatter
Name: %{name}
Version: %{version}
Release: %{release}
Copyright: GPL
Group: Text Processing/Markup/XML
Source: http://www.cs.helsinki.fi/u/~penberg/xmlindent/src/xmlindent-%{version}.tar.gz
URL: http://www.cs.helsinki.fi/u/~penberg/xmlindent/
BuildRoot: /var/tmp/%{name}-%{version}
Packager: Pekka Enberg <penberg@iki.fi>

%description
XML Indent is a XML stream reformatter written in ANSI C. It is
analogous to GNU indent.

%prep
%setup

%build
make all

%install
rm -rf $RPM_BUILD_ROOT
make PREFIX="$RPM_BUILD_ROOT/usr" install
  
%clean
rm -rf $RPM_BUILD_ROOT

%files
%defattr(-,root,root)
%{_bindir}/*
%{_mandir}/*/*
