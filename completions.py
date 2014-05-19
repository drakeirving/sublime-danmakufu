import sublime, sublime_plugin, string, re


# TODO: Add defined functions to completions


class Library():
	def init(self):
		self.dict = {}
		# currently just plops right into actives
		self.settings = sublime.load_settings("sublime-completions-library.sublime-settings")
		# object containing completions filenames
		self.actives = self.settings.get("completions_file_list")

		# currently only dnh
		if self.actives:
			for key in self.actives:
				# load file contents into dictionary
				# make sure it's a settings file
				self.dict[key] = sublime.load_settings(self.actives[key])


library = Library()

if int(sublime.version()) < 3000:
	library.init()
else:
	def plugin_loaded():
		global library
		library.init()


class LibraryCollector(sublime_plugin.EventListener):
	global library
	def on_query_completions(self, view, prefix, locations):
		self.completions = []

		for key in library.dict:
			if (library.actives and library.actives.get(key)): # if dict active
				scope = library.dict[key].get("scope")
				if scope and view.match_selector(locations[0], scope):
					self.completions += library.dict[key].get("completions")

		if not self.completions:
			return []

		# extend other completions
		olds = [view.extract_completions(prefix)]
		olds = [(item, item) for sublist in olds for item in sublist if len(item) > 3]
		olds = list(set(olds))
		self.completions = clean(self.completions, olds)
		return (self.completions)

def clean(completions, olds):
	newcomp = []
	for string in list(completions):
		# validate and split
		match = re.findall(r"^(\w+::)?(\w+)\((.*)\)(\t.*)?$", string)[0]
		# [0]: namespace
		# [1]: function name
		# [2]: parameters
		# [3]: return type

		name = match[1]
		# remove duplicates
		if (name, name) in olds:
			olds.remove((name, name))

		# generate tab-to-params string
		params = "(" + ", ".join(["$"+str(i) for i in list(range(1, match[2].count(",")+2))]) + ")$0"

		# add to completions list
		newcomp.append(tuple([string] + [name + params]))

	newcomp.extend(olds)
	return newcomp


class DanmakufuDoc(sublime_plugin.TextCommand):
	def run(self, edit):
		if(not self.view.match_selector(self.view.sel()[0].begin(), 'source.danmakufu')): return

		panel = self.view.window().get_output_panel('danmakufu_doc')
		self.view.window().run_command('show_panel', {'panel': 'output.danmakufu_doc'})

		panel.set_read_only(False)
		panel.run_command('insert', {'characters': 'aaa'})
		panel.set_read_only(True)

		# hide after timeout
		sublime.set_timeout_async(lambda: hide(panel), 5000)

		def hide(panel):
			if(bool(panel.window())):
				panel.window().run_command('hide_panel')

