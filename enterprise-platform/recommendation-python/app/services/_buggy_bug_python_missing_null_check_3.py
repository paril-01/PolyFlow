# BUG: no null check
def get_price(product):
    return product['pricing']['base_price'] * 1.1
