#!/usr/bin/env python
import re
import sys
import gtk
import appindicator

import os
from subprocess import check_output, CalledProcessError, STDOUT

os.environ["LC_ALL"] = "C"
try:
    interval = int(check_output(["git", "config", "indicator.interval"]))
except Exception:
    interval = 60 # seconds

def scan_git(fetch):
    report = []
    for filename in os.listdir("."):
        if os.path.isdir(filename):
            output = ''
            try:
                if fetch:
                    check_output(["git", "fetch"], cwd=filename, stderr=STDOUT)
                output = check_output(["git", "status", "-b", "--porcelain"], cwd=filename, stderr=STDOUT).split("\n")[:-1]
                if len(output) > 1:
                    report.append("%s has uncommitted files" % filename)
                m = re.search(r"\[(ahead \d+, behind \d+|ahead \d+|behind \d+)\]", output[0])
                if m:
                    report.append("%s needs to push/pull" % filename)
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

    def menu_setup(self):
        self.menu = gtk.Menu()

        self.status_item = gtk.MenuItem("No action required")
        self.status_item.set_sensitive(False)
        self.menu.append(self.status_item)

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
        self.check_git()
        gtk.timeout_add(interval * 1000, self.check_git)
        gtk.main()

    def quit(self, widget):
        sys.exit(0)

    def check_git(self, widget=None):
        report = scan_git(self.fetch)
        if report:
            self.status_item.set_label("\n".join(report))
            self.status_item.show()
            self.ind.set_status(appindicator.STATUS_ATTENTION)
        else:
            self.status_item.hide()
            self.ind.set_status(appindicator.STATUS_ACTIVE)
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
