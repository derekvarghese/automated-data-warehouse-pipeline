import pyodbc

driver = 'ODBC Driver 18 for SQL Server'
server = 'LAPTOP-T6I8ED1E\\SQLEXPRESS'
database = 'AutomatedDWPipeline'
trusted_connection = 'yes'

connection_string = (
    f'DRIVER={{{driver}}};'
    f'SERVER={server};'
    f'DATABASE={database};'
    f'Trusted_Connection={trusted_connection};'
    f'TrustServerCertificate=yes;'
)

def get_connection():
    conn = pyodbc.connect(connection_string)
    return conn


if __name__ == "__main__":
    try:
        conn = get_connection()
        if conn:
            print("Connection Successful")
    except Exception as e:
        print(f"Error occurred: {e}")