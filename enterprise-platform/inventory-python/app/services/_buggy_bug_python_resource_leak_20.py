# BUG: file handle never closed
def read_config():
    f = open('config.yml')
    return f.read()
