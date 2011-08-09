'''
ENABLING GUIDES
  "show_indent_guides": true
    if you want the guides drawn, add this to your user file preferences.

  "show_active_indent_guides": true
    if you want the active guide to be highlighted separately, add this to
    your user file preferences.

PLACEMENT OPTIONS
  "indent_guides_flush_with_text": true
    if you want your guides to be drawn all the way up to the text, add this
    to your user file preferences.

  "indent_guides_flush_with_gutter": true
    if you want your guides to be drawn all the way to the gutter, add this
    to your user file preferences.

  "indent_guides_max_file_characters": 524288
    if you want to limit the size of files that will be processed by this
    plugin, add this to your user file preferences with any number you like.

COLOR OPTIONS
  "indent_guides_color_scope_name" : "guide"
    Normally the color of the guides is the same as the color of comments
    in your code. If you'd like to customize the color, add the below to your
    color scheme file and change EDF2E9 to whatever color you want, then add
    this to your user file preferences.
    (thanks to theblacklion)

  "indent_guides_active_color_scope_name" : "active_guide"
    If you want the indent guides for the column your cursor is in to be a
    slightly different color, set this option in user file preferences.

---ADD TEXT BELOW THIS LINE TO YOUR COLOR SCHEME FILE---
      <dict>
          <key>name</key>
          <string>Guide</string>
          <key>scope</key>
          <string>guide</string>
          <key>settings</key>
          <dict>
            <key>foreground</key>
            <string>#EDF2E9</string>
         </dict>
      </dict>
---ADD TEXT ABOVE THIS LINE TO YOUR COLOR SCHEME FILE---
'''

import sublime
import sublime_plugin
import indentation
import re


class IndentGuidesListener(sublime_plugin.EventListener):
  defaults = {
    'flush_with_gutter': False,
    'flush_with_text': True,
    'max_file_characters': 524288,
    'scope': 'comment'
  }

  guides = []
  loaded = False

  def find_regions_of_interest(self, view, whole_file):
    find_str = r'^(( )|(\t))+(?=(( )|(\t)|$))'

    if whole_file:
      regions_of_interest = view.find_all(find_str)
    else:
      regions_of_interest = []

      for s in view.sel():
        begin_row, _ = view.rowcol(s.begin())
        end_row, _ = view.rowcol(s.end())

        for row in xrange(begin_row, end_row + 1):
          bol = view.text_point(row, 0)
          m = re.search(find_str, view.substr(view.line(bol)))

          if m:
            regions_of_interest.append(sublime.Region(bol, bol + len(m.group(0))))

    return regions_of_interest

  def get_current_guides(self, view, whole_file):
    if whole_file:
      guides = []
    else:
      guides = view.get_regions('IndentGuidesListener')

    return guides

  def file_is_small_enough(self, view):
    max_size = view.settings().get('indent_guides_max_file_characters', self.defaults['max_file_characters'])

    if view.size() > max_size:
      return False
    else:
      return True

  def update_guides(self, view, regions_of_interest, guides):
    tab_size = indentation.get_tab_size(view)
    flush_with_text = view.settings().get('indent_guides_flush_with_text', self.defaults['flush_with_text'])
    flush_with_gutter = view.settings().get('indent_guides_flush_with_gutter', self.defaults['flush_with_gutter'])

    for roi in regions_of_interest:
      pos = 0

      for pt in xrange(roi.begin(), roi.end()):
        ch = view.substr(pt)

        if pos % tab_size == 0 and (flush_with_gutter or pos != 0):
          loc = pt
          guides.append(sublime.Region(loc, loc))

        if ch == '\t':
          pos += tab_size - (pos % tab_size)
        elif ch.isspace():
          pos += 1
        else:
          pos += 1

      if flush_with_text and pos % tab_size == 0:
        guides.append(sublime.Region(roi.end(), roi.end()))

    return guides

  def refresh(self, view, whole_file = False):
    settings = view.settings()

    if not settings.get('show_indent_guides', False) or not self.file_is_small_enough(view):
      view.erase_regions('IndentGuidesListener')
      view.erase_regions('IndentActiveGuidesListener')
    else:
      regions_of_interest = self.find_regions_of_interest(view, whole_file)
      guides = self.get_current_guides(view, whole_file)
      guides = self.update_guides(view, regions_of_interest, guides)

      color_scope_name = settings.get('indent_guides_color_scope_name', self.defaults['scope'])
      view.add_regions('IndentGuidesListener', guides, color_scope_name, sublime.DRAW_EMPTY)

      self.guides = guides

  def calculate_whitespace(self, view, cursor, tab_size):
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

    if pos > cursorCol:
      return cursorCol
    else:
      return pos

  def update_active_guides(self, view):
    settings = view.settings()
    tab_size = indentation.get_tab_size(view)

    if not settings.get('show_indent_guides', False) or not self.file_is_small_enough(view):
      view.erase_regions('IndentGuidesListener')
      view.erase_regions('IndentActiveGuidesListener')
    elif not settings.get('show_active_indent_guides', False):
      view.erase_regions('IndentActiveGuidesListener')
    else:
      cursors = {}
      cursorAbsolutes = {}

      for sel in view.sel():
        cursorAbsolutes[sel.b] = True
        cursors[self.calculate_whitespace(view, sel.b, tab_size)] = True

      active_guides = []
      inactive_guides = []

      if not self.guides and self.loaded:
        self.refresh(view, whole_file = True)

      for guide in self.guides:
        if True or not view.sel().contains(guide):
          if not guide.a in cursorAbsolutes:
            if view.rowcol(guide.a)[1] in cursors:
              active_guides.append(guide)
            else:
              inactive_guides.append(guide)

      inactive_color_scope_name = settings.get('indent_guides_color_scope_name', self.defaults['scope'])
      active_color_scope_name = settings.get('indent_guides_active_color_scope_name', self.defaults['scope'])

      view.erase_regions('IndentGuidesListener')
      view.erase_regions('IndentGuidesActiveListener')
      view.add_regions('IndentGuidesListener', inactive_guides, inactive_color_scope_name, sublime.DRAW_EMPTY)
      view.add_regions('IndentGuidesActiveListener', active_guides, active_color_scope_name, sublime.DRAW_EMPTY)

  def on_load(self, view):
    self.refresh(view, whole_file = True)
    self.update_active_guides(view)

    self.loaded = True

  def on_activated(self, view):
    self.refresh(view, whole_file = True)
    self.update_active_guides(view)

  def on_selection_modified(self, view):
    if self.loaded:
      self.update_active_guides(view)
    else:
      self.refresh(view, whole_file = True)
      self.loaded = True

  def on_modified(self, view):
    #we still need to do the whole file here because doing things like pasting
    #a block of code won't make the indent guides show up correctly
    self.refresh(view, whole_file = True)
    self.update_active_guides(view)
