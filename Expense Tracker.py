from dataclasses import dataclass,field
from typing import List
import datetime as datetime
import re
import sqlite3
import sys
import pandas as pd
import matplotlib.pyplot as plt


@dataclass(frozen = True)
class Transaction:
    amount: float
    category: str
    date: str
    description: str

@dataclass
class Account:
    total: float = 0
    transactions: List[Transaction] = field(default_factory = list)

    def __post_init__(self):
        for transaction in loadTransactions():
            self.total += transaction.amount
            self.transactions.append(transaction)

    def addTransactions(self):
        new_transactions = getTransactions()
        self.transactions.extend(new_transactions)
        for transaction in new_transactions:
            self.total += transaction.amount
        
    def getTotal(self):
        return self.total

def main():
    account = Account(transactions=testData())
    saveTransactions(account.transactions)
    if input("Type 'n' for new entry or Enter: ").strip().lower() == "n":
        account.addTransactions()
        saveTransactions(account.transactions)
        print(f"Total: {account.getTotal()}")
    
    if not input("Type 'e' to exit or Enter to plot Data: ") == "e":
        plotData()

    else:
        sys.exit()


def getTransactions():
    transactions = []

    while True:
        try:
                #date
                pattern = r'^(0[1-9]|[12]\d|3[01])\.(0[1-9]|1[0-2])\.\d{4}$'
                date = input("Date (type 't' for today's time OR Format: Date.Month.Year): ").strip().lower()
                if re.search('^t', date):
                    date = str(datetime.datetime.today().strftime("%d.%m.%Y"))
                elif re.search(pattern, date):
                    pass
                else:
                    raise ValueError("Enter a valid date format")
                
                #category 
                category = str(input("Category (Food, Clothes, Transport, Entertainment, Utilities, Rent): ")).strip().lower()
                categories = ["food", "clothes", "transport", "entertainment", "utilities", "rent"]
                if category not in categories:
                    raise ValueError("Enter a valid Category")

                #description
                description = input("Additional Description (optional): ").strip().lower()
                if description == "":
                    description = " "

                #amount
                amount = float(input("Amount (Format: 14.5): ").strip().replace(",", "."))
                
                t = Transaction(amount, category, date, description)
                transactions.append(t)

        except ValueError as e:
            print(f"Error: {e}. Enter a valid Format")
            continue

        nextAction = input("Type 'n' for new Entry or press Enter: ").strip().lower()
        if not nextAction == "n":
            return transactions


def loadTransactions():
    transactions = []
    with sqlite3.connect("expenses.db") as con:
        cur = con.cursor()
        cur.execute(
        """ 
        CREATE TABLE IF NOT EXISTS transactions
            ( 
        date TEXT,  
        category TEXT,
        amount REAL, 
        description TEXT
            )
        """)
        result = cur.execute("SELECT date, category, amount, description FROM transactions")
        rows = result.fetchall()
        for row in rows:
            transactions.append(Transaction(amount = row[2], category = row[1], date = row[0], description = row[3]))
   
    return transactions


def saveTransactions(transactions):
    seen = set(loadTransactions())
 
    with sqlite3.connect("expenses.db") as con:
        cur = con.cursor()
        cur.execute(
        """ 
        CREATE TABLE IF NOT EXISTS transactions
            ( 
        date TEXT,  
        category TEXT,
        amount REAL, 
        description TEXT
            )
        """)
        for transaction in transactions:
            if transaction not in seen:
                cur.execute("INSERT INTO transactions (date, category, amount, description) Values (?, ?, ?, ?)",
                (transaction.date, transaction.category, transaction.amount, transaction.description))
                seen.add(transaction)
            else:
                pass


def sortDates(df):
    df["date"] = pd.to_datetime(df["date"], format="%d.%m.%Y")
    df = df.sort_values(by = "date")
    return df


