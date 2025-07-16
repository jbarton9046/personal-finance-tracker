import os
import argparse
from dotenv import load_dotenv
from plaid.api import plaid_api
from plaid.model.item_public_token_exchange_request import ItemPublicTokenExchangeRequest
from plaid.configuration import Configuration
from plaid.api_client import ApiClient

# Load environment variables
load_dotenv()

PLAID_CLIENT_ID = os.getenv("PLAID_CLIENT_ID")
PLAID_SECRET = os.getenv("PLAID_SECRET")
PLAID_ENV = os.getenv("PLAID_ENV")

# Map Plaid environment string to actual endpoint URL
env_map = {
    "sandbox": "https://sandbox.plaid.com",
    "development": "https://development.plaid.com",
    "production": "https://production.plaid.com"
}

configuration = Configuration(
    host=env_map.get(PLAID_ENV, "https://sandbox.plaid.com"),
    api_key={
        'clientId': PLAID_CLIENT_ID,
        'secret': PLAID_SECRET,
    }
)

api_client = ApiClient(configuration)
client = plaid_api.PlaidApi(api_client)

def exchange_public_token(public_token: str) -> str:
    try:
        request = ItemPublicTokenExchangeRequest(public_token=public_token)
        response = client.item_public_token_exchange(request)
        access_token = response['access_token']
        print("Access Token:", access_token)
        return access_token
    except Exception as e:
        print("Error exchanging public token:", e)
        return None

def save_token_to_file(token: str, path: str = ".access_token"):
    with open(path, "w") as f:
        f.write(token)
    print(f"Access token saved to {path}")

def save_token_to_env(token: str, env_path: str = ".env"):
    with open(env_path, "a") as f:
        f.write(f"\nPLAID_ACCESS_TOKEN={token}")
    print(f"Access token appended to {env_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Exchange a Plaid public token for an access token.")
    parser.add_argument("--public_token", "-p", help="The public token from Plaid Link", required=True)
    parser.add_argument("--save_to", "-s", choices=["file", "env"], default="file",
                        help="Where to save the access token: 'file' (.access_token) or 'env' (.env)")

    args = parser.parse_args()

    access_token = exchange_public_token(args.public_token)

    if access_token:
        if args.save_to == "file":
            save_token_to_file(access_token)
        elif args.save_to == "env":
            save_token_to_env(access_token)