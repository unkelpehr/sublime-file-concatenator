import sublime, sublime_plugin, re, os
from reporter import *

SETTINGS_FILE = "concatenator.sublime-settings"

#
# Concatenator
#
class ConcatenatorCommand(sublime_plugin.TextCommand):
    concatenated_files  = []
    output_filename     = ''

    #
    # We'll use the same regex rules for matching @imports and @partofs to keep it concistent.
    # 
    re_import = '(?![\r\n])+(\s*)(?://|#|/\*)?(?:\s*)@import(?:[\s|url]*)\(\'(.+)\'\)(;?)(\*/)?'
    re_partof = '(?![\r\n])+(\s*)(?://|#|/\*)?(?:\s*)@partof(?:[\s|url]*)\(\'(.+)\'\)(;?)(\*/)?'

    re_import = re.compile(r'''
        (                       # Full replace part
            (?:\s*[\r\n])*      # Don't match linebreaks or intendated linebreaks
            (\s*)               # Capture any whitespace (intendation)
            (?://|\#|/\*)?      # Non-capture any possible beginning of comment
            (?:\s*)             # Whitespace zero or more times
            @import             # Type (import/partof)
            (?:[\s|url])*       # Match whitespace or 'url' zero or more times
            \(\'(.+)\'\)        # Match the file part ('myfile.js') 1 or more times
            (?:\;|\*|$)?        # Match ending comment, or end of line
        )
    ''', re.VERBOSE | re.MULTILINE | re.IGNORECASE)

    re_partof2 = re.compile(r'''
        (                       # Full replace part
            (?:\s*[\r\n])*      # Don't match linebreaks or intendated linebreaks
            (\s*)               # Capture any whitespace (intendation)
            (?://|\#|/\*)?      # Non-capture any possible beginning of comment
            (?:\s*)             # Whitespace zero or more times
            @import             # Type (import/partof)
            (?:[\s|url])*       # Match whitespace or 'url' zero or more times
            \(\'(.+)\'\)        # Match the file part ('myfile.js') 1 or more times
            (?:\;|\*|$)?        # Match ending comment, or end of line
        )
    ''', re.VERBOSE | re.MULTILINE | re.IGNORECASE)

    #
    # run-method
    # Executed from key-bindings, menu, etc,
    #
    def run(self, edit):
        self.is_running = True

        # Reset
        self.concatenated_files  = []
        self.output_filename     = ''

        if self.view.find(self.re_partof, 0):
            content = self.view.substr(sublime.Region(0, self.view.size()))
            portion = sublime.load_settings(SETTINGS_FILE).get('partof_line_portion', 15)

            if portion == 0: 
                lines = content.splitlines()
            else:
                lines = content.splitlines()[:portion]

            content = '\n'.join(lines)

            for match in re.finditer(self.re_partof, content):
                fullmatch = match.group(0)
                indentation = match.group(1)
                filename = match.group(2)

                self.concat(os.sep.join(self.view.file_name().split(os.sep)[0:-1]) + os.sep + filename)
        else:
            self.concat(self.view.file_name())

        self.is_running = False

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

                self.concatenated_files.append(filename)

                # Get contents, by list of lines
                lines = self.file_get_contents(''.join([filepath, os.sep, filename]), True)

                # Apply indentation
                if settings.get('apply_intendation', False) == True:
                    lines = [indentation + line for line in lines]

                # Convert to string
                lines = ''.join(lines).encode("utf-8")

                # Remove all instances of @partof
                lines = re.sub(self.re_partof, '', lines)

                # And replace the content
                content = content.replace(fullmatch, lines)

            # Copy the raw source into the new file
            handle.writelines(content)

            # Close handle
            handle.close()
        else:
            print 'Concatenator: No commands found in ' + rootFile

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