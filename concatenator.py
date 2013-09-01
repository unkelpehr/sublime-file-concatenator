import sublime, sublime_plugin, re, os
from reporter import *

SETTINGS_FILE = "concatenator.sublime-settings"

#
# Concatenator
#
class ConcatenatorCommand(sublime_plugin.TextCommand):
    message_header = 'Sublime File Concatenator\n====================\n\n' 
    concatenated_files  = []
    files_not_found     = []
    output_filename     = ''

    maximum_recursion = 10
    current_recursion = 0

    #
    # We'll use the excct same regex for matching @imports and @partofs to keep it concistent.
    # 

    re_import = re.compile(r'''
        (                       # Full replace part
            (?:\s*[\r\n])*      # Don't match linebreaks or intendated linebreaks
            (\s*)               # Capture any whitespace (intendation)
            (?://|\#|\/\*)?     # Non-capture any possible beginning of comment
            (?:\s*)             # Whitespace zero or more times
            @import             # Type (import/partof)
            (?:[\s|url])*       # Match whitespace or 'url' zero or more times
            \(\'(.+)\'\)        # Match the file part ('myfile.js') 1 or more times
            (?:\;|\*/|$)?       # Match ending comment, or end of line
        )
    ''', re.VERBOSE | re.MULTILINE | re.IGNORECASE)

    re_partof = re.compile(r'''
        (                       # Full replace part
            (?:\s*[\r\n])*      # Don't match linebreaks or intendated linebreaks
            (\s*)               # Capture any whitespace (intendation)
            (?://|\#|\/\*)?     # Non-capture any possible beginning of comment
            (?:\s*)             # Whitespace zero or more times
            @partof             # Type (import/partof)
            (?:[\s|url])*       # Match whitespace or 'url' zero or more times
            \(\'(.+)\'\)        # Match the file part ('myfile.js') 1 or more times
            (?:\;|\*/|$)?       # Match ending comment, or end of line
        )
    ''', re.VERBOSE | re.MULTILINE | re.IGNORECASE)

    #
    # run-method
    # Executed from key-bindings, menu, etc
    #
    def run(self, edit, targetFile = False):
        self.is_running = True

        if targetFile == False:
            targetFile = self.view.file_name()

        # Reset
        self.concatenated_files  = []
        self.files_not_found     = []
        self.output_filename     = ''
        self.current_recursion = 0

        # Look for @partof's on the first N lines
        content = self.file_get_contents(targetFile, False)
        portion = sublime.load_settings(SETTINGS_FILE).get('partof_line_portion', 15)
        content = '\n'.join(content.splitlines() if portion == 0 else content.splitlines()[:portion])
        matches = self.re_partof.findall(content)

        # Look out for infinite loops
        if self.current_recursion >= self.maximum_recursion:
            sublime.error_message(self.message_header + 'Recursion limit (' + str(self.maximum_recursion) + ') met')
            return
        self.current_recursion += 1

        # @partof or @import?
        if len(matches) > 0:
            for match in matches:
                fullmatch, indentation, filename = match

                self.run(self, os.sep.join(targetFile.split(os.sep)[0:-1]) + os.sep + filename)
        else:
            self.concat(targetFile)

        self.is_running = False

        # Notify about files not found
        if sublime.load_settings(SETTINGS_FILE).get('popup_files_not_found', True) == True:
            num_files_not_found = len(self.files_not_found)
            str_files_not_found = ''
            if num_files_not_found > 0:
                for oList in self.files_not_found:
                    str_files_not_found += oList[0] + ', referer: ' + oList[1] + '\n'
                sublime.message_dialog(self.message_header + str(num_files_not_found) + ' referenced ' + ('files' if num_files_not_found > 1 else 'file') + ' could not be found:\n\n' + str_files_not_found)

        # Update status message
        leftovers = len(self.concatenated_files) - 3
        filenames = ', '.join(["'" + name + "'" for name in self.concatenated_files[:3]])

        sublime.set_timeout(lambda: sublime.status_message('Concatenated ' + filenames + (' and ' + str(leftovers) + ' more' if leftovers > 0 else '') + " into '" + self.output_filename + "'."), 0)

    #
    # Helper method used by Reporter()
    #
    def update_status(self, msg, progress):
        sublime.status_message(msg + progress)

    #
    # Helper method to return the contents of a file
    #
    def file_get_contents(self, filepath, splitLines):
        content = ''
        try:
            handle = open(filepath, 'r')
            try:
                if splitLines:
                    content = handle.readlines()
                else:
                    content = handle.read()
            finally:
                handle.close()
        except IOError:
            pass

        return content

    #
    # Main concat-method
    #
    def concat(self, rootFile):
        # Get file contents
        content = self.file_get_contents(rootFile, False)
        matches = self.re_import.findall(content)
        matchlen = len(matches)

        # Got match?
        if matchlen:
            # Get user settings
            settings = sublime.load_settings(SETTINGS_FILE)

            # Determine file information
            filepath    = os.sep.join(rootFile.split(os.sep)[0:-1])
            filename    = rootFile.split(os.sep)[-1]
            extension   = filename.split('.')[-1]

            Reporter('Starting concatenation for ' + filepath, self)

            # Get output file formatting rules
            prefix = settings.get('prefix_output_file', '')
            suffix = settings.get('suffix_output_file', '')
            prefix_ext = settings.get('prefix_output_file_extension', '.')

            # Safety net so that we don't overwrite the original
            if prefix == '' and suffix == '' and prefix_ext == '':
                prefix_ext = '.cat.'

            if prefix_ext == '':
                prefix_ext = '.'

            self.output_filename = prefix + '.'.join(filename.split('.')[0:-1]) + prefix_ext + extension + suffix

            # The w-flag will create a new file or overwrite an existing file.
            handle = open(filepath + os.sep + self.output_filename, 'w')

            # Loop matches
            for match in matches:
                fullmatch, indentation, filename = match

                tmp_filepath = ''.join([filepath, os.sep, filename])
                lines = ''

                # Skip if the file does not exist
                if os.path.isfile(tmp_filepath):
                    # Append to history
                    self.concatenated_files.append(filename)

                    # Get contents, by list of lines
                    lines = self.file_get_contents(tmp_filepath, True)

                    # Apply indentation
                    if settings.get('apply_intendation', False) == True:
                        lines = [indentation + line for line in lines]

                    # Convert to string
                    lines = ''.join(lines).encode("utf-8")

                    # Remove all instances of @partof
                    lines = re.sub(self.re_partof, '', lines)
                else:
                    self.files_not_found.append(["'" + filename + "'", "'" + rootFile.split(os.sep)[-1] + "'"])

                # Replace the full match with the target
                content = content.replace(fullmatch, lines)

            # Copy the raw source into the new file
            handle.writelines(content)

            # Close handle
            handle.close()

#
# Event listener for post-save
#
class ConcatenatorEventListener(sublime_plugin.EventListener):

    def on_post_save(self, view):
        settings = sublime.load_settings(SETTINGS_FILE)
        
        # Should the concat on save?
        if settings.get('run_on_save', False) == False:
            return
            
        # Is the current extension set to be ran on save?
        if view.file_name().split('.')[-1] not in settings.get('run_on_save_extensions', []):
            return

        sublime.active_window().run_command("concatenator")