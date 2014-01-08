# git-indicator for ubuntu

A simple ubuntu app indicator that lets you know if any of the monitored git repositories require attention.

Inspired by [git-dude](http://github.com/sickill/git-dude), and the late SVN-Monitor,
[RIP](https://github.com/tgmayfield/svn-monitor).

git-indicator is meant to work with checked out repositories, not bare ones. The idea is to tell you if there's
a reason to do commit, push or pull your current branch.

# Requirements

AFAIK, this thing only works on the latest ubuntu.
By default, git-cola is used for committing.

# Installation and Usage

Clone the git-indicator repository into some convenient location:

    git clone https://github.com/itsadok/git-indicator ~/.git-indicator

If you don't have one yet, create a directory that will contain the repositories you want to monitor:

    mkdir ~/monitored-repos
    cd ~/monitored-repos
    # You can clone a new repository into here,
    git clone https://github.com/jquery/jquery
    # You can move your repositories to be under here,
    mv ~/projects/myawesomwapp ./
    # Or you can just link them here, that works too.
    ln -s ~/projects/myproject ./

To start git-indicator, run it from the monitored directory:

    cd ~/monitored-repos
    python ~/.git-indicator/git-indicator.py &

# To do

Haven't figured out yet how to run it automatically on startup.
Should probably show different icons based on actions required.

# Author

Israel Tsadok. Code license - [CC0](http://creativecommons.org/publicdomain/zero/1.0/).

Git Logo by [Jason Long](http://twitter.com/jasonlong) is licensed under the [Creative Commons Attribution 3.0
Unported License](http://creativecommons.org/licenses/by/3.0/).