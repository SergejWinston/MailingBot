import sqlite3

NAME_BASE = "database.db"

def return_table(table: str) -> list: 
    conn = sqlite3.connect(NAME_BASE)
    cursor = conn.cursor() 
    sql_query = f"""SELECT * FROM {table}"""
    cursor.execute(sql_query) 
    results = cursor.fetchall() 
    conn.close() 
    return results

def check(table: str, columns: str, search_text: str) -> list: 
    conn = sqlite3.connect(NAME_BASE)
    cursor = conn.cursor()
    sql_query = f"""SELECT * FROM {table} WHERE {columns} = '{search_text}';"""
    cursor.execute(sql_query)
    results = cursor.fetchall()
    conn.close()
    return list(results)

def check_contains(table: str, columns: str, search_text: str) -> list: 
    conn = sqlite3.connect(NAME_BASE)
    cursor = conn.cursor()
    sql_query = f"""SELECT *\nFROM {table}\nWHERE ',' || {columns} || ',' LIKE '%{search_text}%';"""
    cursor.execute(sql_query)
    results = cursor.fetchall()
    conn.close()
    return list(results)

def insert(table: str, columns: str, values: str) -> None:
    conn = sqlite3.connect(NAME_BASE)
    cursor = conn.cursor() 
    sql_query = f"""INSERT INTO {table} ({columns})
                    VALUES ({values});"""
    cursor.execute(sql_query) 
    conn.commit()  
    conn.close()  

def count_row(table: str) -> int:
    conn = sqlite3.connect(NAME_BASE)
    cursor = conn.cursor() 
    sql_query = f"""SELECT * FROM {table}"""
    cursor.execute(sql_query) 
    results = cursor.fetchall() 
    conn.close() 
    return len(results)

def set_state(id: int, state: int) -> None:
    conn = sqlite3.connect(NAME_BASE)
    cursor = conn.cursor() 
    sql_query = f"""UPDATE users
                    SET state = {state}
                    WHERE user_id = '{id}';"""
    cursor.execute(sql_query) 
    conn.commit()  
    conn.close() 
    return

def delete_chat(id: int) -> None:
    conn = sqlite3.connect(NAME_BASE)
    cursor = conn.cursor() 
    sql_query = f"""DELETE FROM "main"."chats" WHERE Unique_ID = '{id}'"""
    cursor.execute(sql_query) 
    conn.commit()  
    conn.close() 
    return

def remove_line(table, column, value):
    conn = sqlite3.connect(NAME_BASE)
    cursor = conn.cursor() 
    sql_query = f"""DELETE FROM {table} WHERE {column} = '{value}'"""
    cursor.execute(sql_query) 
    conn.commit()  
    conn.close() 
    return

def get_pos_line(table: int, pos: int) -> list:
    conn = sqlite3.connect(NAME_BASE)
    cursor = conn.cursor() 
    sql_query = f"""SELECT * FROM {table} LIMIT 1 OFFSET {pos};"""
    cursor.execute(sql_query) 
    results = cursor.fetchall() 
    conn.close() 
    return len(results)

def get_pos_line_result(table: int, pos: int) -> list:
    conn = sqlite3.connect(NAME_BASE)
    cursor = conn.cursor() 
    sql_query = f"""SELECT * FROM {table} LIMIT 1 OFFSET {pos};"""
    cursor.execute(sql_query) 
    results = cursor.fetchall() 
    conn.close() 
    return results

def set(table: str, search_column: str, search_value: str, change_column: str, change_value: str) -> None:
    conn = sqlite3.connect(NAME_BASE)
    cursor = conn.cursor() 
    sql_query = f"""UPDATE {table} SET {change_column} = "{change_value}" WHERE {search_column} = "{search_value}" """
    cursor.execute(sql_query) 
    conn.commit()  
    conn.close() 
    return


def set_null(table: str, search_column: str, search_value: str, change_column: str) -> None:
    conn = sqlite3.connect(NAME_BASE)
    cursor = conn.cursor() 
    sql_query = f"""UPDATE {table} SET {change_column} = NULL WHERE {search_column} = "{search_value}" """
    cursor.execute(sql_query) 
    conn.commit()  
    conn.close() 
    return