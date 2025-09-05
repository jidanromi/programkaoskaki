# app.py
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from functools import wraps  # Import wraps dari functools
import pyodbc
from datetime import datetime
import os
import hashlib
import secrets

app = Flask(__name__)
app.secret_key = 'your-super-secret-key-ubah-ini-dengan-key-anda-sendiri'

# Koneksi Database
def get_db_connection():
    try:
        conn = pyodbc.connect(
            "Driver={SQL Server};"
            "Server=localhost;"
            "Database=PenjualanKaosKaki;"
            "Trusted_Connection=yes;"
        )
        return conn
    except Exception as e:
        print(f"Database connection error: {e}")
        return None

# Fungsi hash password
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

# Middleware untuk cek login
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': 'Login required'}), 401
        return f(*args, **kwargs)
    return decorated_function

# Decorator untuk role checking
def role_required(required_role):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'role' not in session:
                return jsonify({'error': 'Login required'}), 401
            if session['role'] != required_role and session['role'] != 'admin':
                return jsonify({'error': 'Insufficient permissions'}), 403
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def admin_required(f):
    return role_required('admin')(f)

# Routes untuk authentication
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        data = request.json
        username = data.get('username')
        password = data.get('password')
        
        print(f"Login attempt: username={username}, password={password}")
        
        conn = get_db_connection()
        if conn:
            try:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT id, username, password_hash, nama, role FROM Users WHERE username = ? AND is_active = 1",
                    username
                )
                user = cursor.fetchone()
                
                if user:
                    print(f"User found: {user[1]}, Hash: {user[2]}")
                    print(f"Verifying password: {verify_password(user[2], password)}")
                
                if user and verify_password(user[2], password):
                    session['user_id'] = user[0]
                    session['username'] = user[1]
                    session['nama'] = user[3]
                    session['role'] = user[4]
                    
                    print("Login successful!")
                    return jsonify({
                        'message': 'Login berhasil',
                        'user': {
                            'id': user[0],
                            'nama': user[3],
                            'role': user[4]
                        }
                    })
                else:
                    print("Login failed: invalid credentials")
                    return jsonify({'error': 'Username atau password salah'}), 401
                    
            except Exception as e:
                print(f"Login error: {e}")
                return jsonify({'error': str(e)}), 500
            finally:
                conn.close()
        
        return jsonify({'error': 'Database connection failed'}), 500
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return jsonify({'message': 'Logout berhasil'})

@app.route('/api/current-user')
@login_required
def get_current_user():
    return jsonify({
        'id': session['user_id'],
        'username': session['username'],
        'nama': session['nama'],
        'role': session['role']
    })

# Fungsi untuk generate kode produk otomatis
def generate_kode_produk():
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            # Cek produk terakhir
            cursor.execute("SELECT TOP 1 kode FROM Produk ORDER BY id DESC")
            last_product = cursor.fetchone()
            
            if last_product:
                # Ambil angka dari kode terakhir dan tambah 1
                last_code = last_product[0]
                if last_code.startswith('KK'):
                    try:
                        last_number = int(last_code[2:])
                        new_number = last_number + 1
                        return f"KK{new_number:04d}"  # Format: KK0001, KK0002, dst.
                    except ValueError:
                        pass
            
            # Jika tidak ada produk atau format tidak sesuai, mulai dari KK0001
            return "KK0001"
            
        except Exception as e:
            print(f"Error generating product code: {e}")
            return "KK0001"
        finally:
            conn.close()
    return "KK0001"

# Routes
@app.route('/')
def index():
    return render_template('index.html')

# API untuk generate kode produk otomatis
@app.route('/api/generate-kode-produk', methods=['GET'])
@login_required
def generate_kode_produk_api():
    kode = generate_kode_produk()
    return jsonify({'kode': kode})

# API untuk Produk
@app.route('/api/produk', methods=['GET'])
@login_required
def get_produk():
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM Produk ORDER BY nama")
            columns = [column[0] for column in cursor.description]
            produk = [dict(zip(columns, row)) for row in cursor.fetchall()]
            return jsonify(produk)
        except Exception as e:
            return jsonify({'error': str(e)}), 500
        finally:
            conn.close()
    return jsonify({'error': 'Database connection failed'}), 500

