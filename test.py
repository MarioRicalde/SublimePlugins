import sublime, sublime_plugin

class ExampleCommand(sublime_plugin.TextCommand):
  def run(self, edit):
    print self.view.scope_name(self.view.sel()[0].a)
    print self.view.extract_scope(self.view.sel()[0].a)
    print self.view.sel()[0]