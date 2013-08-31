Sublime File Concatenator
=========================

Automatically concatenates all dependencies based on simple rules you specify in the referenced files.

## Getting started ##

### Using Package Control ###
(In the workings....)
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
