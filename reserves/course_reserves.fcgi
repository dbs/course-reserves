#!/usr/bin/env python
from flup.server.fcgi import WSGIServer
from course_reserves import app 

if __name__ == '__main__':
    WSGIServer(app, bindAddress='/tmp/refdesk-fcgi.sock').run()
