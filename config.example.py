import os
from urllib.parse import quote_plus

DB_USER = "root"
DB_PASSWORD = os.getenv("DRIVENOW_DB_PASSWORD", "YOUR_PASSWORD") 
DB_HOST = "localhost"
DB_PORT = 3306
DB_NAME = "drivenow_db"

DATABASE_URL = (f"mysql+pymysql://{DB_USER}:{quote_plus(DB_PASSWORD)}"
                    f"@{DB_HOST}:{DB_PORT}/{DB_NAME}")