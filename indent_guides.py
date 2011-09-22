import sublime
import sublime_plugin
import indentation
import re


class IndentGuidesListener(sublime_plugin.EventListener):
  def __init__(self):
    self.cache = {}
    self.guides = []
    self.current_tab = None
    self.region = None

  def get_indent(self, region, view, tab_size):
    pos = 0
    tabs = []
    line = view.rowcol(region.a)[0]
    if line not in self.cache:
      text = view.substr(region)
      for c in range(0, len(text)):
        if text[c].isspace():
          pos += 1
        elif text[c] == '\t':
          pos += tab_size - (pos % tab_size)
        else:
          break

        if pos % tab_size == 0:
          tabs.append(c + 1)

      if len(tabs) > 0:
        tabs.pop()
      self.cache[line] = tabs
    return self.cache[line]

  def refresh(self, view, clear_cache):
    if clear_cache:
      self.cache = {}

    tab = self.calculate_active_guide(view)
    if clear_cache or tab != self.current_tab:
      self.guides = []
      self.region_start = 0
      self.region_end = 0
      self.current_tab = tab

    visible = view.visible_region()
    expanded_region = sublime.Region(max(visible.a - 250, 0), min(visible.b + 5, view.size()))
    visible_regions = view.split_by_newlines(visible)

    tab_size = indentation.get_tab_size(view)

    for region in visible_regions:
      line = view.rowcol(region.a)[0]
      tabs = self.get_indent(region, view, tab_size)
      if self.current_tab < len(tabs):
        pos = region.a + tabs[tab]
        self.guides.append(sublime.Region(pos, pos))

    view.add_regions('IndentGuidesListener', self.guides, 'active_guide', sublime.DRAW_EMPTY)

  def check_indent(self, view, start, forward, tab_size):
    start_indent = self.get_indent(start, view, tab_size)

    if len(start_indent) <= 0:
      return 0

    print 'loop'
    print start_indent
    while True:
      print start
      if start.a <= 0:
        return 0
      if start.b >= view.size():
        return 0

      if forward:
        start = view.full_line(start.b + 1)
      else:
        start = view.full_line(start.a - 1)

      if abs(start.b - start.a) <= 1:
        continue

      tabs = self.get_indent(start, view, tab_size)
      return len(tabs) - len(start_indent)


  def calculate_active_guide(self, view):
    tab_size = indentation.get_tab_size(view)
    cursor = view.sel()[-1].b
    region = view.line(cursor)
    cursorCol = view.rowcol(cursor)[1]
    pos = 0

    for pt in xrange(region.begin(), region.end()):
      ch = view.substr(pt)

      if ch == '\t':
        pos += tab_size - (pos % tab_size)
      elif ch.isspace():
        pos += 1
      else:
        break

    tab = int(pos / tab_size)
    if cursorCol < pos:
      tab = int(cursorCol / tab_size)
    else:
      before = self.check_indent(view, region, False, tab_size)
      after = self.check_indent(view, region, True, tab_size)
      print cursorCol, tab, pos
      print before, after

      if after <= 0:
        tab -= 1
    return max(tab - 1, 0)

  def on_load(self, view):
    self.refresh(view, True)

  def on_activated(self, view):
    self.refresh(view, True)

  def on_selection_modified(self, view):
    self.refresh(view, False)

  def on_modified(self, view):
    self.refresh(view, True)
