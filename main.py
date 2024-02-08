import psycopg2
from psycopg2 import sql

connection = psycopg2.connect(
    dbname='finance',
    user='postgres',
    password='YOUR_PASSWORD',
    host='localhost',
    port='5432'
)

cursor = connection.cursor()

tables_queries = (
    """
    CREATE TABLE IF NOT EXISTS Users
    (id SERIAL PRIMARY KEY, 
     name VARCHAR(255) NOT NULL,
     birthday DATE);
    """,

    """
    CREATE TABLE IF NOT EXISTS Categories
    (id SERIAL PRIMARY KEY, 
     name VARCHAR(100) NOT NULL
     );
    """,

    """
    CREATE TABLE IF NOT EXISTS Money
    (id SERIAL PRIMARY KEY, 
     value DECIMAl (10,2),  
     trans_date DATE
     );
    """,

    """
    CREATE TABLE IF NOT EXISTS Wallet
    (id SERIAL PRIMARY KEY, 
     user_id INTEGER, 
     category_id INTEGER,
     money_id INTEGER,
     FOREIGN KEY (user_id) REFERENCES Users (id) ON UPDATE CASCADE ON DELETE CASCADE, 
     FOREIGN KEY (category_id) REFERENCES Categories (id) ON UPDATE CASCADE ON DELETE CASCADE,
     FOREIGN KEY (money_id) REFERENCES Money (id) ON UPDATE CASCADE ON DELETE CASCADE
     );
    """
)

for query in tables_queries:
    cursor.execute(query)
    connection.commit()


class User:
    def __init__(self, dbname, user, password, host, port):
        self.connection = psycopg2.connect(dbname=dbname, user=user, password=password,
                                           host=host, port=port)
        self.connection.set_session(autocommit=True)
        self.cursor = self.connection.cursor()

    def add_user(self, name: str, date: str):
        query = sql.SQL("INSERT INTO Users (name, birthday) VALUES (%s, %s)")
        self.cursor.execute(query, ((name, ), date))

    def add_money(self,  name: str, categories: str, value: float, date_trans: str):
        money_query = sql.SQL("INSERT INTO Money (value, trans_date) VALUES (%s, %s)")
        self.cursor.execute(money_query, (value, date_trans))

        query = sql.SQL(""" INSERT INTO Wallet (user_id, category_id, money_id)
            VALUES ((SELECT id FROM Users WHERE name = %s), 
            (SELECT id FROM Categories WHERE name = %s), 
            (SELECT id FROM Money WHERE value = %s AND trans_date = %s))""")
        self.cursor.execute(query, ((name, ), categories, value, date_trans))

    def get_info_by_name(self, name):
        query = sql.SQL("""
       SELECT users.name AS user_name,
       categories.name AS category_name,
       money.value AS money_value,
       money.trans_date AS money_trans_date
       FROM wallet
       INNER JOIN users ON wallet.user_id = users.id
       INNER JOIN categories ON wallet.category_id = categories.id
       INNER JOIN money ON wallet.money_id = money.id;""")
        self.cursor.execute(query, (name, ))
        data = self.cursor.fetchall()
        return data

    def get_info_by_categories(self, name, categories):
        query = sql.SQL("""
       SELECT users.name, categories.name AS category_name,
       money.value AS money_value,
       money.trans_date AS money_trans_date
       FROM wallet
       INNER JOIN users ON wallet.user_id = users.id
       INNER JOIN categories ON wallet.category_id = categories.id
       INNER JOIN money ON wallet.money_id = money.id
       WHERE users.name = %s AND categories.name = %s;""")
        self.cursor.execute(query, (name, categories))
        user = self.cursor.fetchall()
        return user

    def summ_money(self, date, name):
        query = sql.SQL("""
               select sum(value) from money
               inner join wallet on wallet.money_id = money.id
               inner join users on users.id = wallet.user_id 
               where trans_date < %s AND users.name = %s;""")
        self.cursor.execute(query, (date, name))
        user = self.cursor.fetchall()
        return user

    def close(self):
        self.cursor.close()
        self.connection.close()


categories = ['Продукты', 'Транспорт', 'Жилье', 'Здоровье', 'Развлечения']


def choose_expense_category():

    print("Выберите категорию расходов:")
    for i, category in enumerate(categories, start=1):
        print(f"{i}. {category}")

    choice = int(input("Введите номер категории: "))

    if choice < 1 or choice > len(categories):
        print("Некорректный выбор. Попробуйте снова.")
        choose_expense_category()
    else:
        selected_category = categories[choice - 1]
        return selected_category


