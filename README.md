# Personal Finance Tracker

A professional-grade budgeting tool powered by the Plaid API, designed to automate financial data collection and help users make smarter, real-time spending decisions based on actual income, cash flow, and account activity.

---

## 💼 Overview

The Personal Finance Tracker is a CLI-based finance assistant that:

- Connects securely to users' bank accounts using the Plaid API
- Automatically fetches and refreshes transaction data
- Categorizes income and spending
- Filters out returns, overdrafts, and internal transfers
- Summarizes financial activity weekly or monthly
- Provides a clear picture of available spending money, dynamically

My goal is to replace manual spreadsheets with clean, automated financial insights, especially for freelancers, families, and individuals who want real-time control of their budgets.

---

## 🔗 Plaid API Integration

This app currently integrates the following Plaid products:

| Product                  | Purpose                                                                 |
|--------------------------|-------------------------------------------------------------------------|
| **Auth**                 | Retrieve account and routing numbers to name and find linked accounts   |
| **Transactions**         | Pull historical and live bank transactions, both income and expenses    |
| **Transactions Refresh** | Keep data current without requiring the user to reconnect               |
| **Statements**           | Enable monthly statement downloads and insights                         |
| **Identity**             | Confirm account ownership to prevent fraudulent use                     |
| **Identity Match**       | Match provided user info with linked account data for added verification|

---

## 🛠 Features

- ✅ Link multiple bank accounts via Plaid
- ✅ Automatically exclude returns, transfers, and overdrafts
- ✅ Weekly and monthly summaries with net cash flow
- ✅ Filter by category (e.g., groceries, subscriptions, gas)
- ✅ Optional export to CSV or JSON
- 🚧 Statement viewer + budgeting goals (coming soon)
- 🚧 Auto-alerts and web dashboard (coming soon)

---

## 🔧 Tech Stack

- **Python 3.10+**
- **Plaid API**
- **dotenv** for secure API key management
- **requests**, **csv**, **json** for data handling
- **VS Code** for development

---

## 📁 Project Structure

```bash
personal-finance-tracker/
├── statements/             # JSON and CSV transaction exports
├── screenshots/            # UI mockups and CLI screenshots
├── plaid_fetch.py          # Script that pulls transaction data from Plaid API
├── parser.py               # Core logic: filters, summaries, CLI
├── requirements.txt        # Python dependencies
├── .env                    # API keys and config (not committed)
└── README.md               # Project overview and documentation

🗺 Roadmap
 Automate transaction pulls using Plaid

 CLI summaries with category filters

 Monthly statement integration

 Web dashboard with charts (React or Flask)

 Add daily/weekly spending alerts

 OAuth-based user authentication for multi-user support

 Export features (.csv/.pdf)

 Rule-based auto-tagging (e.g., Venmo = “Transfer”)

🔐 Security Notes
API keys are stored in a .env file and never hardcoded

Only read-only access to bank account data via Plaid

No user credentials are stored at any time

Files like .env are listed in .gitignore to prevent accidental commits

📫 Contact
Built and maintained by Jack Barton
📍 Sarasota, Florida
🔗 https://github.com/jbarton9046
📧 jbarton9046@gmail.com

⚠️ Disclaimer
This tool is under active development and currently intended for personal and educational use only.
It is not a licensed financial advisor, and no financial decisions should be made solely based on its outputs.