@app.route('/api/produk', methods=['POST'])
@login_required
@admin_required
def tambah_produk():
    data = request.json
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            
            # Generate kode otomatis jika tidak disediakan
            kode = data.get('kode')
            if not kode:
                kode = generate_kode_produk()
            
            cursor.execute("""
                INSERT INTO Produk (kode, nama, warna, ukuran, bahan, harga_beli, harga_jual, stok)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, kode, data['nama'], data['warna'], data['ukuran'], 
               data['bahan'], data['harga_beli'], data['harga_jual'], data['stok'])
            
            conn.commit()
            return jsonify({'message': 'Produk berhasil ditambahkan', 'kode': kode})
        except Exception as e:
            return jsonify({'error': str(e)}), 500
        finally:
            conn.close()
    return jsonify({'error': 'Database connection failed'}), 500

# API untuk Penjualan
@app.route('/api/penjualan', methods=['POST'])
@login_required
def tambah_penjualan():
    data = request.json
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            
            # Default customer_id jika tidak ada
            customer_id = data.get('customer_id', 1)
            
            # Cek jika customer_id ada
            cursor.execute("SELECT id FROM Customer WHERE id = ?", (customer_id,))
            if not cursor.fetchone():
                # Jika customer tidak ada, buat customer default
                cursor.execute("""
                    INSERT INTO Customer (kode, nama, alamat, telepon, email)
                    VALUES ('CUST001', 'Customer Umum', '-', '-', '-')
                """)
                customer_id = 1
            
            # Insert penjualan
            no_transaksi = f"TRX-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
            cursor.execute("""
                INSERT INTO Penjualan (no_transaksi, tanggal, customer_id, total)
                VALUES (?, GETDATE(), ?, ?)
            """, no_transaksi, customer_id, data['total'])
            
            # Get inserted ID
            cursor.execute("SELECT @@IDENTITY AS id")
            penjualan_id = cursor.fetchone()[0]
            
            # Insert detail penjualan
            for item in data['items']:
                cursor.execute("""
                    INSERT INTO DetailPenjualan (penjualan_id, produk_id, jumlah, harga, subtotal)
                    VALUES (?, ?, ?, ?, ?)
                """, penjualan_id, item['produk_id'], item['jumlah'], item['harga'], item['subtotal'])
                
                # Update stok
                cursor.execute("UPDATE Produk SET stok = stok - ? WHERE id = ?", 
                              item['jumlah'], item['produk_id'])
            
            conn.commit()
            return jsonify({'message': 'Penjualan berhasil', 'no_transaksi': no_transaksi})
            
        except Exception as e:
            conn.rollback()
            return jsonify({'error': str(e)}), 500
        finally:
            conn.close()
    return jsonify({'error': 'Database connection failed'}), 500

@app.route('/api/penjualan', methods=['GET'])
@login_required
def get_penjualan():
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT p.no_transaksi, p.tanggal, c.nama as customer, p.total
                FROM Penjualan p
                INNER JOIN Customer c ON p.customer_id = c.id
                ORDER BY p.tanggal DESC
            """)
            columns = [column[0] for column in cursor.description]
            penjualan = [dict(zip(columns, row)) for row in cursor.fetchall()]
            return jsonify(penjualan)
        except Exception as e:
            return jsonify({'error': str(e)}), 500
        finally:
            conn.close()
    return jsonify({'error': 'Database connection failed'}), 500

# API untuk delete produk
@app.route('/api/produk/<int:product_id>', methods=['DELETE'])
@login_required
@admin_required
def hapus_produk(product_id):
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            
            # Cek apakah produk ada dalam transaksi
            cursor.execute("""
                SELECT COUNT(*) FROM DetailPenjualan 
                WHERE produk_id = ?
            """, product_id)
            
            transaction_count = cursor.fetchone()[0]
            
            if transaction_count > 0:
                return jsonify({'error': 'Tidak dapat menghapus produk yang sudah ada dalam transaksi'}), 400
            
            # Hapus produk
            cursor.execute("DELETE FROM Produk WHERE id = ?", product_id)
            conn.commit()
            
            if cursor.rowcount == 0:
                return jsonify({'error': 'Produk tidak ditemukan'}), 404
                
            return jsonify({'message': 'Produk berhasil dihapus'})
            
        except Exception as e:
            conn.rollback()
            return jsonify({'error': str(e)}), 500
        finally:
            conn.close()
    return jsonify({'error': 'Database connection failed'}), 500

# API untuk mendapatkan user role
@app.route('/api/user-role')
@login_required
def get_user_role():
    return jsonify({'role': session['role']})

if __name__ == '__main__':
    app.run(debug=True, port=5000)