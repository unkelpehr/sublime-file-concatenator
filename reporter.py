import thread
import functools
import time
import sublime

class Reporter(object):
    def __init__(self, msg, listener):
        self.msg = msg
        self.listener = listener
        thread.start_new_thread(self.run_thread, ())

    def run_thread(self):
        progress = ""
        while True:
            if self.listener.is_running:
                if len(progress) >= 3:
                    progress = ""
                progress += "."
                sublime.set_timeout(lambda: self.listener.update_status(self.msg, progress), 0)
                time.sleep(0.1)
            else:
                break
