import sublime, sublime_plugin
import re, os

blockScope = u'meta.property-list.css source.css'
nameScope = u'meta.property-name.css'
valueScope = u'meta.property-value.css'
language = u'Packages/CSS/CSS.tmLanguage'

class CssSorter:
  def __init__(self, view):
    self.view = view
    #print self.view.lines(sublime.Region(0, self.view.size()))
    #print self.view.visible_region()
    region = self.view.visible_region()
    #half = (region.b - region.a) / 2
    #top = min(region.a + half, self.view.size())
    #print top

    self.parseBlocks()

    self.view.show(region.a)
    #self.view.show_at_center(region)

  def parseBlocks(self):
    start = 0
    while start < self.view.size():
      # quick hack to jump to the start of a property list
      region = self.view.find(u'{', start, sublime.LITERAL)
      if region == None:
        break

      # ensure we are at the start of a property list and not in a string
      if self.view.scope_name(region.a).find(blockScope) < 0:
        start = region.a + 1
        continue

      # iterate to find the end of the contiuous property list section
      # The below css declaration returns a property list scope region that ends at the first colon of the first rule
      # So, in this case, we have to keep iterating as long as the regions/scopes contain property-list.css
      # .test4 {-moz-border-radius: 1px;border-top-width: 1px;border: none;border-bottom-width: 1px;}
      end = self.view.extract_scope(region.a).b
      while True:
        if self.view.scope_name(end).find(blockScope) < 0:
          break
        end = self.view.extract_scope(end).b

      self.parseBlock(region.a+1, end)
      start = end

  def parseBlock(self, start, end):
    region = sublime.Region(start, end)
    existingContent = self.view.substr(region)

    # don't sort if /*nosort*/ is in the css block
    if re.search(r'/\*\s*nosort\s*\*/', existingContent) != None:
      return

    rules, tail = self.parseRules(start, end)
    if rules == None or len(rules) == 0:
      return
    rules.sort(self.compareLines)

    output = map(lambda rule: rule['rule'], rules)
    output = (''.join(output))+tail

    # Only perform the edit if it needs to be sorted to avoid unnecessary jumping / undo states
    if output != existingContent:
      editObject = self.view.begin_edit()
      self.view.replace(editObject, region, output)
      self.view.end_edit(editObject)

  def parseRules(self, start, end):
    rules = []
    while start < end:
      ruleNameStart, ruleNameEnd = self.parseToScope(start, end, nameScope)
      #print 'N%s %s' % (ruleNameStart, ruleNameEnd)
      if ruleNameStart == None:
        break

      ruleValueStart, ruleValueEnd = self.parseToScope(ruleNameEnd, end, valueScope)
      #print 'V%s %s' % (ruleValueStart, ruleValueEnd)
      if ruleValueStart == None:
        break

      data = {'rule': self.view.substr(sublime.Region(start, ruleValueEnd))}
      data['sortRule'] = self.view.substr(sublime.Region(ruleNameStart, ruleValueEnd)).strip()
      data['sortPrefix'] = ''
      match = re.match(r'^(\-[a-zA-Z]+\-)(.*)', data['sortRule'])
      if match != None:
        data['sortRule'] = match.group(2)
        data['sortPrefix'] = match.group(1)
      data['sortName'] = data['sortRule'].split(':')[0].strip()
      rules.append(data)

      start = ruleValueEnd

    return rules, self.view.substr(sublime.Region(start, end))

  # This is a custom sorting function for the css rules
  # If there are duplicate rule names, then they should remain in the same order, regardless of value
  # If a rule name is a prefix of the other rule name (like border/border-width), the shorter should always come first
  # Lastly -moz- and such should be ignored
  def compareLines(self, a, b):
    if a['sortName'] == b['sortName']:
      return cmp(a['sortPrefix'], b['sortPrefix'])

    if a['sortName'].startswith(b['sortName']):
      return 1
    elif b['sortName'].startswith(a['sortName']):
      return -1
    else:
      return cmp(a['sortRule'], b['sortRule'])

  # This function traverses until it finds the first instance of scope
  # It continues parsing until it finds the last instance of that scope
  # It stops if it exceeds blockEnd
  def parseToScope(self, start, blockEnd, targetScope):
    # Find the first instance of scope
    while start < blockEnd:
      # Ignoring whitespace is purely an optimization
      c = self.view.substr(start)
      if c != ' ' and c != '\n':
        scope = self.view.scope_name(start).strip()
        if scope.find(targetScope) >= 0:
          break
      start += 1

    # If the loop didn't break early, then we did not find the scope
    if start >= blockEnd:
      return None, None

    # Now find the end of the scope region
    end = start
    while end < blockEnd:
      # Find the end of the region that includes end
      region = self.view.extract_scope(end)
      if region.b == end:
        break

      # Make sure it is still part of the scope region
      scope = self.view.scope_name(end)
      if scope.find(targetScope) < 0:
        break

      # Some scopes regions don't encompass the full extent of the scope, so we need to keep iterating
      # until we hit the end of this continuous section of scope
      end = region.b

    return start, end

class SortCss(sublime_plugin.TextCommand):
  def run(self, edit):
    CssSorter(self.view)

class SortCssListener(sublime_plugin.EventListener):
  def on_pre_save(self, view):
    if view.settings().get('sort_css_on_save', True):
      if view.settings().get('syntax') == language:
        CssSorter(view)

class TestSortCss(sublime_plugin.WindowCommand):
  def run(self):
    path = os.path.join(sublime.packages_path(), 'MyPlugins', 'test', 'sortCss')
    inPath = os.path.join(path, 'in')
    outPath = os.path.join(path, 'out')

    files = os.listdir(inPath)
    for filename in files:
      view = self.window.open_file(os.path.join(inPath, filename))
      view.run_command('sort_css')
      content = view.substr(sublime.Region(0, view.size()))


      with open(os.path.join(outPath, filename), 'rb') as f:
        targetContent = f.read()

      content = content.replace('\n', '').replace('\r', '')
      targetContent = targetContent.replace('\n', '').replace('\r', '')

      print u"%s matches: %s" % (filename, content == targetContent)