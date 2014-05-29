import sublime
import sublime_plugin
import re
import os
import time
import ntpath
import glob

SETTINGS_FILE   = 'FileConcatenator.sublime-settings'
MESSAGE_HEADER  = 'Sublime File Concatenator\n===========================\n\n'

MSG_TYPE = {}
MSG_TYPE['INFO'] 	= 1
MSG_TYPE['WARNING'] 	= 2
MSG_TYPE['ERROR'] 	= 3
MSG_TYPE['FATAL'] 	= 4

#
# Concatenator
# 
# Todo:
#   "Brand" output-file to prevent bad overwrites?
#   Only concat changed files? Some how
#   Add "Increment output file", up to x pieces of them. 0 = don't increment, always overwrite
#   Warn about @(unknown_setting_key, value)
# 
# BUGS
class ConcatenatorCommand(sublime_plugin.TextCommand):
	re_template = re.compile(r''' 
		(?P<outermatch>
			{{
			(?P<namespace>\w+)
			.
			(?P<key>\w+)
			}}
		)
	''', re.VERBOSE | re.IGNORECASE)

	# We'll use the exact same regex for matching @imports and @partofs to keep it concistent.
	re_method = re.compile(r'''
		(\r\n|\n)?                  # Match any linebreak zero or on time
		(                           # Full replace part
			([ \t]*)                # Capture any whitespace or tab (intendation)
			(?://|\#|\/\*)?         # Non-capture any possible beginning of comment
			(?:[ \t]*)              # Non-capture any possible whitespace
			@(import|partof|option|saveto) # Match method
			(?:[ \t|url])*           # Non-capture whitespace or 'url'
			\(([^\)]+)\)            # Match "(" and capture everything up until ")"
			(?:\;|\*/)?             # Non-capture ending comment, or end of line, 
		)
		(\r\n|\n)?                   # Match any linebreak zero or one time
	''', re.VERBOSE | re.IGNORECASE)

	# Instance variables
	jit_settings_dict 		= {}
	jit_rec_settings_dict 	= {}
	log_list 				= []

	log_list_types 			= {}
	log_list_types[1] 		= 0 # Info
	log_list_types[2] 		= 0 # Warning
	log_list_types[3] 		= 0 # Error
	log_list_types[4] 		= 0 # Fatal

	# Function for resetting all instance variables
	def reset_instance (self):
		self.jit_settings_dict.clear()
		del self.log_list[:]
		self.log_list_types[1] = 0 # Info
		self.log_list_types[2] = 0 # Warning
		self.log_list_types[3] = 0 # Error
		self.log_list_types[4] = 0 # Fatal

	# The logging method used throughout the plugin
	def log (self, msg_type, message, file_dict = 0):
		log_entry = ''

		if msg_type == MSG_TYPE['INFO']:
			if file_dict:
				log_entry += file_dict['filename'] + ', '
			log_entry += 'INFO: '
			log_entry += message
		else:
			log_entry += '\n'
			if file_dict:
				log_entry += file_dict['filename'] + ', '
			if msg_type == MSG_TYPE['WARNING']:
				log_entry += 'WARNING: '
			elif msg_type == MSG_TYPE['ERROR']:
				log_entry += 'ERROR: '
			elif msg_type == MSG_TYPE['FATAL']:
				log_entry += 'FATAL: '

			log_entry += message
			log_entry += '\n'

		self.log_list.append(log_entry)

		self.log_list_types[msg_type] += 1

	def get_jit_setting (self, key, file_dict):
		if not file_dict:
			return
		
		file_key = file_dict['realpath']

		if file_key in self.jit_settings_dict and key in self.jit_settings_dict[file_key]:
			return self.jit_settings_dict[file_key][key]
		else:
			for file_key in self.jit_rec_settings_dict:
				if key in self.jit_rec_settings_dict[file_key]:
					return self.jit_rec_settings_dict[file_key][key]

	def push_jit_setting (self, key, value, recursive, file_dict = 0):
		if not file_dict:
			return

		file_key = file_dict['realpath']

		log_msgtype = MSG_TYPE['INFO']
		log_message = ''

		overwrote = False

		if recursive:
			if not file_key in self.jit_rec_settings_dict:
				self.jit_rec_settings_dict[file_key]  = {}

			if key in self.jit_rec_settings_dict[file_key]:
				overwrote = True
				overwrote_val = self.jit_rec_settings_dict[file_key][key]
				overwrote_rec = 'True'

			self.jit_rec_settings_dict[file_key][key] = value
		else:
			if not file_key in self.jit_settings_dict:
				self.jit_settings_dict[file_key]  = {}

			if key in self.jit_settings_dict[file_key]:
				overwrote = True
				overwrote_val = self.jit_settings_dict[file_key][key]
				overwrote_rec = 'False'

			self.jit_settings_dict[file_key][key] = value

		if overwrote:
			log_message = 'Overwrote JIT-setting {"' + key + '": "' + overwrote_val + '", recursive="' + overwrote_rec + '"}, {"' + key + '": "' + value + '", recursive="' + str(recursive) + '"}'
		else:
			log_message = 'Pushed JIT-setting {"' + key + '": "' + value + '", recursive="' + str(recursive) + '"}'

		self.log(log_msgtype, log_message, file_dict)

	def clear_jit_setting (self, key, recursive, file_dict = 0):
		if not file_dict:
			return
		
		file_key = file_dict['realpath']

		if not key == '*':
			log_msgtype = MSG_TYPE['WARNING']
			log_message = 'Tried to clear non-existing JIT-setting "' + key + '"'
		else:
			log_msgtype = MSG_TYPE['INFO']
			log_message = ''

		if recursive:
			if file_key in self.jit_rec_settings_dict:
				if key == '*':
					self.jit_rec_settings_dict[file_key].clear()
					log_message = 'Cleared all JIT-settings recursively'
				elif key in self.jit_rec_settings_dict[file_key]:
					log_message = 'Cleared recursive JIT-setting "' + key + '"'
					self.jit_rec_settings_dict[file_key].pop(key, None)
		else:
			if file_key in self.jit_settings_dict:
				if key == '*':
					self.jit_settings_dict[file_key].clear()
					log_message = 'Cleared all non-recursive JIT-settings recursively'
				elif key in self.jit_settings_dict[file_key]:
					log_message = 'Cleared non-recursive JIT-setting "' + key + '"'
					self.jit_settings_dict[file_key].pop(key, None)

		if log_message:
			self.log(log_msgtype, log_message, file_dict)

	# A helper function to retrieve the behaviour of this plugin.
	# Returns a JIT-setting if available, otherwise a global
	def setting (self, file_dict, key, fallback_value = False):
		jit_setting = self.get_jit_setting(key, file_dict)

		if not jit_setting == None:
			return jit_setting

		return sublime.load_settings(SETTINGS_FILE).get(key, fallback_value)

	# A helper function for formatting size
	def format_bytes (self, bytes):
		for unit in ['B', 'KB', 'MB', 'GB']:
			if bytes < 1024.0:
				return '%3.1f %s' % (bytes, unit)
			bytes /= 1024.0
		return '%3.1f %s' % (bytes, 'TB')


	def parse_string_literals (self, string):
		return (
			string
				.replace('\\\\', '{!~db~!}') 	# Temporarily rename escaped \\ backslashes
				.replace('\\\'', "'") 			# Single quote (')
				.replace('\\\"', '"') 			# Double quote (")
				.replace('\\a', '\a') 			# ASCII Bell (BEL)
				.replace('\\b', '\b') 			# ASCII Backspace (BS)
				.replace('\\f', '\f') 			# ASCII Formfeed (FF)
				.replace('\\n', '\n') 			# ASCII Linefeed (LF)
				.replace('\\r', '\r') 			# ASCII Carriage Return (CR)
				.replace('\\t', '\t') 			# ASCII Horizontal Tab (TAB)
				.replace('\\v', '\v') 			# ASCII Vertical Tab (VT)
				.replace('{!~db~!}', '\\') 		# Revert escaped backslashes
		)

	# Helper method to return the contents of a file
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
			# if exc.errno != errno.ENOENT: raise
			# http://stackoverflow.com/questions/82831/how-do-i-check-if-a-file-exists-using-python
			self.log(MSG_TYPE['FATAL'], 'Something')
			pass

		return content

	def get_path_info (self, path, working_dir = ''):
		info = {}

		# Convert to absolute path if needed
		if not os.path.isabs(path):
			info['dirname'] = os.path.abspath(ntpath.join(working_dir, path))
		else:
			info['dirname'] = path

		info['dirname']     = ntpath.dirname(info['dirname'])                   # (C:\source)\file.js
		info['filename']    = ntpath.basename(path)                             # C:\source\(file.js)
		split               = ntpath.splitext(info['filename'])
		info['fileroot']    = split[0]                                          # C:\source\(file).js
		info['extension']   = split[1][1:]                                      # C:\source\file.(js)
		info['realpath']    = ntpath.join(info['dirname'], info['filename'])    # (C:\source\file.js)
		info['working_dir'] = working_dir                                       # As specified in the argument. The directory to start from.
		info['is_child'] 	= True

		return info

	def template (self, file_dict, string, valueDict):
		if string: 
			# Find all {{template_variables}} in the header/footer
			for tpl_match in re.finditer(self.re_template, string):
				value = False
				outermatch  = tpl_match.group('outermatch')
				namespace   = tpl_match.group('namespace')
				key         = tpl_match.group('key')

				# (source/target/referer).*
				if namespace == 'this' or namespace == 'source' or namespace == 'referer':
					owner = valueDict[namespace]

					if key in owner:
						value = owner[key]

					# Say that the .lastmod_date and .lastmod_time exists in both the header and the footer.
					# This means that we'll have to call os.path.getmtime 4 times.
					# An alternative would be to cache the os.path.getmtime temporarily for all files during the concatenation,
					# but that would add more complexity to the plugin. I do not know the performance implications for calling for example getmtime
					# and does at the time of this writing not want to optimize prematurely.
					elif key == 'filesize':
						value = str(self.format_bytes(os.path.getsize(owner['realpath'])))
					elif key == 'lastmod_date':
						value = time.strftime(self.setting(file_dict, 'date_format'), time.gmtime(os.path.getmtime(owner['realpath'])))
					elif key == 'lastmod_time':
						value = time.strftime(self.setting(file_dict, 'time_format'), time.gmtime(os.path.getmtime(owner['realpath'])))
					else:
						self.log(MSG_TYPE['WARNING'], 'Unknown template key' + '"' + key + '"', file_dict)

				# system.*
				elif namespace == 'system':
					if key == 'time':
						value = time.strftime(self.setting(file_dict, 'time_format'))
					elif key == 'date':
						value = time.strftime(self.setting(file_dict, 'date_format'))
					elif key == 'platform':
						value = sublime.platform()
					elif key == 'arch':
						value = sublime.arch()
					elif key == 'version':
						value = sublime.version()
					else:
						self.log(MSG_TYPE['WARNING'], 'Unknown template key' + '"' + key + '"', file_dict)

				# result.*
				elif namespace == 'result':
					owner = valueDict[namespace]
					tmp = 0
					display_x_files = 3

					if key == 'num_referenced_files':
						tmp = len(owner['referenced_file_dicts'])
						value = str(tmp) + (' files' if tmp > 1 else ' file')
					elif key == 'referenced_files_size':
						value = self.format_bytes(owner['referenced_file_bytes'])
					elif key == 'written_filenames':
						tmp = len(owner['written_file_dicts'])
						value = ', '.join(["'" + fdict['filename'] + "'" for fdict in owner['written_file_dicts'][:display_x_files]])
						value += (' and ' + str(tmp - display_x_files) + ' more') if tmp > display_x_files else ''
					elif key == 'referenced_filenames':
						tmp = len(owner['referenced_file_dicts'])
						value = ', '.join(["'" + fdict['filename'] + "'" for fdict in owner['referenced_file_dicts'][:display_x_files]])
						value += (' and ' + str(tmp - display_x_files) + ' more') if tmp > display_x_files else ''
					elif key == 'runtime':
						value = "{0:.2f}".format(owner['runtime_end'] - owner['runtime_start'])
					elif key == 'num_reused_files':
						value = str(owner['num_reused_files'])
					else:
						self.log(MSG_TYPE['WARNING'], 'Unknown template key' + '"' + key + '"', file_dict)

				# ?.*
				else:
					self.log(MSG_TYPE['WARNING'], 'Unknown namespace key' + '"' + namespace + '"', file_dict)

				# If we got a value, replace the outermatch ({{template_var}}) with the value
				if not value == False:
					string = string.replace(outermatch, value)

		return self.parse_string_literals(string)

	# Writes a file_dict to disc
	def write (self, source_file_dict, target_file_dict, referer_file_dict, content, saveto_file_dict = False):
		filename = saveto_file_dict['filename'] if saveto_file_dict else ''
		dirname  = saveto_file_dict['dirname'] if saveto_file_dict else target_file_dict['dirname']

		output_filename = filename if filename else self.setting(target_file_dict, 'tpl_output_filename')
		output_filename = self.template(target_file_dict, output_filename, {
			'this':     target_file_dict,
			'source':   source_file_dict,
			'referer':  referer_file_dict
		})

		# The absolute path to the output file
		output_realpath = ntpath.join(dirname, output_filename)

		# Safety net
		if not saveto_file_dict and os.path.isfile(output_realpath) and target_file_dict['filename'] == output_filename:
			return self.log(MSG_TYPE['FATAL'], 'A file already exist at the path specified and the name equals to the original. I will not continue at risk of overwriting the original.\n\nEvaluated filename:\n' + output_filename + '\n\nDirectory:\n' + target_file_dict['dirname'] + '\n\n' + 'Please look over your settings.', target_file_dict)

		# If the source´s filename equals to the target, this means that this is the last write.
		# Depending on current settings, trim the content.
		if (source_file_dict['filename'], target_file_dict['filename']) and self.setting(target_file_dict, 'trim_output'):
			content = content.strip()

		# The w-flag will create a new file or overwrite an existing file.
		with open(output_realpath, 'w') as handle:
			handle.write(content)

		target_file_dict['output_filename'] = output_filename
		target_file_dict['output_dirname'] = dirname
		target_file_dict['output_realpath'] = output_realpath

		return target_file_dict

	def parse (self, target_file_dict, referer_file_dict, callback, memo = False):
		if not memo:
			memo = {}
			memo['runtime_start']           = time.time()
			memo['written_file_dicts']      = []
			memo['referenced_file_dicts']   = []
			memo['referenced_file_bytes']   = 0
			memo['partof_queue']            = []
			memo['source_file_dict']        = target_file_dict
			memo['missing_parents']         = []
			memo['missing_children']        = []
			memo['num_reused_files']        = 0

			target_file_dict['is_child'] 	= False
			referer_file_dict['is_child'] 	= False

		# A file can be both a parent and child at the same time.
		is_child = target_file_dict['is_child']
		is_parent = False

		target_content = self.file_get_contents(target_file_dict['realpath'], False)
		target_matches = self.re_method.findall(target_content)
		target_partofs = []

		self.log(MSG_TYPE['INFO'], 'Started parsing ' + ('child' if is_child else 'parent'), target_file_dict)

		# Reset saveto-variables. This can be filled via the @saveto
		saveto_file_dict = False

		if len(target_matches) > 0:
			for parent_match in target_matches:
				beg_linebreak, fullmatch, indentation, method, value, end_linebreak = parent_match

				# Clean the value from ' " and whitespaces
				value = value.strip('\'" ')

				# Users can prefix values with 'glob:' to activate globsearch 
				globsearch = value.startswith('glob:')
				if (globsearch):
					value = value[5:] # Remove the 'glob:'-prefix 

				# Handle 'partof', 'option' and 'saveto' methods
				if method == 'partof' or method == 'option' or method == 'saveto':

					# Save all partof's and parse them later, when all import's are done
					if not is_child and method == 'partof':
						memo['partof_queue'].append(parent_match)

					# Handle @option
					elif method == 'option':
						option_split = value.split(',', 2)
						
						if len(option_split) > 1:
							option_key = option_split[0].strip('\'" ').lower()
							option_val = option_split[1].strip('\'" ')
							option_rec = option_split[2].strip('\'" ').lower() if len(option_split) > 2 else False

							if option_rec == 'true' or option_rec == '1':
								option_rec = True
							else:
								option_rec = False

							if option_val.lower() == 'default':
								self.clear_jit_setting(option_key, option_rec, target_file_dict)
							else:
								self.push_jit_setting(option_key, option_val, option_rec, target_file_dict)
						else:
							self.log(MSG_TYPE['WARNING'], 'Malformed @option method: "' + fullmatch + '"', target_file_dict)

					# Handle @saveto
					elif not is_child and method == 'saveto':
						if len(value) > 0:

							# If the value seems to have an extension, we'll assume the user wants us to write to a file
							saveto_file = len(ntpath.splitext(value)[1]) > 1

							saveto_file_dict = self.get_path_info(value if saveto_file else ntpath.join(value, 'tempname.ext'), target_file_dict['dirname'])
							
							if not saveto_file:
								saveto_file_dict['filename'] = ''

							# If the evaluated path does not exist, ask the user if we should create it.
							if not os.path.isdir(saveto_file_dict['dirname']):
								if not sublime.ok_cancel_dialog(MESSAGE_HEADER + 'The path specified via @saveto in ' + target_file_dict['filename'] + ' does no exist. Do you want me to create it?\n\nPath specified:\n' + ntpath.dirname(value) + os.sep + '\n\nEvaluated:\n' + saveto_file_dict['dirname'] + os.sep):
									saveto_file_dict = False
								else:
									try:
										os.makedirs(saveto_file_dict['dirname'])
									except OSError as exc: # Python >2.5
										if exc.errno == errno.EEXIST and os.path.isdir(path):
											pass
										else:
											self.log(MSG_TYPE['FATAL'], exc, target_file_dict)
											saveto_file_dict = False
											raise
						else:
							self.log(MSG_TYPE['WARNING'], 'Malformed @saveto method: "' + fullmatch + '"', target_file_dict)

					# Remove the fullmatch reference. Prioritize the preceding linebreak, then the succeeding
					if end_linebreak:
						target_content = target_content.replace(fullmatch + end_linebreak, '', 1)
					else:
						target_content = target_content.replace(beg_linebreak + fullmatch, '', 1)

				# Handle the 'import' method
				elif method == 'import':

					child_file_dict = self.get_path_info(value, target_file_dict['dirname'])

					# Skip if the file does not exist
					if not globsearch and not os.path.isfile(child_file_dict['realpath']):
						memo['missing_children'].append([child_file_dict, target_file_dict])

						# Remove the fullmatch reference. Prioritize the preceding linebreak, then the succeeding
						if end_linebreak:
							target_content = target_content.replace(fullmatch + end_linebreak, '', 1)
						else:
							target_content = target_content.replace(beg_linebreak + fullmatch, '', 1)
						
						continue

					is_parent = True
					child_content = ''

					# Look through the "written_file_dicts"-list in the memo and check that we haven't already parsed and written this file to disc.
					for already_written_dict in memo['written_file_dicts']:
						if already_written_dict['realpath'] == child_file_dict['realpath']:
							child_content = self.file_get_contents(already_written_dict['output_realpath'], False)
							memo['num_reused_files'] += 1
							break
					else:

						# Normalize the child_matches list.
						# globsearch or not, we are gonna continue with a list of 0 or more matches 
						if globsearch:
							child_matches = [self.get_path_info(filematch, target_file_dict['dirname']) for filematch in glob.glob(child_file_dict['realpath'])]
						else:
							child_matches = [child_file_dict]

						if len(child_matches) > 0:
							child_content = ''.join([self.parse(child_file_dict, target_file_dict, callback, memo) for child_file_dict in child_matches])

							# 
							memo['referenced_file_dicts'].extend(child_matches)
							memo['referenced_file_bytes'] += len(child_content)


					# glob: can yield 0 results, therefore we have to check that we actually got any content
					if child_content: 
						# Apply indentation
						if len(indentation) > 0 and self.setting(target_file_dict, 'apply_intendation') == True:
							child_content = indentation + child_content.replace('\n', '\n' + indentation)

						# Stitch togheter the contents and replace them into the target_content
						target_content = target_content.replace(fullmatch, child_content, 1)
		else:
			self.log(MSG_TYPE['INFO'], 'No methods found', target_file_dict)

		# We handle parents and children almost exactly the same, but the user supplied settings can differ.
		# Instead of doing more work in the name of clarity, we'll do half with variable variables.
		write_to_disc = is_parent and (not is_child or self.setting(target_file_dict, 'write_nested_parents'))
		trim_type     = 'parents' if is_parent else 'children'
		tpl_type      = 'parent' if is_parent else 'child'

		# Trim this file?
		if self.setting(target_file_dict, 'trim_' + trim_type):
			target_content = target_content.strip()

		# Apply header/footer
		values = {'this': target_file_dict, 'source': memo['source_file_dict'], 'referer': referer_file_dict}

		header = self.setting(target_file_dict, 'tpl_' + tpl_type + '_header')
		footer = self.setting(target_file_dict, 'tpl_' + tpl_type + '_footer')

		header = header and self.template(target_file_dict, header, values)
		footer = footer and self.template(target_file_dict, footer, values)

		if header or footer:
			target_content = header + target_content + footer

		if write_to_disc:
			# Write the file, save the name in the file_dict and add it to the memo
			memo['written_file_dicts'].append(self.write(memo['source_file_dict'], target_file_dict, referer_file_dict, target_content, saveto_file_dict))

		self.log(MSG_TYPE['INFO'], 'Finished parsing', target_file_dict)

		# Clear JIT-settings
		self.clear_jit_setting(key = '*', recursive = (not is_child), file_dict = target_file_dict)

		last_file_to_write = not is_child and not len(memo['partof_queue'])

		# Parse all the 'partof'-references
		if not is_child:
			if len(memo['partof_queue']) > 0:
				while memo['partof_queue']:
					# .pop() the first item from the queue, get the value (filepath) (@method(value)) at position 4 and clean it.
					parent_file_dict = self.get_path_info(memo['partof_queue'].pop(0)[4].strip('\'" '), target_file_dict['dirname'])

					parent_file_dict['is_child'] = False

					# Skip if the file does not exist
					if not os.path.isfile(parent_file_dict['realpath']):
						memo['missing_parents'].append([parent_file_dict, target_file_dict])
					else:
						self.parse(parent_file_dict, target_file_dict, callback, memo)
			else:
				# End of the line, run the callback.
				memo['runtime_end'] = time.time()
				self.log(MSG_TYPE['INFO'], 'Parsing finished in ' + "{0:.2f}".format(memo['runtime_end'] - memo['runtime_start']) + ' seconds', target_file_dict)
				callback(memo)

		return target_content

	def parser_callback (self, result):
		num_missing_parents  = len(result['missing_parents'])
		num_missing_children = len(result['missing_children'])

		# If one or more files could not be found, pop an error message
		if num_missing_parents > 0 or num_missing_children > 0:
			str_missing_parents = ''
			str_missing_children = ''

			# Build string for presenting missing parents
			if num_missing_parents > 0:
				str_missing_parents = 'Parents:\n' + ''.join([missing_file[0]['realpath'] + ', referer: ' + missing_file[1]['filename'] + '\n' for missing_file in result['missing_parents']]) + '\n\n'

			# Build string for presenting missing children
			if num_missing_children > 0:
				str_missing_children = 'Children:\n' + ''.join([missing_file[0]['realpath'] + ', referer: '+ missing_file[1]['filename'] + '\n' for missing_file in result['missing_children']])

			missing_message = MESSAGE_HEADER + str(num_missing_parents + num_missing_children) + ' referenced ' + ('files' if num_missing_children > 1 else 'file') + ' could not be found:\n\n'

			# Notify user
			sublime.error_message(missing_message + str_missing_parents + str_missing_children)

		infos	 = self.log_list_types[MSG_TYPE['INFO']]
		warnings = self.log_list_types[MSG_TYPE['WARNING']]
		errors 	 = self.log_list_types[MSG_TYPE['ERROR']]
		fatals 	 = self.log_list_types[MSG_TYPE['FATAL']]

		message = MESSAGE_HEADER
		message += 'The concatenation finished with '
		message += str(warnings) + ' ' + ('warning' if warnings == 1 else 'warnings') + ', '
		message += str(errors) + ' ' + ('error' if errors == 1 else 'errors') + ' and '
		message += str(fatals) + ' fatal.\n\n'
		message += '\n'.join(self.log_list)

		if warnings or errors or fatals:
			sublime.error_message(message)
		elif self.setting(0, 'verbose') and infos:
			sublime.message_dialog(message)

		if len(result['written_file_dicts']) > 0:
			# Set status message
			status_message = self.setting(0, 'tpl_status_message')

			if status_message:
				status_message = self.template(0, status_message, {
					'result': result
				})

				sublime.set_timeout(lambda: sublime.status_message(status_message), 0)
	#
	# The main run-method
	# Executed from key-bindings, menu, save etc
	#
	def run (self, edit, targetFile = False, current_iteration = 0):
		# 1) Has some very intermittent troubles with instance variables not resetting properly.. so we have to be quite rough here
		self.reset_instance()

		self.log(MSG_TYPE['INFO'], 'Initiating concatenation')

		if targetFile == False:
			targetFile = self.view.file_name()

		# Generalized dictionary used throughout the plugin for file information
		target_file_dict = self.get_path_info(ntpath.basename(targetFile), ntpath.dirname(targetFile))

		# Get the ball rollin'
		self.parse(target_file_dict, target_file_dict, self.parser_callback)

		# See 1)
		self.reset_instance()

#
# Event listener for post-save
#
class FileConcatenatorEventListener(sublime_plugin.EventListener):

	def on_post_save(self, view):
		settings = sublime.load_settings(SETTINGS_FILE)

		# Should we the concat on save?
		if settings.get('run_on_save', False) == False:
			return
			
		# Is the current extension set to be ran on save?
		if view.file_name().split('.')[-1] not in settings.get('run_on_save_extensions'):
			return

		sublime.active_window().run_command('concatenator')
