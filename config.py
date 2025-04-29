from sqlalchemy.engine import URL

class Config:
    SECRET_KEY = 'your_secret_key'

    SQLALCHEMY_DATABASE_URI = URL.create(
        "mssql+pyodbc",
        username="sa",
        password="Aa@123456",
        host="DESKTOP-ICP5P36",
        database="mri",
        query={
            "driver": "ODBC Driver 17 for SQL Server",
            "TrustServerCertificate": "yes",
            "unicode_results": "yes",
            "charset": "utf8"
        }
    )

    SQLALCHEMY_TRACK_MODIFICATIONS = False
