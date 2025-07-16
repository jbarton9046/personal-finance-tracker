from dotenv import load_dotenv
import os
print(os.listdir('.'))  # Lists files in current directory

load_dotenv()

print("PLAID_CLIENT_ID =", os.getenv("PLAID_CLIENT_ID"))
print("PLAID_SECRET =", os.getenv("PLAID_SECRET"))
print("PLAID_ENV =", os.getenv("PLAID_ENV"))
