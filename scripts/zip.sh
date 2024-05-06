#!/bin/bash
#
# scripts/zip.sh
#
# zips the current git repository
# excludes patterns defined in .gitignore
# outputs to "a.zip" by default, if no args were supplied
#
# usage: scripts/zip.sh [a.zip]

if ! [ -d .git ]; then
	echo "error: script must run in git repository"
	exit 1
fi

repo=$(pwd)

cd ..
mkdir zip.sh.tmp
cd zip.sh.tmp

git clone -l --no-hardlinks "$repo" zip.tmp
cd zip.tmp

# zip files inside git repo
if ! [ -z $(command -v zip) ]; then
	zip -r a.zip .
elif ! [ -z $(command -v powershell) ]; then
	# windows
	# use powershell Compress-Archive
	powershell "Get-ChildItem -Path '.' -Force |"\
"Compress-Archive -Force -DestinationPath 'a.zip'"
else
	echo "error: no zip command found"
	exit 1
fi

cd "$repo"

# move to "a.zip", if no args supplied
# otherwise, move to outfile defined in first arg
if [ $# -eq 1 ]; then
	mv -f ../zip.sh.tmp/zip.tmp/a.zip "$1"
else
	mv -f ../zip.sh.tmp/zip.tmp/a.zip a.zip
fi

# clean up
rm -rf ../zip.sh.tmp
