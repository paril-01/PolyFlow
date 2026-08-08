# BUG: shared mutable state without lock
counter = 0
def increment():
    global counter
    temp = counter
    counter = temp + 1
