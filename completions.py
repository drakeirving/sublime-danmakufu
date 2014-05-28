import sublime, sublime_plugin, string, re


# TODO: Add defined functions to dictionary


class Library():
	def init(self):
		self.dict = {}
		# currently just plops right into actives
		self.settings = sublime.load_settings("sublime-completions-library.sublime-settings")
		# object containing completions filenames
		self.actives = self.settings.get("completions_file_list")

		if self.actives:
			for key in self.actives:
				# load file contents into dictionary with scope as key
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
		self.dict = []

		for key in library.dict:
			# if dict active
			if (library.actives and library.actives.get(key)): 
				scope = library.dict[key].get("scope")
				# if dict matches current scope
				if scope and view.match_selector(locations[0], scope):
					self.dict += library.dict[key].get("dict")

		if not self.dict:
			return []

		# extend existing completions list
		oldcomp = [view.extract_completions(prefix)]
		oldcomp = [(item, item) for sublist in oldcomp for item in sublist if len(item) > 3]
		oldcomp = list(set(oldcomp))
		newcomp = extend_comp(self.dict, oldcomp)
		return (newcomp)

def extend_comp(dict, oldcomp):
	newcomp = []
	for obj in list(dict):
		# validate and split
		matchlist = re.findall(r"^(\w+::)?(\w+)\((.*)\)(\t.*)?$", obj["sig"])

		# if invalid string is found
		if (len(matchlist) == 0): continue

		match = matchlist[0]
		# [0]: namespace
		# [1]: function name
		# [2]: parameters
		# [3]: return type

		name = match[1]
		# remove duplicates
		if (name, name) in oldcomp:
			oldcomp.remove((name, name))

		# generate tab-to-params string
		params = "(" + ", ".join(["$"+str(i) for i in list(range(1, match[2].count(",")+2))]) + ")$0"

		# add to completions list
		newcomp.append(tuple([obj["sig"]] + [name + params]))

	newcomp.extend(oldcomp)
	return newcomp

# TODO: Hook up with dict
# TODO: Need to generalize
# TODO: Multiple lines
class DanmakufuDoc(sublime_plugin.TextCommand):
	def run(self, edit):
		if(not self.view.match_selector(self.view.sel()[0].begin(), "source.danmakufu")): return

		panel = self.view.window().get_output_panel("danmakufu_doc")
		self.view.window().run_command("show_panel", {"panel": "output.danmakufu_doc"})

		panel.set_read_only(False)
		panel.run_command("insert", {"characters": "aaa"})
		panel.set_read_only(True)

		# hide after timeout
		sublime.set_timeout_async(lambda: hide(panel), 5000)

		def hide(panel):
			if(bool(panel.window())):
				panel.window().run_command("hide_panel")

