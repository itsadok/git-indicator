#!/usr/bin/env python
import re
import sys
import signal
import gtk
import appindicator

import os
from subprocess import check_output, CalledProcessError, STDOUT, Popen

def get_config(key, default, wrap=None):
    try:
        value = check_output(["git", "config", "indicator.%s" % key])
        if wrap:
            value = wrap(value)
        return value
    except Exception:
        return default

class Action(object):
    def __init__(self, command, terminal):
        self.command = command
        self.terminal = terminal

def get_config_action(action_name, default_command, default_terminal):
    command = get_config("actions.%s" % action_name, default_command)
    terminal = get_config("actions.%s.terminal" % action_name, default_terminal, bool)
    return Action(command, terminal)

# Prevent GTK warnings from appearing in the console
devnull = open(os.devnull, 'w')
sys.stderr = devnull

os.environ["LC_ALL"] = "C"
interval = get_config("interval", 60, int)
actions = {
    "commit": Action("git-cola", terminal=False),
    "pull": Action("git pull", terminal=True),
    "push": Action("git push", terminal=True),
    "sync": Action("git pull", terminal=True)
}

for action_name in actions:
    action = actions[action_name]
    actions[action_name] = get_config_action(action_name, action.command, action.terminal)

def scan_git(fetch):
    report = []
    for filename in os.listdir("."):
        if not filename.startswith(".") and os.path.isdir(filename):
            try:
                if fetch:
                    check_output(["git", "fetch"], cwd=filename, stderr=STDOUT)
                output = check_output(["git", "status", "-b", "--porcelain"], cwd=filename, stderr=STDOUT).split("\n")[:-1]
                if len(output) > 1:
                    report.append(("%s has uncommitted files" % filename, "commit", filename))
                if re.search(r"\[ahead \d+\]", output[0]):
                    report.append(("%s needs to push" % filename, "push", filename))
                elif re.search(r"\[behind \d+\]", output[0]):
                    report.append(("%s needs to pull" % filename,  "pull", filename))
                elif re.search(r"\[ahead \d+, behind \d+\]", output[0]):
                    report.append(("%s needs to pull&push" % filename,  "sync", filename))
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
            self.check_git()

    def git_action(self, action_name, cwd):
        def action(widget):
            if not actions[action_name].terminal:
                args = [ actions[action_name].command ]
            else:
                args = ["gnome-terminal", "--disable-factory", "-x", "bash" , "-c", """bash --rcfile <(echo '%s && echo "Press any key to close terminal, interrupt to leave open" && read -n 1 && exit')""" % actions[action_name].command]

            pid = Popen(args, cwd=cwd).pid
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

        for line, action_name, cwd in report:
            self.report_items.append(gtk.MenuItem(line))
            self.report_items[-1].show()
            if action:
                self.report_items[-1].connect("activate", self.git_action(action_name, cwd))
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
