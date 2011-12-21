import sublime, sublime_plugin
import os, re

class StarInserter(sublime_plugin.TextCommand):
  def run(self, edit):
    for i in range(0, len(self.view.sel())):
      sel = self.view.sel()[i]
      scope_name = self.view.scope_name(sel.b)
      add_space = self.view.substr(self.view.line(sel.b)).strip() == '/**'
      is_end = self.view.substr(self.view.line(sel.b)).strip() == '*/'
      self.view.run_command("insert", {"characters": "\n"})
      if not is_end:
        if 'comment.block.documentation.js' in scope_name:
          sel = self.view.sel()[i]
          if add_space:
            self.view.insert(edit, sel.a, ' * ')
          else:
            self.view.insert(edit, sel.a, '* ')
