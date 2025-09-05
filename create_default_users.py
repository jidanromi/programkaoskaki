# create_default_users.py
from app import app, hash_password

def create_default_users():
    with app.app_context():
        conn = app.get_db_connection()
        if conn:
            try:
                cursor = conn.cursor()
                
                # User admin
                admin_password = hash_password('admin123')
                cursor.execute("""
                    IF NOT EXISTS (SELECT 1 FROM Users WHERE username = 'admin')
                    INSERT INTO Users (username, password_hash, nama, role)
                    VALUES ('admin', ?, 'Administrator', 'admin')
                """, admin_password)
                
                # User kasir
                kasir_password = hash_password('kasir123')
                cursor.execute("""
                    IF NOT EXISTS (SELECT 1 FROM Users WHERE username = 'kasir')
                    INSERT INTO Users (username, password_hash, nama, role)
                    VALUES ('kasir', ?, 'Kasir Toko', 'kasir')
                """, kasir_password)
                
                conn.commit()
                print("Default users created successfully!")
                
            except Exception as e:
                print(f"Error creating default users: {e}")
            finally:
                conn.close()

if __name__ == '__main__':
    create_default_users()