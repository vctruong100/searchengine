#!/bin/bash
#
# scripts/realign.sh
#
# realigns the tab width from files that use spaces for indentation
# the first 3 args must be specified
#
# usage: scripts/realign.sh (old_width) (new_width) (file_1) [(file_2), ...]
#
# old_width: old width for space indentation
# new_width: new width for space indentation
# file_X: files to specify

if [ $# -lt 3 ]; then
	echo "error: too few args specified"
	exit 1
fi

# for each arg starting from file_1
# convert space indentations based on old_width and new_width
for ((i = 3; i <= $#; i++)); do
	if ! [ -f "${!i}" ]; then
		printf "error: arg $i = \"${!i}\" is not a file\n"
		continue
	fi
	unexpand -t $1 --first-only < "${!i}" > .realign.sh.tmp
	expand -it $2 < .realign.sh.tmp > "${!i}"
done

# clean up
rm -f .realign.sh.tmp
