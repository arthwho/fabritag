import os
import database_manager as db
from dotenv import load_dotenv

load_dotenv()

try:
    data = db.fetch_infraestrutura_data()
    print("Success fetching infra data")
    print(f"Total Camaras: {data['total_camaras']}")
    if data['lista_camaras']:
        print(f"Sample Camara: {data['lista_camaras'][0]}")
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
