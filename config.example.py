import os
from urllib.parse import quote_plus

DB_USER = "root"
DB_PASSWORD = os.getenv("DRIVENOW_DB_PASSWORD", "YOUR_PASSWORD") 
DB_HOST = "localhost"
DB_PORT = 3306
DB_NAME = "drivenow_db"

DATABASE_URL = (f"mysql+pymysql://{DB_USER}:{quote_plus(DB_PASSWORD)}"
                    f"@{DB_HOST}:{DB_PORT}/{DB_NAME}")

# Optional (NOTIF-01): to send booking emails for real, fill these in with an email account.
# Leave them out and the app stays in test mode, saving each email in the outbox folder instead.
# EMAIL_HOST = "smtp.gmail.com"
# EMAIL_PORT = 587
# EMAIL_USER = "your.email@gmail.com"
# EMAIL_PASSWORD = "your app password"
