# BUG: circular import
from . import order_service
def process():
    return order_service.get_orders()
