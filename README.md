![](https://raw.githubusercontent.com/isislab/CTFd/master/CTFd/static/original/img/logo.png)
====

[![CTFd Slack](https://slack.ctfd.io/badge.svg)](https://slack.ctfd.io/)

CTFd is a CTF in a can. Easily modifiable and has everything you need to run a jeopardy style CTF.

Install: 
 1. `./prepare.sh` to install dependencies using apt.
 2. Modify [CTFd/config.py](https://github.com/isislab/CTFd/blob/master/CTFd/config.py) to your liking.
 3. Use `python serve.py` in a terminal to drop into debug mode.
 4. [Here](https://github.com/isislab/CTFd/wiki/Deployment) are some deployment options

Live Demo:
https://demo.ctfd.io/

Reverse Engineering Module:
https://reversing.ctfd.io/

Logo by [Laura Barbera](http://www.laurabb.com/)

Theme by [Christopher Thompson](https://github.com/breadchris)

Cam's Instructions

to run virtual environment from base directory

1. virtualenv -p /usr/bin/python2.7.1 env
2. source env/bin/activate
3. cd CFTD_Senior_Project
4. ./prepare.sh

and to end it run

1. deactivate
