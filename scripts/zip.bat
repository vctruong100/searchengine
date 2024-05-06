:: scripts/zip.bat
::
:: zips the current git repository
:: excludes patterns defined in .gitignore
:: outputs to "a.zip" by default, if no args were supplied
::
:: usage: scripts/zip.bat [a.zip]

@echo off

if not exist ".git\" (
	echo "error: script must run in git repository"
	exit 1
)

set repo="%cd%"

cd ..
mkdir zip.bat.tmp
cd zip.bat.tmp

git clone -l "%repo%" zip.tmp
cd zip.tmp

:: zip files inside git repo

powershell "Get-ChildItem -Path '.' -Force | Compress-Archive -Force -DestinationPath 'a.zip'"


cd "%repo%"

:: move to "a.zip", if no args supplied
:: otherwise, move to outfile defined in first arg

if not "%1"=="" (
	move /Y ..\zip.bat.tmp\zip.tmp\a.zip "%1"
	goto continue2
)
move /Y ..\zip.bat.tmp\zip.tmp\a.zip a.zip


:continue2

:: clean up
rd /s /q ..\zip.bat.tmp
