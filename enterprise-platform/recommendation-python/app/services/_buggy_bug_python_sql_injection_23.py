# BUG: string concatenation in SQL
def get_user(name):
    query = f"SELECT * FROM users WHERE name = '{name}'"
    return db.execute(query)
