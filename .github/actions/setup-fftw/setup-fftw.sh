#!/bin/bash -eu

# mac-latest -> mac
# ubuntu-latest -> ubuntu
os=${1%-*}

setup-apt-fftw () {
    sudo apt update && sudo apt install -y -q libfftw3-dev
}

setup-brew-fftw () {
    brew install fftw
}

setup-env-fftw () {
    case "$os" in
	mac)
	    prefix=$(brew --prefix fftw)
	    echo "include-dir=$prefix/include" >> "$GITHUB_OUTPUT"
	    echo "library-dir=$prefix/lib" >> "$GITHUB_OUTPUT"
	    ;;
	ubuntu)
	    echo "include-dir=/usr/include" >> "$GITHUB_OUTPUT"
	    echo "library-dir=/usr/lib/x86_64-linux-gnu" \
		 >> "$GITHUB_OUTPUT"
	    ;;
    esac
}

case $(uname) in
    Linux)
	setup-apt-fftw
	;;
    Darwin)
	setup-brew-fftw
	;;
esac

setup-env-fftw
