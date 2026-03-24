import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

# Database Credentials
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_NAME = os.getenv("DB_NAME", "fabritag")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASS = os.getenv("DB_PASS", "1234")

def run_migration():
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASS
        )
        cur = conn.cursor()
        
        # Check if column exists
        cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name='movimentacao' AND column_name='posicao_vaga';")
        if not cur.fetchone():
            print("Adding posicao_vaga column to MOVIMENTACAO table...")
            cur.execute("ALTER TABLE MOVIMENTACAO ADD COLUMN posicao_vaga INT;")
            conn.commit()
            print("Migration successful.")
        else:
            print("Column 'posicao_vaga' already exists.")
            
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Migration error: {e}")

if __name__ == "__main__":
    run_migration()
