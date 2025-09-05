# create_users.py
import hashlib
import secrets
import pyodbc

def hash_password(password, salt=None):
    if salt is None:
        salt = secrets.token_hex(16)
    hashed = hashlib.sha256((password + salt).encode()).hexdigest()
    return f"sha256${salt}${hashed}"

def verify_password(stored_password, provided_password):
    try:
        _, salt, hashed = stored_password.split('$')
        new_hash = hashlib.sha256((provided_password + salt).encode()).hexdigest()
        return new_hash == hashed
    except:
        return False

def create_default_users():
    try:
        # Koneksi database
        conn = pyodbc.connect(
            "Driver={SQL Server};"
            "Server=localhost;"
            "Database=PenjualanKaosKaki;"
            "Trusted_Connection=yes;"
        )
        
        cursor = conn.cursor()
        
        # Cek jika tabel Users sudah ada, jika tidak buat tabel
        cursor.execute("""
            IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='Users' AND xtype='U')
            CREATE TABLE Users (
                id INT IDENTITY(1,1) PRIMARY KEY,
                username VARCHAR(50) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                nama VARCHAR(100) NOT NULL,
                role VARCHAR(20) DEFAULT 'kasir',
                created_at DATETIME DEFAULT GETDATE(),
                is_active BIT DEFAULT 1
            )
        """)
        
        # User admin
        admin_password = hash_password('admin123')
        cursor.execute("""
            IF NOT EXISTS (SELECT 1 FROM Users WHERE username = 'admin')
            INSERT INTO Users (username, password_hash, nama, role)
            VALUES ('admin', ?, 'Administrator', 'admin')
            ELSE
            UPDATE Users SET password_hash = ? WHERE username = 'admin'
        """, admin_password, admin_password)
        
        # User kasir
        kasir_password = hash_password('kasir123')
        cursor.execute("""
            IF NOT EXISTS (SELECT 1 FROM Users WHERE username = 'kasir')
            INSERT INTO Users (username, password_hash, nama, role)
            VALUES ('kasir', ?, 'Kasir Toko', 'kasir')
            ELSE
            UPDATE Users SET password_hash = ? WHERE username = 'kasir'
        """, kasir_password, kasir_password)
        
        conn.commit()
        
        # Verifikasi password
        cursor.execute("SELECT username, password_hash FROM Users")
        users = cursor.fetchall()
        
        print("=" * 50)
        print("USER ACCOUNTS CREATED/UPDATE SUCCESSFULLY!")
        print("=" * 50)
        
        for user in users:
            print(f"Username: {user[0]}")
            print(f"Password test: {'admin123' if user[0] == 'admin' else 'kasir123'}")
            print(f"Password valid: {verify_password(user[1], 'admin123' if user[0] == 'admin' else 'kasir123')}")
            print("-" * 30)
        
        print("✅ Default users created successfully!")
        print("🔑 Login credentials:")
        print("   Username: admin, Password: admin123")
        print("   Username: kasir, Password: kasir123")
        print("=" * 50)
        
    except Exception as e:
        print(f"❌ Error creating default users: {e}")
        print("Pastikan:")
        print("1. SQL Server sedang running")
        print("2. Database 'PenjualanKaosKaki' sudah ada")
        print("3. Koneksi string di script sesuai dengan setup Anda")
    finally:
        if conn:
            conn.close()

if __name__ == '__main__':
    create_default_users()