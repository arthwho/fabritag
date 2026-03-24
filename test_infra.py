import os
import database_manager as db
from dotenv import load_dotenv

load_dotenv()

try:
    data = db.fetch_infraestrutura_data()
    print("Success fetching infra data")
    print(f"Total Camaras: {data['total_camaras']}")
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
