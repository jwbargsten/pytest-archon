# Some web server logic

from myapp.database import store
from myapp.logic import AppLogic


def handle_request():
    app_logic = AppLogic()
    # Do stuff with request
    ...
    store(app_logic)
