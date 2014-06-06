import sublime, sublime_plugin, string, re


class Library():
	def init(self):
		self.collection = []		# list of dictionary objects
		self.ordered_key_list = []	# list of lists of ordered keys of same-indexed dictionaries

		# currently no program settings besides file list
		self.settings = sublime.load_settings("sublime-completions-library.sublime-settings")
		# list of completions filenames
		self.file_list = self.settings.get("completions_file_list")

		if self.file_list:
			for f in self.file_list:
				# parse file contents into the structures actually used
				temp = dictionaryize(sublime.load_settings(f))
				self.collection.append(temp[0])
				self.ordered_key_list.append(temp[1])

# precompute dict items from lists to dictionaries for fast and ez
# also generates list of keys in original order for sequential access
def dictionaryize(settings):
	d = {}
	keys = []
	d["scope"] = settings.get("scope")
	d["dict"] = {}
	temp_dict = settings.get("dict")
	regex = re.compile(r"^(\w+::)?(\w+)\((.*)\)(\t.*)?$")
	# [1]: namespace
	# [2]: function name
	# [3]: parameters
	# [4]: return type

	for entry in temp_dict:
		# extract function name and use as key
		match = regex.search(entry["sig"])
		if match: 
			name = match.group(2)
			d["dict"][name] = entry
			d["dict"][name]["num_params"] = 0 if (match.group(3) == "") else match.group(3).count(",") + 1
			keys.append(name)

	return (d, keys)



class DictCollector(sublime_plugin.EventListener):
	global library
	def on_query_completions(self, view, prefix, locations):
		self.dict = {}
		self.ordered_keys = []

		for i, d in enumerate(library.collection):
			scope = d["scope"]
			# if dict matches current scope
			if scope and view.match_selector(locations[0], scope):
				self.dict.update(d["dict"])
				self.ordered_keys = library.ordered_key_list[i]

		if not self.dict:
			return []

		oldcomp = [view.extract_completions(prefix)]
		oldcomp = [(item, item) for sublist in oldcomp for item in sublist if len(item) > 3]
		oldcomp = list(set(oldcomp))
		newcomp = extend_comp(self.dict, self.ordered_keys, oldcomp)
		
		return newcomp

# find matching completions and extend existing list
def extend_comp(dict, ordered_keys, oldcomp):
	temp = []
	for name in ordered_keys:

		# remove duplicates
		if (name, name) in oldcomp:
			oldcomp.remove((name, name))

		# generate tab-to-params string
		params = "(" + ", ".join([ "$"+str(i+1) for i in range(0, dict[name]["num_params"]) ]) + ")$0"

		# add to completions list
		temp.append( (dict[name]["sig"], (name + params)) )

	temp.extend(oldcomp)
	return temp



class GetFunctionDocs(sublime_plugin.TextCommand):
	global library
	def run(self, edit):
		self.dict = {}
		location = self.view.sel()[0].begin()

		for d in library.collection:
			scope = d["scope"]
			# if dict matches current scope
			if scope and self.view.match_selector(location, scope):
				self.dict.update(d["dict"])
				break

		# get word at current point
		name = self.view.substr(self.view.word(location))

		# valid if existing function name
		if not self.dict or name not in self.dict:
			return

		run_function_docs_panel(self.view, name, self.dict)
		
def run_function_docs_panel(view, name, dict):

	doc = dict[name]["doc"]

	if not doc:
		doc = "(No documentation)"

	# prepend with function signature
	doc = dict[name]["sig"].rsplit("\t", 1)[0] + "\n" + doc

	panel = view.window().get_output_panel("get_function_docs_panel")
	view.window().run_command("show_panel", {"panel": "output.get_function_docs_panel"})

	panel.set_read_only(False)
	panel.settings().set("auto_indent", False) # required for docstring to not screw up
	panel.run_command("insert", {"characters": doc})
	panel.set_read_only(True)

	# identify current docs panel by the function it describes
	panel.set_name(name)

	# hide after timeout
	sublime.set_timeout_async(lambda: hide(panel, name), 8000)

	def hide(panel, name):
		# if docs panel is the same one as when it was opened
		if panel.window() and panel.name() == name:
			panel.window().run_command("hide_panel")



# initialization
library = Library()

if int(sublime.version()) < 3000:
	library.init()
else:
	def plugin_loaded():
		global library
		library.init()