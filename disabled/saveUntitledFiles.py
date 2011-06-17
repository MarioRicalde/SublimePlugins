import sublime, sublime_plugin
import time, os

# This class executes a callback function once self.delay seconds have elapsed since the last call to timer.notify()
# This allows a method like on_modified to repeatedly call notify without triggering the event multiple times per second.
class DelayedTimer:
  def __init__(self, delay, callback):
    self.delay = delay
    self.callback = callback
    self.lastRequest = 0

    self.scheduleTimer()

  def scheduleTimer(self):
    sublime.set_timeout(self.onTimer, 100)

  def onTimer(self):
    self.scheduleTimer()
    if self.lastRequest > 0 and self.lastRequest + self.delay < time.time():
      self.lastRequest = 0
      self.callback()

  def notify(self):
    self.lastRequest = time.time()

class SaveUntitledFiles(sublime_plugin.EventListener):
  def __init__(self):
    self.timer = DelayedTimer(5, self.saveViews)

    # self.views will be a mapping of buffer id to view object or None
    # if the value is None then it does not need to be saved, it is just storing the buffer id so we know we have it
    # if the value is a view object, then it needs to be saved
    self.views = {}

    self.path = os.path.join(sublime.packages_path(), 'User', 'UntitledFiles')
    if not os.path.exists(self.path):
      os.makedirs(self.path)

    # It appears that reading and saving the files in the constructor does not always work.
    # A small delay seems to allow everything to finish
    self.enabled = False
    sublime.set_timeout(self.enable, 100)

  def enable(self):
    self.enabled = True
    self.reopenFiles()

  # Timer Callback
  def saveViews(self):
    self.removeOldFiles()

    for id in self.views:
      self.saveView(self.views[id])

  def saveView(self, view):
    # No changes since last timer fire
    if view == None:
      return

    # read the contents of the view and save it
    name = 'buffer_'+str(view.buffer_id())
    content = view.substr(sublime.Region(0, view.size()))
    with open(os.path.join(self.path, name), 'wb') as f:
      f.write(content)

    # mark the view as not requiring another save
    self.views[view.buffer_id()] = None

  # remove any of the saved buffers that have since been closed
  def removeOldFiles(self):
    files = os.listdir(self.path)
    for filename in files:
      id = int(filename.split('buffer_')[1])
      if id not in self.views:
        os.remove(os.path.join(self.path, filename))

  def reopenFiles(self):
    files = os.listdir(self.path)
    for filename in files:
      with open(os.path.join(self.path, filename), 'rb') as f:
        content = f.read()
      os.remove(os.path.join(self.path, filename))

      view = sublime.active_window().new_file()
      edit = view.begin_edit()
      view.insert(edit, 0, content)
      view.end_edit(edit)
      self.saveView(view)

  # Marks a view as modified
  def add(self, view):
    if not self.enabled:
      return

    id = view.buffer_id()
    if view.file_name() == None and not view.is_scratch():
      self.views[id] = view
    elif id in self.views:
      del self.views[id]

  # Marks a view as having been closed
  def remove(self, view):
    if not self.enabled:
      return

    id = view.buffer_id()
    if id in self.views:
      del self.views[id]

  def on_post_save(self, view):
    self.remove(view)
    self.timer.notify()

  def on_close(self, view):
    self.remove(view)
    self.timer.notify()

  def on_new(self, view):
    self.add(view)
    self.timer.notify()

  def on_clone(self, view):
    self.add(view)
    self.timer.notify()

  def on_modified(self, view):
    self.add(view)
    self.timer.notify()