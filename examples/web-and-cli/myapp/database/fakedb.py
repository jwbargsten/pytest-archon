# A fake DB

import sqlite3

from myapp.logic.applogic import AppLogic


def store(app_logic: AppLogic):
    conn = sqlite3.connect(":memory:")
    # Do stuff with the API
    ...
    conn.close()
