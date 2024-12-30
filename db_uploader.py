import pandas as pd
from sqlalchemy import create_engine

def upload_csv_to_postgres(csv_filename):
    """
    Upload CSV file to PostgreSQL running in Docker
    """
    try:
        # Connection parameters for Docker setup
        # engine = create_engine(
        #     'postgresql://postgres:yourpassword@localhost:5432/your_database'
        #     from sqlalchemy import create_engine
        # )
        engine = create_engine("postgresql+psycopg2://fahimah:fahimah123@postgres:5432/llm_db")

        
        
        # Read CSV from the mounted data directory
        df = pd.read_csv(f'/data/{csv_filename}')
        
        # Upload to PostgreSQL
        table_name = csv_filename.split('.')[0]  # Use filename as table name
        df.to_sql(table_name, engine, if_exists='replace', index=False)
        
        print(f"Successfully uploaded {csv_filename} to table '{table_name}'")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    csv_filename = "MOCK_DATA.csv"  # Replace with your CSV filename
    upload_csv_to_postgres(csv_filename)