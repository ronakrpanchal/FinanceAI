import sqlite3

def create_users_db():
    conn = sqlite3.connect('finance_ai.db')
    cursor = conn.cursor()
    
    # Create the users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username VARCHAR(50) NOT NULL,
            password VARCHAR(50) NOT NULL
        )
    ''')
    conn.commit()
    return conn

def create_transactions_db():
    conn = sqlite3.connect('finance_ai.db')
    cursor = conn.cursor()
    
    # Create the transactions table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            transaction_date DATE,
            amount DECIMAL(10, 2),
            amount_type VARCHAR(10),
            category VARCHAR(50),
            description TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')
    
    conn.commit()
    return conn

def create_subscriptions_db():
    conn = sqlite3.connect('finance_ai.db')
    cursor = conn.cursor()
    
    # Create the subscriptions table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS subscriptions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            name VARCHAR(100) NOT NULL,
            cost DECIMAL(10, 2) NOT NULL,
            usage VARCHAR(20) NOT NULL,
            priority VARCHAR(20) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id),
            CHECK (usage IN ('Daily', 'Weekly', 'Monthly', 'Rarely')),
            CHECK (priority IN ('High', 'Medium', 'Low'))
        )
    ''')
    
    conn.commit()
    return conn

def create_debts_db():
    conn = sqlite3.connect('finance_ai.db')
    cursor = conn.cursor()
    
    # Create the debts table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS debts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            name VARCHAR(100) NOT NULL,
            amount DECIMAL(10, 2) NOT NULL,
            interest_rate DECIMAL(5, 2) NOT NULL,
            priority VARCHAR(20) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id),
            CHECK (priority IN ('High', 'Medium', 'Low'))
        )
    ''')
    
    conn.commit()
    return conn

def create_budget_db():
    conn = sqlite3.connect('finance_ai.db')
    cursor = conn.cursor()
    
    # Create table for budgets if not exists
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS budgets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            budget_data TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)
    conn.commit()
    return conn
    

if __name__ == '__main__':
    create_users_db()
    create_transactions_db()
    create_subscriptions_db()
    create_debts_db()
    create_budget_db()
    print("Database created successfully")