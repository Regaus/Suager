import mimetypes
from sys import platform

import cherrypy

from utils import time


# logger = logging.getLogger("cherrypy")


class Calendar(object):
    @cherrypy.expose
    def index(self):
        print(f"{time.time()} > Cherry > Index page accessed")
        return "Hello World!"


def main():
    cherrypy.config.update({"log.screen": False, "log.access_file": "", "log.error_file": ""})
    cherrypy.engine.unsubscribe("graceful", cherrypy.log.reopen_files)
    # logging.config.dictConfig(LOG_CONF)
    cherrypy.config.update("webserver/server.conf")
    # cherrypy.tree.mount(Calendar(), "app.conf")
    print(f"{time.time()} > Cherry > Server launched")
    if platform.startswith("linux"):
        cherrypy.quickstart(Calendar(), "/", "webserver/app.conf")
    else:
        cherrypy.quickstart(Calendar(), "/", "webserver/app_windows.conf")


mimetypes.types_map[".ics"] = "text/calendar"


if __name__ == '__main__':
    main()
