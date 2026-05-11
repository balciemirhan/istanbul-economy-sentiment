import os
from dotenv import load_dotenv

load_dotenv()

# Apify API
# APIFY_API_TOKEN = os.getenv("APIFY_API_TOKEN")
# APIFY_DATASET_ID = os.getenv("APIFY_DATASET_ID", "PgC0W1PKWRqaEwRND")

# X API Credentials
X_BEARER_TOKEN = os.getenv("X_BEARER_TOKEN")
X_API_KEY = os.getenv("X_API_KEY")
X_API_SECRET = os.getenv("X_API_SECRET")

# Database
DB_NAME = os.getenv("DB_NAME", "istanbul_ekonomi")

# NLP Model
SENTIMENT_MODEL = "savasy/bert-base-turkish-sentiment-cased"


