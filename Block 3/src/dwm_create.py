import sqlite3
from pathlib import Path


def execute_sql_file(conn: sqlite3.Connection, sql_file_path: Path):
    """Читает SQL файл и выполняет все запросы из него"""
    with open(sql_file_path, 'r', encoding='utf-8') as f:
        sql_content = f.read()
    
    cursor = conn.cursor()
    
    statements = sql_content.split(';')
    
    for statement in statements:
        statement = statement.strip()
        if statement:  # Пропускаем пустые строки
            cursor.execute(statement)
    
    conn.commit()


def create_star_schema(conn: sqlite3.Connection):
    """Создаёт структуру star schema из SQL файла"""
    sql_file = Path(__file__).parent.parent / 'ddl' / 'create_schema.sql'
    execute_sql_file(conn, sql_file)


def populate_star_schema(conn: sqlite3.Connection):
    """Заполняет star schema данными из SQL файла"""
    sql_file = Path(__file__).parent.parent / 'ddl' / 'populate_schema.sql'
    execute_sql_file(conn, sql_file)