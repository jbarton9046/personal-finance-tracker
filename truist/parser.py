import os
import csv
import json
import glob
import re
from collections import defaultdict
from datetime import datetime
from dotenv import load_dotenv
load_dotenv()

PLAID_CLIENT_ID = os.getenv("PLAID_CLIENT_ID")
PLAID_SECRET = os.getenv("PLAID_SECRET")
PLAID_ENV = os.getenv("PLAID_ENV")

CATEGORY_KEYWORDS = {
    "Paychecks": ["PR PAYMENT", "MOBILE DEPOSIT"],
    "Cash Income": ["CASH TIP", "PHOTOGIG", "VENMO FROM", "BAR CASH", "WORK CASH", "CASH JOB"],
    "Fees": ["FEE", "SARASOTA CNTY LIBR"],
    "Camera": ["AMAZON MKTPL*NA09L", "421739594945978", "BEST BUY 00005629 06-20-25 SARASOTA FL 8834"],
    "Costco (repaid)": ["ANNUAL REN"],
    "Phone": ["STRAIGHTTALK", "JLPHONE", "VERIZON", "WALMART.C 702 SW 8TH S 06-22-25BENTONVILLE 8842 DEBIT CARD PURCHASE-PIN"],
    "Rent/Utilities": ["FPL", "FRONTIER", "COMCAST", "WATER", "ELECTRIC", "UTILIT"],
    "Eating Out": ["GECKOS", "TACO BELL", "MCDONALD'S", "JERSEY MIKES", "STARBUCKS", "DINER", "RESTAURANT", "CAFE", "DINE", "SUBWAY", "CHICK-FIL-A", "MAS TACOS", "CASA VIEJA", "400 DEGREE", "PF CHANG", "MELLOW MUSHROOM"],
    "Subscriptions": ["SPOTIFY", "YOUTUBE TV", "NETFLIX", "PELOTON"],
    "Transportation": ["CIRCLE K", "SARASOTA PARK", "UBER", "LYFT", "CAR WASH", "GAS", "TOLL", "BURT'S", "ADVANCE AUTO", "SHELL OIL", "EXXON", "BP"],
    "Online Shopping": ["EBAY", "SHOPIFY", "WALGREENS", "AMAZON", "AMAZON.COM", "AMZNFREETIME"],
    "Transfers": ["TRUIST ONLINE TRANSFER", "DEPOSIT TRANSFER"],
    "Truck": ["DT RETAIL"],
    "Insurance": ["STATE FARM"],
    "Clothes": ["ABERCROMBIE & FITC", "GOODWILL", "MISSION THRIFT", "ONCE UPON A CHILD", "PLATOS CLOSET", "HM.COM"],
    "Withdrawals": ["ATM", "CASH", "WITHDRAWL"],
    "Written Checks": ["CHECK"],
    "Venmo": ["VENMO"],
    "Groceries/Home": ["COSTCO", "TRADER JOE", "BESTBUYCOM80706770", "ACE HARDWARE", "ALDI", "WM SUPERC", "TARGET", "WALMART", "PUBLIX", "WAL-MART", "SAMS CLUB", "SAMSCLUB"],
    "Medical": ["RADIOLOG", "RX", "1-800 CONTACTS", "ODONOGHUE", "DERMATOL", "KORPATH", "CHEEKY", "CVS/PHARMACY", "PRIMEHEALTH"],
    "Credit Card": ["CITI", "BK OF AMER", "CAPITAL ONE"],
    "Flight": ["AIR", "SARASOTA A", "BNA", "CHARLOTTE COUNTY"],
    "OD Trans": ["OVERDRAFT"],
    "Entertainment": ["SKY ZONE", "HOBBYLOBB", "MAIN STREET CR", "PHOTODAY ORDER"],
    "Cosmetic": ["LUSH", "HAPPY NAI", "CHRISTOPHER TR", "MANATEE TECHNICAL"],
    "Kids": ["MISS SARASOTA", "STAGE DOOR", "CHURCH OF"],
    "Rosie": ["DIANE'S"],
    "Miscellaneous": []
}

EXCLUDE_DESCRIPTIONS = ["RETURN", "OVERDRAFT TRANSFER", "TRANSFER"]
REFUND_KEYWORDS = ["RETURN", "REFUND"]

