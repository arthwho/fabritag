import os
import database_manager as db
from dotenv import load_dotenv

load_dotenv()

try:
    # Try with ID 1 which we know exists from previous test
    data = db.fetch_camara_detalhes(1)
    print("Success fetching camara details")
    print(f"Camara: {data['nome']}")
    print(f"Lotes: {len(data['lotes'])}")
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
