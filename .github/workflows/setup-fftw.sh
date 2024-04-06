#!/bin/bash -eu

echo num args $#

echo "called with $1"

# mac-latest -> mac
# ubuntu-latest -> ubuntu

os=mac-latest

setup-apt-fftw () {
    sudo apt update && sudo apt install -y -q libfftw3-dev
}

setup-brew-fftw () {
    brew install fftw
}

setup-env-fftw () {
    case "$os" in
	mac)
	    echo "FFTW_ROOT=$(brew --prefix fftw)" >> "$GITHUB_ENV"
	    ;;
	ubuntu)
	    # Paths picked up automatically.
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