def check_user_exists(user_name):
    cursor.execute("SELECT id FROM users WHERE name = %s", (user_name,))
    result = cursor.fetchone()
    if result:
        return False
    else:
        print("Такого пользователя не существует, попробуйте ещё раз!")
        return True


db = User(
    dbname='finance',
    user='postgres',
    password='YOUR_PASSWORD',
    host='localhost',
    port='5432'
)

while True:
    print("1. Добавить пользователя")
    print("2. Добавить затраты пользователя по категориям")
    print("3. Посмотреть все затраты пользователя")
    print("4. Посмотреть затраты пользователя по категориям")
    print("5. Посмотреть сумму затрат до определенного времени")
    print("6. Выход")

    choice = int(input("Выберите действие (1-6): "))

    match choice:
        case 1:
            name = input("Имя пользователя: ")
            birthday = input("Дата рождения пользователя (ДД/ММ/ГГГГ): ")
            state = True
            while state:
                parts = birthday.split("/")
                if len(parts) != 3 or not all(part.isdigit() for part in parts):
                    print("Некорректный формат даты. Попробуйте еще раз.")
                    birthday = input("Дата рождения сотрудника (день/месяц/год): ")
                    continue

                day, month, year = map(int, parts)
                if day < 1 or day > 31 or month < 1 or month > 12 or year < 0:
                    print("Некорректная дата. Попробуйте еще раз.")
                    birthday = input("Дата рождения сотрудника (день/месяц/год): ")
                    continue
                state = False

            db.add_user(name, birthday)
        case 2:
            state = True
            while state:
                name = input("Имя пользователя: ")
                state = check_user_exists(name)
            selected_category = choose_expense_category()
            state = True
            while state:
                value = input("Введите значение: ")
                if value.isdigit() and float(value) > 0:
                    value = float(value)
                    state = False
                else:
                    print("Ошибка ввода, попробуйте ещё раз")
            transe_date = input("Введите дату транзакции (ДД/ММ/ГГГГ): ")
            state = True
            while state:
                parts = transe_date.split("/")
                if len(parts) != 3 or not all(part.isdigit() for part in parts):
                    print("Некорректный формат даты. Попробуйте еще раз.")
                    transe_date = input("Введите дату транзакции: ")
                    continue

                day, month, year = map(int, parts)
                if day < 1 or day > 31 or month < 1 or month > 12 or year < 0:
                    print("Некорректная дата. Попробуйте еще раз.")
                    transe_date = input("Введите дату транзакции: ")
                    continue
                state = False

            db.add_money(name, selected_category, value, transe_date)

        case 3:
            state = True
            while state:
                name = input("Имя пользователя: ")
                state = check_user_exists(name)
            info = db.get_info_by_name(name)

            for item in info:
                name, category, amount, date = item
                print(f"Имя пользователя: {name}")
                print(f"Категория расхода: {category}")
                print(f"Сумма расхода: {amount}")
                print(f"Дата расхода: {date}")

        case 4:
            state = True
            while state:
                name = input("Имя пользователя: ")
                state = check_user_exists(name)
            categories = choose_expense_category()
            info = db.get_info_by_categories(name, categories)

            for item in info:
                name, category, amount, date = item
                print(f"Имя пользователя: {name}")
                print(f"Категория расхода: {category}")
                print(f"Сумма расхода: {amount}")
                print(f"Дата расхода: {date}")

        case 5:
            date = input("Введите дату (ДД/ММ/ГГГГ): ")
            state = True
            while state:
                parts = date.split("/")
                if len(parts) != 3 or not all(part.isdigit() for part in parts):
                    print("Некорректный формат даты. Попробуйте еще раз.")
                    date = input("Введите дату: ")
                    continue

                day, month, year = map(int, parts)
                if day < 1 or day > 31 or month < 1 or month > 12 or year < 0:
                    print("Некорректная дата. Попробуйте еще раз.")
                    date = input("Введите дату: ")
                    continue
                state = False
            state = True
            while state:
                name = input("Имя пользователя: ")
                state = check_user_exists(name)

            sum_value = db.summ_money(date, name)
            sum_value_str = str(sum_value)
            sum_value_numeric = sum_value_str.split("'")[1]

            print(f"Cумма равна: {sum_value_numeric}")
        case 6:
            break
        case _:
            print("Некорректный выбор. Пожалуйста, выберите действие от 1 до 4.")


db.close()
