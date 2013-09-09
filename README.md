Sublime File Concatenator
=========================

This project has been put on ice due to recent lack of time. Contributions will be handled but I can at the moment not spend more time developing it.
-------------------------------------------------------------------------------------------------------------
-------------------------------------------------------------------------------------------------------------









Automatically concatenates all dependencies based on simple rules you specify in the referenced files.

## Getting started ##

### Using Package Control ###
(Not supported)
The easiest way to get started is to install the package using [Sublime Package Control](https://sublime.wbond.net/).

Open the pallete by pressing *CTRL + SHIFT + P* (Win, Linux) or *CMD + SHIFT + P (OS X*). Type **install** and the command palette should filter down **Package Control: Install Package**.
Select this command by either clicking on it, or using your cursor keys to highlight it and pressing Enter. 

In the pallete that follows type **Concat** and look for **File Concatenator**. Select this command in the same manner as before and when the installation is finished you are good to go!

## Manual install ##
If you for some reason cannot or will not use [Package Control](https://sublime.wbond.net/), you can install the plugin manually be using the instructions below.

 1. Click the *Preferences > Browse Packages…* menu
 2. Browse up a folder and then into the *Installed Packages/ folder*
 3. Download [master.zip](https://github.com/unkelpehr/sublime-file-concatenator/archive/master.zip) and copy it into the *Installed Packages/* directory
 4. Restart Sublime Text

## Documentation ##

There is only two commands you need to use this plugin: @import and @partof.

###@import###
xxx

###@partof###
xxx

*CTRL + SHIFT + C* or *CMD + Shift + C* will start the concatenation process. You can also specify concatenation on Save; this is enabled as default for JavaScript and CSS files. Check out the settings file via *Preferences -> Package Settings -> Concatenator -> Settings - User*.

## Contribute! ##
 1. Fork it.
 2. Create a branch (git checkout -b sublime_file_concatenator)
 3. Commit your changes (git commit -am "Fixed regex...")
 4. Push to the branch (git push origin sublime_file_concatenator)
 5. Open a Pull Request
 5. Tada!

## Changelog ##
###v0.8.5###
 1. Added changelog
 2. Added popup for referenced files that could not be found.
 3. Added 'popup_files_not_found'-setting
 4. Added tests
 5. Fixed bug that didn't reset certain variables each run
 6. Cleaned up the regex's and the general code a bit
 7. **Added support for multi-level @partof**


###v0.8.0###
Initial release