def categorize_transaction(description, amount):
    """
    Categorize a transaction based on its description and amount.
    """
    desc_upper = description.upper()

    # 1) Check paycheck keywords first
    paycheck_keywords = ["PAYROLL", "MOBILE DEPOSIT", "PAYCHECK", "SALARY", "DIRECT DEPOSIT", "GUSTO PAY"]
    if any(keyword in desc_upper for keyword in paycheck_keywords):
        return "Paychecks"

    # 2) Refunds or returns — only if expense (negative amount)
    if "RETURN" in desc_upper and amount < 0:
        return "Refunds"

    # 3) Special rule for rent
    if abs(amount) == 2500:
        return "Rent/Utilities"

    # 4) Transfers always
    if any(keyword in desc_upper for keyword in ["TRANSFER"]):
        return "Transfers"

    # 5) Other categories
    for category, keywords in CATEGORY_KEYWORDS.items():
        for keyword in keywords:
            if keyword in desc_upper:
                return category

    # 6) Default to Miscellaneous
    return "Miscellaneous"

def load_transactions(filename):
    """
    Load transactions from a CSV file and categorize them.
    """
    transactions = []
    with open(filename, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            date_str = row.get('Posted Date', '') or row.get('Date', '')
            try:
                date_obj = datetime.strptime(date_str, "%m/%d/%Y")
                date_formatted = date_obj.strftime("%m/%d/%Y")
            except ValueError:
                date_obj = None
                date_formatted = date_str

            amt_str = row.get('Amount', '').replace('$', '').replace(',', '').strip()
            if amt_str.startswith('(') and amt_str.endswith(')'):
                try:
                    amt = -float(amt_str.strip('()'))
                except ValueError:
                    amt = 0.0
            else:
                try:
                    amt = float(amt_str)
                except ValueError:
                    amt = 0.0

            desc = row.get('Description', '').strip()
            if any(excl in desc.upper() for excl in EXCLUDE_DESCRIPTIONS if excl != "TRANSFER"):
                continue
            category = categorize_transaction(desc, amt)
            transactions.append({
                'date': date_formatted,
                'description': desc,
                'amount': amt,
                'category': category,
                'DateObj': date_obj
            })
    return transactions

def load_plaid_json(file_path):
    """
    Load transactions from a Plaid JSON file and categorize them.
    """
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    transactions = []
    for tx in data:
        date_str = tx.get("date", "")
        try:
            date_obj = datetime.strptime(date_str, "%Y-%m-%d")
            date_formatted = date_obj.strftime("%m/%d/%Y")
        except ValueError:
            date_obj = None
            date_formatted = date_str

        amt = float(tx.get("amount", 0.0))
        desc = tx.get("name", "")
        category = categorize_transaction(desc, amt)
        transactions.append({
            "date": date_formatted,
            "DateObj": date_obj,
            "description": desc,
            "amount": amt,
            "category": category
        })
    return transactions

def get_latest_plaid_json_file(folder_path):
    """
    Get the most recent Plaid JSON file from the folder.
    """
    pattern = os.path.join(folder_path, "plaid_*.json")
    json_files = glob.glob(pattern)
    if not json_files:
        raise FileNotFoundError("No Plaid JSON files found")
    return max(json_files, key=os.path.getmtime)

def load_all_transactions_from_folder(folder_path):
    """
    Load all CSV and latest Plaid JSON transactions from the folder, sorted by date.
    """
    all_transactions = []
    for filename in os.listdir(folder_path):
        if filename.endswith(".csv"):
            file_path = os.path.join(folder_path, filename)
            print(f"Loading CSV: {file_path}...")
            all_transactions.extend(load_transactions(file_path))
    try:
        latest_json_file = get_latest_plaid_json_file(folder_path)
        print(f"Loading latest Plaid JSON: {latest_json_file}...")
        all_transactions.extend(load_plaid_json(latest_json_file))
    except FileNotFoundError:
        print("No Plaid JSON files found, skipping JSON load.")
    all_transactions.sort(key=lambda tx: tx['DateObj'] or datetime.min)
    return all_transactions

def summarize_by_category(transactions):
    """
    Summarize transactions amounts by category, accounting for refunds.
    """
    category_sums = {}

    for tx in transactions:
        amt = tx.get('amount', 0)
        cat = tx.get('category', 'Miscellaneous')
        desc = tx.get('description', '').upper()

        # Skip Transfers from income/expense summaries
        if cat == "Transfers":
            continue

        # Check if transaction is a refund
        is_refund = any(keyword in desc for keyword in REFUND_KEYWORDS)

        if is_refund:
            # Refunds reduce expenses, so subtract absolute amount
            category_sums[cat] = category_sums.get(cat, 0) - abs(amt)
        else:
            # Normal transactions add their amount
            category_sums[cat] = category_sums.get(cat, 0) + amt

    return category_sums

def print_transactions(transactions):
    """
    Print all transactions with date, description, amount, and category.
    """
    for tx in transactions:
        print(f"{tx['date']} | {tx['description']} | ${tx['amount']:.2f} | {tx['category']}")

def print_income_expense_summary(category_sums):
    """
    Print income and expense summaries, where income is only Paychecks and Cash Income.
    """
    income = {
        cat: amt
        for cat, amt in category_sums.items()
        if amt > 0 and cat in ["Paychecks", "Cash Income"]
    }
    expenses = {
        cat: amt
        for cat, amt in category_sums.items()
        if amt < 0
    }

    print("\nIncome totals by category (Paychecks and Cash Income):")
    for category, total in sorted(income.items(), key=lambda x: x[1], reverse=True):
        print(f"{category}: ${total:.2f}")

    print("\nExpense totals by category (largest to smallest):")
    for category, total in sorted(expenses.items(), key=lambda x: abs(x[1]), reverse=True):
        print(f"{category}: ${-total:.2f}")

def print_category_transactions(transactions, category_name):
    """
    Print all transactions for a specific category.
    """
    print(f"\n--- {category_name} Transactions ---")
    for tx in transactions:
        if tx['category'] == category_name:
            print(f"{tx['date']}: {tx['description']} - ${tx['amount']:.2f}")

def print_transfers(transactions):
    """
    Print all transfer transactions.
    """
    print("\n--- Transfers ---")
    for tx in transactions:
        if tx['category'] == "Transfers":
            print(f"{tx['date']}: {tx['description']} - ${tx['amount']:.2f}")

def print_total_expenses(transactions):
    """
    Print total expenses (absolute value), excluding transfers.
    """
    total = sum(abs(tx['amount']) for tx in transactions if tx['amount'] < 0 and tx['category'] != "Transfers")
    print(f"\nTOTAL EXPENSES: ${total:.2f}")

from datetime import date, timedelta

def print_weekly_summary(transactions):
    """
    Print summaries for only the current week and the previous week.
    """
    weekly_data = defaultdict(lambda: defaultdict(float))
    for tx in transactions:
        date_obj = tx.get('DateObj')
        if not date_obj:
            continue
        year, week, _ = date_obj.isocalendar()
        cat = tx.get('category', 'Miscellaneous')
        amt = tx.get('amount', 0)
        if cat == "Transfers":
            continue
        weekly_data[(year, week)][cat] += amt

    # Get current and previous week numbers
    today = date.today()
    current_year, current_week, _ = today.isocalendar()
    last_week = today - timedelta(weeks=1)
    prev_year, prev_week, _ = last_week.isocalendar()

    # Only show current and previous week
    for (year, week) in sorted(weekly_data.keys()):
        if (year, week) in [(prev_year, prev_week), (current_year, current_week)]:
            print(f"\n=== Week {week} of {year} ===")
            cat_totals = weekly_data[(year, week)]
            sorted_cats = sorted(cat_totals.items(), key=lambda x: abs(x[1]), reverse=True)
            for category, total in sorted_cats:
                print(f"{category}: ${total:.2f}")
            print("------------------------")
            total_for_week = sum(cat_totals.values())
            print(f"TOTAL: ${total_for_week:.2f}")

def print_monthly_summary(transactions):
    """
    Print monthly income and expense summaries similar to weekly summary style.
    """
    monthly_groups = defaultdict(list)
    for tx in transactions:
        if tx['DateObj']:
            month_str = tx['DateObj'].strftime('%Y-%m')
        else:
            month_str = 'Unknown'
        monthly_groups[month_str].append(tx)

    for month in sorted(monthly_groups.keys()):
        month_txs = monthly_groups[month]
        category_sums = defaultdict(float)
        for tx in month_txs:
            if tx['category'] == 'Transfers':
                continue
            category_sums[tx['category']] += tx['amount']

        income = {cat: amt for cat, amt in category_sums.items() if amt > 0}
        expenses = {cat: amt for cat, amt in category_sums.items() if amt < 0}

        try:
            month_display = datetime.strptime(month, '%Y-%m').strftime('%B %Y')
        except ValueError:
            month_display = month
        print(f"--- {month_display} ---")

        print("\nIncome (largest to smallest):")
        for category, total in sorted(income.items(), key=lambda x: x[1], reverse=True):
            print(f"  {category}: ${total:.2f}")

        print("\nExpenses (largest to smallest):")
        for category, total in sorted(expenses.items(), key=lambda x: abs(x[1]), reverse=True):
            print(f"  {category}: ${-total:.2f}")

        print("-" * 30)
        print(f"Total Income:  ${sum(income.values()):.2f}")
        print(f"Total Expense: ${-sum(expenses.values()):.2f}\n")

def normalize_description(desc):
    """
    Normalize description for deduplication: lowercase, remove digits, normalize spaces.
    """
    desc = desc.lower()
    desc = re.sub(r'\d+', '', desc)
    desc = re.sub(r'\s+', ' ', desc).strip()
    return desc

def deduplicate_transactions(transactions):
    """
    Remove duplicate transactions based on date, amount (rounded), and normalized description.
    """
    seen = set()
    deduped = []
    for tx in transactions:
        key = (
            tx.get('date'),
            round(tx.get('amount', 0.0), 2),  # fixed default from 2 to 0.0
            normalize_description(tx.get('description', ''))
        )
        if key not in seen:
            seen.add(key)
            deduped.append(tx)
        else:
            print(f"🟡 Skipped duplicate: {tx['date']} | {tx['description']} | ${tx['amount']:.2f}")
    return deduped

def clean_transactions_for_json(transactions):
    """
    Convert DateObj datetime to string for JSON serialization.
    """
    cleaned = []
    for tx in transactions:
        tx_copy = tx.copy()
        if 'DateObj' in tx_copy:
            if isinstance(tx_copy['DateObj'], datetime):
                tx_copy['DateObj'] = tx_copy['DateObj'].strftime('%m/%d/%Y')
            else:
                del tx_copy['DateObj']
        cleaned.append(tx_copy)
    return cleaned

def save_transactions_to_json(transactions):
    """
    Save transactions to a JSON file with today's date in filename.
    """
    cleaned_transactions = clean_transactions_for_json(transactions)
    filename = f"statements/transactions_{datetime.now().strftime('%m%d%Y')}.json"
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(cleaned_transactions, f, indent=2)
    print(f"Saved transactions to {filename}")

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Transaction parser and summarizer.")
    parser.add_argument("--category", help="Print transactions for a specific category (e.g. 'Groceries/Home')")
    parser.add_argument("--weekly", action="store_true", help="Show weekly summary")
    parser.add_argument("--monthly", action="store_true", help="Show monthly summary")
    parser.add_argument("--json-only", action="store_true", help="Only save transactions to JSON, no printout")
    parser.add_argument("--add-cash", action="store_true", help="Add a manual cash transaction")
    args = parser.parse_args()

    folder = "statements"
    transactions = load_all_transactions_from_folder(folder)
    print(f"Loaded {len(transactions)} total transactions.")
    transactions = deduplicate_transactions(transactions)
    print(f"{len(transactions)} transactions after removing duplicates.")

    # ➕ Handle manual cash entry
    if args.add_cash:
        desc = input("Enter description: ").strip()
        amount_input = input("Enter amount (positive = income, negative = expense): ").strip()
        try:
            amount = float(amount_input)
        except ValueError:
            print("❌ Invalid amount.")
            exit(1)
        category = input("Enter category (default: 'Cash Income'): ").strip() or "Cash Income"
        
        tx = {
            'date': datetime.now().strftime('%m/%d/%Y'),
            'DateObj': datetime.now(),
            'description': desc,
            'amount': amount,
            'category': category
        }
        transactions.append(tx)
        print(f"✅ Added: {tx['date']} | {tx['description']} | ${tx['amount']:.2f} | {tx['category']}")

    if args.json_only:
        save_transactions_to_json(transactions)
    else:
        print_transactions(transactions)
        print_total_expenses(transactions)
        if args.category:
            print_category_transactions(transactions, args.category)
        print_transfers(transactions)
        save_transactions_to_json(transactions)

        if args.weekly:
            print_weekly_summary(transactions)
        if args.monthly:
            print("\n" + "=" * 7 + " MONTHLY SUMMARY " + "=" * 7 + "\n") 
            print_monthly_summary(transactions)

        print("\n❤️  Script by JL for Rachel ❤️")
