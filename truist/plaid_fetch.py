import time
import json
import os
import logging
from datetime import datetime, timedelta
from plaid.exceptions import ApiException

from plaid.api import plaid_api
from plaid.configuration import Configuration
from plaid.api_client import ApiClient

from plaid.model.item_public_token_exchange_request import ItemPublicTokenExchangeRequest
from plaid.model.transactions_get_request import TransactionsGetRequest

# Import Plaid Link token creation models
from plaid.model.link_token_create_request import LinkTokenCreateRequest
from plaid.model.country_code import CountryCode
from plaid.model.link_token_create_request_user import LinkTokenCreateRequestUser
from plaid.model.products import Products

from dotenv import load_dotenv
load_dotenv()

PLAID_CLIENT_ID = os.getenv("PLAID_CLIENT_ID")
PLAID_SECRET = os.getenv("PLAID_SECRET")
PLAID_ENV = os.getenv("PLAID_ENV")

if not all([PLAID_CLIENT_ID, PLAID_SECRET, PLAID_ENV]):
    raise EnvironmentError("❌ One or more Plaid environment variables are missing.")

print(f"✅ PLAID_CLIENT_ID loaded: {bool(PLAID_CLIENT_ID)}")
print(f"✅ PLAID_SECRET loaded: {bool(PLAID_SECRET)}")
print(f"✅ PLAID_ENV loaded: {PLAID_ENV}")


# Configure logging
os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    filename="logs/plaid_fetch.log",
    level=logging.INFO,
    format="%(asctime)s %(levelname)s: %(message)s"
)

PLAID_ENV_HOSTS = {
    "sandbox": "https://sandbox.plaid.com",
    "development": "https://development.plaid.com",
    "production": "https://production.plaid.com"
}

if PLAID_ENV not in PLAID_ENV_HOSTS:
    raise ValueError(f"Invalid PLAID_ENV value: {PLAID_ENV}")

configuration = Configuration(
    host=PLAID_ENV_HOSTS[PLAID_ENV],
    api_key={
        'clientId': PLAID_CLIENT_ID,
        'secret': PLAID_SECRET,
    }
)


api_client = ApiClient(configuration)
client = plaid_api.PlaidApi(api_client)

def create_link_token():
    request = LinkTokenCreateRequest(
        products=[Products("transactions")],
        client_name="Your App Name",
        country_codes=[CountryCode("US")],
        language="en",
        user=LinkTokenCreateRequestUser(client_user_id="unique_user_id_123")  # Replace with your user id logic
    )
    response = client.link_token_create(request)
    return response['link_token']

def main():
    logging.info("Plaid fetch started")

    # Generate and print the link token for frontend Plaid Link
    link_token = create_link_token()
    print("Your Plaid link_token is:", link_token)
    print("\nUse this token in your frontend to initialize Plaid Link and get the public_token.\n")

    try:
        # Prompt for public_token from frontend Plaid Link flow
        public_token = input("Please enter the public_token obtained from Plaid Link: ").strip()

        exchange_request = ItemPublicTokenExchangeRequest(public_token=public_token)
        exchange_response = client.item_public_token_exchange(exchange_request)
        access_token = exchange_response.access_token

        start_date = (datetime.now() - timedelta(days=30)).date()
        end_date = datetime.now().date()

        transactions_request = TransactionsGetRequest(
            access_token=access_token,
            start_date=start_date,
            end_date=end_date
        )

        max_retries = 5
        for attempt in range(max_retries):
            try:
                transactions_response = client.transactions_get(transactions_request)
                break
            except ApiException as e:
                if "PRODUCT_NOT_READY" in str(e):
                    logging.warning(f"Product not ready, retrying {attempt + 1}/{max_retries}...")
                    time.sleep(3)
                else:
                    logging.error(f"ApiException: {e}")
                    raise
        else:
            logging.error("Max retries reached, product still not ready.")
            return

        transactions = transactions_response['transactions']

        os.makedirs("statements", exist_ok=True)
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        filename = f"statements/plaid_transactions_{timestamp}.json"

        with open(filename, "w") as f:
            json.dump(
                [tx.to_dict() for tx in transactions],
                f,
                indent=2,
                default=str
            )

        logging.info(f"Saved {len(transactions)} transactions to '{filename}'")
        print(f"✅ Saved {len(transactions)} transactions to '{filename}'")

    except Exception as e:
        logging.error(f"Unexpected error: {e}", exc_info=True)
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
