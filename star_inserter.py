import sublime, sublime_plugin
import os, re

class StarInserter(sublime_plugin.TextCommand):
  def run(self, edit):
    scope_name = self.view.scope_name(self.view.sel()[0].a)
    self.view.run_command("insert", {"characters": "\n"})
    if 'comment.block.documentation.js' in scope_name:
      self.view.insert(edit, self.view.sel()[0].a, '* ')
