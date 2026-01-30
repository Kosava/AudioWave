Name: audiowave
Version: 0.3.0
Release: 1%{?dist}
Summary: Modern desktop audio player written in Python

License: MIT
URL: https://github.com/Kosava/AudioWave
Source0: %{url}/archive/v%{version}.tar.gz

BuildArch: noarch

Requires: python3 >= 3.11
Requires: python3-qt6
Requires: python3-mutagen
Requires: gstreamer1
Requires: gstreamer1-plugins-base
Requires: gstreamer1-plugins-good

%description
AudioWave is a modern, lightweight desktop music player written in Python.
It features playlist management, plugin support, theming, and tray controls.

%prep
%autosetup -n AudioWave-%{version}

%build

%install
mkdir -p %{buildroot}/usr/lib/audiowave
cp -r core ui plugins utils resources audiowave.py main.py requirements.txt \
    %{buildroot}/usr/lib/audiowave

mkdir -p %{buildroot}/usr/bin
install -m 755 packaging/audiowave %{buildroot}/usr/bin/audiowave

mkdir -p %{buildroot}/usr/share/applications
install -m 644 packaging/rpm/audiowave.desktop \
    %{buildroot}/usr/share/applications/audiowave.desktop

mkdir -p %{buildroot}/usr/share/pixmaps
install -m 644 resources/icons/audiowave_color.png \
    %{buildroot}/usr/share/pixmaps/audiowave.png

%files
/usr/lib/audiowave
/usr/bin/audiowave
/usr/share/applications/audiowave.desktop
/usr/share/pixmaps/audiowave.png

%changelog
* Mon Jan 01 2026 Kosava - 0.3.0-1
- Initial package