def plotData():
    months = {
        1: "Jan", 2: "Feb", 3: "Mar", 4: "Apr", 5: "May", 6: "Jun",
        7: "Jul", 8: "Aug", 9: "Sep", 10: "Oct", 11: "Nov", 12: "Dec"
             }
    with sqlite3.connect("expenses.db") as con:
        df = pd.read_sql("SELECT * FROM transactions", con)
        fig, axs = plt.subplots(1,2, figsize = (15,10))

        df = sortDates(df)
        years = f"{str(df['date'][0])[:4]}-{str(df['date'].iloc[-1])[:4]}"

        if input("Type 'm' to see transactions per month: ").strip().lower() == "m":
            #First Graph per month
            df["month"] = df["date"].dt.month
            y = df.groupby("month")["amount"].sum()
            x = [months[i] for i in y.index]

            axs[0].bar(x, y, color = "lightcoral", width = 0.8)
            axs[0].tick_params(axis='x', rotation=45)
            axs[0].set_ylabel("Amount in $ per month")
            axs[0].set_xlabel("Transactions")
            axs[0].set_title(f"Amount of $ per transaction per month | {years}")

            #Second Graph per month
            monthNumber = int(input("Type 1-12 for each corresponding month: ").strip())
            monthData = df[df["month"] == monthNumber]
            categoriesSumMonth = monthData.groupby("category")["amount"].sum()

            axs[1].pie(categoriesSumMonth, labels = categoriesSumMonth.index, autopct = "%1.2f%%")
            axs[1].set_title(f"Percentage of Transactions per Category | {months[monthNumber]}")

        else:
            #First Graph per Day
            y = df.groupby("date")["amount"].sum()
            x = y.index.strftime("%d.%m")

            axs[0].bar(x, y, color = "lightcoral", width = 0.8)
            axs[0].tick_params(axis='x', rotation=45)
            axs[0].set_ylabel("Amount in $")
            axs[0].set_xlabel("Transactions")
            axs[0].set_title(f"Amount of $ per transaction | {years}")
        
            #Second Graph Overall
            categoriesSum = df.groupby("category")["amount"].sum()

            axs[1].pie(categoriesSum, labels = categoriesSum.index, autopct = "%1.2f%%")
            axs[1].set_title(f"Percentage of Transactions per Category | {years}")
        plt.tight_layout()
        plt.show()


def testData():
    transactions=[
    Transaction(45.20, "food", "01.01.2025", "bought vegetables and fruit"),
    Transaction(45.20, "food", "26.01.2026", "bought vegetables and fruit"),
    Transaction(20.00, "transport", "05.02.2025", "mvg ticket"),
    Transaction(89.99, "transport", "15.03.2025", "fuel refill"),
    Transaction(12.50, "food", "20.04.2025", "morning coffee at café"),
    Transaction(67.30, "utilities", "07.05.2025", "electricity bill"),
    Transaction(25.00, "entertainment", "10.06.2025", "movie ticket"),
    Transaction(9.75, "food", "13.07.2025", "bought chips and soda"),
    Transaction(54.40, "food", "15.08.2025", "lunch with a friend"),
    Transaction(32.60, "food", "17.09.2025", "weekly grocery shopping"),
    Transaction(120.00, "rent", "18.10.2025", "shared apartment rent payment"),
    Transaction(15.00, "entertainment", "20.11.2025", "bowling night"),
    Transaction(40.00, "clothes", "21.12.2025", "new jacket"),
    Transaction(8.50, "food", "22.01.2025", "breakfast sandwich"),
    Transaction(55.75, "utilities", "23.02.2025", "water bill"),
    Transaction(100.00, "rent", "25.03.2025", "monthly rent payment"),
    Transaction(5.00, "transport", "26.04.2025", "bus ticket"),
    Transaction(30.25, "food", "27.05.2025", "dinner takeaway"),
    Transaction(75.00, "clothes", "28.06.2025", "shoes purchase"),
    Transaction(20.00, "entertainment", "29.07.2025", "concert ticket"),
    Transaction(60.00, "utilities", "30.08.2025", "internet bill"),
    Transaction(13.45, "food", "01.09.2025", "snacks and drinks"),
    Transaction(22.00, "transport", "05.09.2025", "train ticket"),
    Transaction(80.00, "rent", "10.09.2025", "partial rent payment"),
    Transaction(15.30, "entertainment", "15.09.2025", "museum entry"),
    Transaction(42.00, "clothes", "20.09.2025", "t-shirt and jeans"),
    Transaction(55.00, "utilities", "25.09.2025", "gas bill"),
    Transaction(7.20, "food", "30.09.2025", "coffee and croissant"),
    Transaction(18.00, "transport", "05.10.2025", "taxi fare"),
    Transaction(25.00, "entertainment", "10.10.2025", "theater ticket"),
    ]
    return transactions


if __name__ == "__main__":
    main()