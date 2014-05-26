Sublime File Concatenator
-------------------------------------------------------------------------------------------------------------

Automatically concatenates all dependencies based on simple rules you specify in the referenced files.

**Main features:**
1. Multi-level importing: @import(*filepath*)
2. Multi-level referencing: @partof(*filepath*)
3. Importing through glob: @import('glob:components/*.js)
4. Per-file specific settings: @option('setting_key', 'new_setting_value')
5. Per-file output-control: @saveto('../../lib.js')
6. Generalized templating for controlling headers, footers, output filenames and more
7. Small (~400 SLOC)
8. Compatible through Sublime 2.x to Sublime 3.x 

## Getting started ##

### Using Package Control ###
(Not yet supported)
The easiest way to get started is to install the package using [Sublime Package Control](https://sublime.wbond.net/).

Open the pallete by pressing *CTRL + SHIFT + P* (Win, Linux) or *CMD + SHIFT + P (OS X*). Type **install** and the command palette should filter down **Package Control: Install Package**.
Select this command by either clicking on it, or using your cursor keys to highlight it and pressing Enter. 

In the pallete that follows type **Concat** and look for **File Concatenator**. Select this command in the same manner as before and when the installation is finished you are good to go!

## Manual install ##
If you for some reason cannot or will not use [Package Control](https://sublime.wbond.net/), you can install the plugin manually be using the instructions below.

 1. Click the *Preferences > Browse Packages…* menu
 2. Download [master.zip](https://github.com/unkelpehr/sublime-file-concatenator/archive/master.zip) and unpack it into the *Packages/* directory
 3. Restart Sublime Text

## Documentation ##
The plugin works by analysing the targeted file for certain commands. If found, it will be executed and stripped from the source code before writing the finished concatenated file. There are four commands available:

###@import(*filepath*)###
The only command you'll really need for small projects. Replaces the @import(*filepath*)-line with the contents of *filepath*.

**C:\wwwroot\main.js**
```
// Dependency1.js
@import('components/dependency1.js')
```

**C:\wwwroot\components\dependency1.js**
```
+-----------------------------+
|                             |
| Hello! I am dependency1.js! |
|                             |
+-----------------------------+
```

**C:\wwwroot\main.cat.js**
```
// Dependency1.js
+-----------------------------+
|                             |
| Hello! I am dependency1.js! |
|                             |
+-----------------------------+
```

###@partof(*filepath*)###
Tells the intepreter to look for references of this file in *filepath*.
This allows for the concatenation progress to start from both the parent (main.js) and the child (dependency1.js):
**dependency1.js**
```
@partof('../main.js')
+-----------------------------+
|                             |
| Hello! I am dependency1.js! |
|                             |
+-----------------------------+
```

###@saveto(*filepath*)###
The default behaviour is to save the concatenated file in the same directory as the source file.
You can easily specify an alternative path by using the @saveto-command:

**C:\wwwroot\main.js**
```
// Dependency1.js
@import('components/dependency1.js')
@saveto('builds/main.js')
```

In the example above we also gave it a specific name. If we had just specified the 'builds/'-folder the name given had been as per the "tpl_output_filename-setting" (more on that below).

If the directory does not exist the plugin will ask if you want it to create it for you.

###@option(*key*, *value*)###
Sublime File Concatenator has very a extensive and flexible settings file. But because of the nature of this plugin, all settings can't apply very good to all files and projects at all times.

By using the @option-command you can temporarily overwrite the global plugin settings.
Settings specified via @option only apply the file that is currently being handled and gets removed when the file has finished parsing or when a value of "default" has been passed.

**C:\wwwroot\main.js**
```
// Dependency1.js
@import('components/dependency1.js')
@saveto('builds/') // Here we choose only to specify an directory for output
@option('tpl_output_filename', '{{this.fileroot}}-{{system.date}}.{{this.extension}}')
```

**C:\wwwroot\builds\main-2014-05-26.js**
```
// Dependency1.js
+-----------------------------+
|                             |
| Hello! I am dependency1.js! |
|                             |
+-----------------------------+
```

###glob:###
This magic prefix activates [Python's glob module](https://docs.python.org/2/library/glob.html) and passes your argument directly to it. Whatever comes out, gets imported.

**C:\wwwroot\main.js**
```
// My dependencies:
@import('glob:components/*.js') // Import all Javascript-files in the components-directory 
@saveto('builds/')
@option('tpl_output_filename', '{{this.fileroot}}-{{system.date}}.{{this.extension}}')
```
**C:\wwwroot\builds\main-2014-05-26.js**
```
// My dependencies:
+-----------------------------+
|                             |
| Hello! I am dependency1.js! |
|                             |
+-----------------------------+
+-----------------------------+
|                             |
| Hello! I am dependency2.js! |
|                             |
+-----------------------------+
```

###Starting the concatenation process###
*CTRL + SHIFT + C* or *CMD + Shift + C* will start the concatenation process. You can also specify concatenation on Save, read more under the Settings-section below.

###The settings file###
1. Open  the default settings via *Preferences -> Package Settings -> File Concatenator -> Settings - Default*.
2. Copy the contents into *Preferences -> Package Settings -> File Concatenator -> Settings - User*

There is *a lot* of documentation in the settings file. Don't be put of though, it's actually really easy.

## Contribute! ##
 1. Fork it.
 2. Create a branch (git checkout -b sublime_file_concatenator)
 3. Commit your changes (git commit -am "Fixed regex...")
 4. Push to the branch (git push origin sublime_file_concatenator)
 5. Open a Pull Request
 5. Tada!

## Changelog ##
###v0.9.5###
 1. Removed 'popup_files_not_found'-setting *(always pops)*
 2. Added *trim_parents*-setting
 3. Added *trim_children*-setting
 4. Added *date_format*-setting
 5. Added *time_format*-setting
 6. Added {{mustasche_style}}-templating options accessable via the settings, with a great number of namespaced variables.
 7. Added @saveto-method
 8. Added @option-method
 9. Added glob:-prefix
 10. Added multi-level @import
 11. Added optimizations which greatly improved overall runtime
     
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
