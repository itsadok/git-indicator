#!/usr/bin/env python
import re
import sys
import signal
import gtk
import appindicator

import os
from subprocess import check_output, CalledProcessError, STDOUT, Popen

os.environ["LC_ALL"] = "C"
try:
    interval = int(check_output(["git", "config", "indicator.interval"]))
except Exception:
    interval = 60 # seconds

def scan_git(fetch):
    report = []
    for filename in os.listdir("."):
        if os.path.isdir(filename):
            try:
                if fetch:
                    check_output(["git", "fetch"], cwd=filename, stderr=STDOUT)
                output = check_output(["git", "status", "-b", "--porcelain"], cwd=filename, stderr=STDOUT).split("\n")[:-1]
                if len(output) > 1:
                    report.append(("%s has uncommitted files" % filename, ["git-cola"], filename))
                if re.search(r"\[ahead \d+\]", output[0]):
                    report.append(("%s needs to push" % filename, ["gnome-terminal", "--disable-factory", "-x", "bash" , "-c", """bash --rcfile <(echo 'git push && echo "Press any key to close terminal, interrupt to leave open" && read -n 1 && exit')"""], filename))
                elif re.search(r"\[behind \d+\]", output[0]):
                    report.append(("%s needs to pull" % filename,  ["gnome-terminal", "--disable-factory", "-x", "bash" , "-c", """bash --rcfile <(echo 'git pull && echo "Press any key to close terminal, interrupt to leave open" && read -n 1 && exit')"""], filename))
                elif re.search(r"\[ahead \d+, behind \d+\]", output[0]):
                    report.append(("%s needs to pull&push" % filename,  ["gnome-terminal", "--disable-factory", "-x", "bash" , "-c", """bash --rcfile <(echo 'git pull && git push; echo "Press any key to close terminal, interrupt to leave open" && read -n 1 && exit')"""], filename))
            except CalledProcessError:
                report.append("Error checking %s" % filename)
    return report

class GitMonitor(object):
    def __init__(self):
        self.ind = appindicator.Indicator("git-indicator",
                                           "active",
                                           appindicator.CATEGORY_APPLICATION_STATUS)
        self.ind.set_status(appindicator.STATUS_ACTIVE)
        self.ind.set_icon_theme_path(os.path.abspath(os.path.dirname(__file__)))
        self.ind.set_attention_icon("attention")

        self.menu_setup()
        self.ind.set_menu(self.menu)

        self.fetch = True
        self.new_items = []
        self.report_items = []
        self.action_pids = set()

    def do_add_item(self, widget):
        print "add item"
        self.new_items.append(gtk.MenuItem("New item %d" % (len(self.new_items) + 1)))
        self.new_items[-1].show()
        self.menu.insert(self.new_items[-1], len(self.new_items) - 1)

    def do_clear_items(self, widget):
        for item in self.new_items:
            self.menu.remove(item)

    def menu_setup(self):
        self.menu = gtk.Menu()

        self.pause_item = gtk.MenuItem("Pause fetching")
        self.pause_item.connect("activate", self.toggle_fetching)
        self.pause_item.show()
        self.menu.append(self.pause_item)

        self.refresh_item = gtk.MenuItem("Refresh")
        self.refresh_item.connect("activate", self.check_git)
        self.refresh_item.show()
        self.menu.append(self.refresh_item)

        self.quit_item = gtk.MenuItem("Quit")
        self.quit_item.connect("activate", self.quit)
        self.quit_item.show()
        self.menu.append(self.quit_item)

    def main(self):
        signal.signal(signal.SIGCHLD, self.sig_child)
        gtk.timeout_add(50, self.check_git_first)
        gtk.timeout_add(interval * 1000, self.check_git)
        gtk.main()

    def sig_child(self, signum, frame):
        pid, status = os.wait()
        if pid in self.action_pids:
            self.action_pids.remove(pid)
            print "refreshing git"
            self.check_git()

    def git_action(self, cmd, cwd):
        def action(widget):
            pid = Popen(cmd, cwd=cwd).pid
            self.action_pids.add(pid)
        return action

    def quit(self, widget):
        sys.exit(0)

    def check_git_first(self, widget=None):
        self.check_git()
        return False

    def check_git(self, widget=None):
        report = scan_git(self.fetch)
        for item in self.report_items:
            self.menu.remove(item)
        self.report_items = []

        if report:
            self.ind.set_status(appindicator.STATUS_ATTENTION)
        else:
            self.ind.set_status(appindicator.STATUS_ACTIVE)

        for line, cmd, cwd in report:
            self.report_items.append(gtk.MenuItem(line))
            self.report_items[-1].show()
            if cmd:
                self.report_items[-1].connect("activate", self.git_action(cmd, cwd))
            self.menu.insert(self.report_items[-1], len(self.report_items) - 1)
        return True

    def toggle_fetching(self, widget):
        self.fetch = not self.fetch
        if self.fetch:
            self.pause_item.set_label("Pause fetching")
        else:
            self.pause_item.set_label("Resume fetching")

if __name__ == "__main__":
    indicator = GitMonitor()
    indicator.main()
