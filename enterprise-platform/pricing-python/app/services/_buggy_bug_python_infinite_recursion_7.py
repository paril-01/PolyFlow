# BUG: no base case
def flatten(lst):
    result = []
    for item in lst:
        result.extend(flatten(item))
    return result
