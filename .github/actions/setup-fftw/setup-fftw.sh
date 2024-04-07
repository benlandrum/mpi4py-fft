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
    exit 1
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
	*)
	    echo os "$os" not recognized
	    exit 1
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

echo all outputs $GITHUB_OUTPUT
cat $GITHUB_OUTPUT