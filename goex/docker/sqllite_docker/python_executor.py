from io import StringIO
from contextlib import redirect_stdout
import sys
import os

def code_execute():
    f = StringIO()
    code = os.environ['CODE']
    with redirect_stdout(f):
        exec(code, globals())

    exec_stdout = f.getvalue()
    print(exec_stdout)
    return exec_stdout

if __name__ == "__main__":
    globals()[sys.argv[1]]()
