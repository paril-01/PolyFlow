# BUG: growing list never cleared
_cache = []
def process(item):
    _cache.append(item)
    return item
