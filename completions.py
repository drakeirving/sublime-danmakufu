import sublime, sublime_plugin, string


#TODO: Add defined functions to completions


class Library():
	def init(self):
		self.dict = {}
		#currently just plops right into actives
		self.settings = sublime.load_settings("sublime-completions-library.sublime-settings")
		#object containing completions filenames
		self.actives = self.settings.get("completions_file_list")

		#currently only dnh
		if self.actives:
			for key in self.actives:
				#load file contents into dictionary
				#make sure it's a settings file
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
			if (library.actives and library.actives.get(key)): #if dict active
				scope = library.dict[key].get("scope")
				if scope and view.match_selector(locations[0], scope):
					self.completions += library.dict[key].get("completions")

		if not self.completions:
			return []

		#extend other completions
		olds = [view.extract_completions(prefix)]
		olds = [(item, item) for sublist in olds for item in sublist if len(item) > 3]
		olds = list(set(olds))
		self.completions = clean(self.completions, olds)
		return (self.completions)

def clean(completions, olds):
	newcomp = []
	for attr in list(completions):
		name = attr.split("::", 1)[1].split("(", 1)[0]

		#remove duplicates
		if (name, name) in olds:
			olds.remove((name, name))

		#add completion string
		name += "("
		params = attr.split("(", 1)[1].split(")", 1)[0]
		if len(params) > 0:
			i = 1
			while i <= params.count(","):
				name += "$" + str(i) + ", "
				i += 1
			name += "$" + str(i)
		name += ")$0"
		newcomp.append(tuple([attr] + [name]))

	newcomp.extend(olds)
	return newcomp

