import os
from dotenv import load_dotenv
from dhanhq import DhanContext, dhanhq

# Load .env
load_dotenv()

# Read credentials
CLIENT_ID = os.getenv("DHAN_CLIENT_ID")
ACCESS_TOKEN = os.getenv("DHAN_ACCESS_TOKEN")

# Create Context
context = DhanContext(
    CLIENT_ID,
    ACCESS_TOKEN
)

# Create Dhan Client
dhan = dhanhq(context)

print("✅ Dhan Client Connected")

funds = dhan.get_fund_limits()

print(funds)