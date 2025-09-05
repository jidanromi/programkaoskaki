# program_penjualan_sqlserver.py
import pyodbc
from datetime import datetime
import json

class DatabaseConnection:
    def __init__(self):
        self.connection = None
        self.connect()
    
    def connect(self):
        try:
            # Ganti dengan koneksi string SQL Server Anda
            connection_string = (
                "Driver={SQL Server};"
                "Server=VivoBookX415JA;"
                "Database=PenjualanKaosKaki;"
                "Trusted_Connection=yes;"  # Untuk Windows Authentication
                # atau untuk SQL Authentication:
                # "UID=username;PWD=password;"
            )
            self.connection = pyodbc.connect(connection_string)
            print("Berhasil terhubung ke SQL Server")
        except Exception as e:
            print(f"Error koneksi database: {e}")
    
    def execute_query(self, query, params=None):
        try:
            cursor = self.connection.cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            
            if query.strip().upper().startswith('SELECT'):
                return cursor.fetchall()
            else:
                self.connection.commit()
                return cursor.rowcount
        except Exception as e:
            print(f"Error executing query: {e}")
            return None
    
    def close(self):
        if self.connection:
            self.connection.close()

class PenjualanKaosKaki:
    def __init__(self):
        self.db = DatabaseConnection()
    
    # ===== MASTER PRODUK =====
    def tambah_produk(self):
        print("\n=== TAMBAH PRODUK ===")
        
        kode = input("Kode produk: ")
        
        # Cek jika kode sudah ada
        result = self.db.execute_query("SELECT id FROM Produk WHERE kode = ?", (kode,))
        if result:
            print("Kode produk sudah ada!")
            return
        
        data = (
            kode,
            input("Nama produk: "),
            input("Warna: "),
            input("Ukuran: "),
            input("Bahan: "),
            float(input("Harga beli: ")),
            float(input("Harga jual: ")),
            int(input("Stok awal: "))
        )
        
        query = """
        INSERT INTO Produk (kode, nama, warna, ukuran, bahan, harga_beli, harga_jual, stok)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        if self.db.execute_query(query, data):
            print("Produk berhasil ditambahkan!")
    
    def lihat_produk(self):
        print("\n=== DAFTAR PRODUK ===")
        
        query = "SELECT * FROM Produk ORDER BY nama"
        products = self.db.execute_query(query)
        
        if not products:
            print("Tidak ada data produk.")
            return
        
        for i, p in enumerate(products, 1):
            print(f"{i}. {p.kode} - {p.nama}")
            print(f"   Warna: {p.warna}, Ukuran: {p.ukuran}")
            print(f"   Harga: Rp {p.harga_jual:,.0f}, Stok: {p.stok}")
            print("-" * 40)
    
    # ===== MASTER CUSTOMER =====
    def tambah_customer(self):
        print("\n=== TAMBAH CUSTOMER ===")
        
        kode = input("Kode customer: ")
        
        # Cek jika kode sudah ada
        result = self.db.execute_query("SELECT id FROM Customer WHERE kode = ?", (kode,))
        if result:
            print("Kode customer sudah ada!")
            return
        
        data = (
            kode,
            input("Nama customer: "),
            input("Alamat: "),
            input("Telepon: "),
            input("Email: ")
        )
        
        query = """
        INSERT INTO Customer (kode, nama, alamat, telepon, email)
        VALUES (?, ?, ?, ?, ?)
        """
        
        if self.db.execute_query(query, data):
            print("Customer berhasil ditambahkan!")
    
    # ===== TRANSAKSI PENJUALAN =====
    def transaksi_penjualan(self):
        print("\n=== TRANSAKSI PENJUALAN ===")
        
        # Tampilkan customer
        customers = self.db.execute_query("SELECT id, kode, nama FROM Customer ORDER BY nama")
        if not customers:
            print("Belum ada data customer!")
            return
        
        print("Daftar Customer:")
        for i, c in enumerate(customers, 1):
            print(f"{i}. {c.kode} - {c.nama}")
        
        try:
            cust_idx = int(input("Pilih customer: ")) - 1
            customer = customers[cust_idx]
        except:
            print("Customer tidak valid!")
            return
        
        # Input items
        items = []
        while True:
            # Tampilkan produk
            products = self.db.execute_query("SELECT id, kode, nama, harga_jual, stok FROM Produk WHERE stok > 0 ORDER BY nama")
            if not products:
                print("Tidak ada produk yang tersedia!")
                return
            
            print("\nDaftar Produk:")
            for i, p in enumerate(products, 1):
                print(f"{i}. {p.kode} - {p.nama} (Stok: {p.stok}) - Rp {p.harga_jual:,.0f}")
            
            try:
                prod_idx = int(input("Pilih produk (0 untuk selesai): ")) - 1
                if prod_idx == -1:
                    break
                    
                produk = products[prod_idx]
                if produk.stok <= 0:
                    print("Stok habis!")
                    continue
                    
                jumlah = int(input("Jumlah: "))
                if jumlah > produk.stok:
                    print(f"Stok tidak cukup! Stok tersedia: {produk.stok}")
                    continue
                
                subtotal = jumlah * produk.harga_jual
                items.append({
                    'produk_id': produk.id,
                    'nama': produk.nama,
                    'jumlah': jumlah,
                    'harga': produk.harga_jual,
                    'subtotal': subtotal
                })
                
                print("Item ditambahkan!")
                
            except:
                print("Input tidak valid!")
        
        if not items:
            print("Tidak ada item yang dibeli!")
            return
        
        # Hitung total
        total = sum(item['subtotal'] for item in items)
        
        # Simpan transaksi ke database
        try:
            # Mulai transaction
            no_transaksi = f"TRX-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
            tanggal = datetime.now()
            
            # Insert ke tabel Penjualan
            query_penjualan = """
            INSERT INTO Penjualan (no_transaksi, tanggal, customer_id, total)
            VALUES (?, ?, ?, ?)
            """
            self.db.execute_query(query_penjualan, (no_transaksi, tanggal, customer.id, total))
            
            # Dapatkan ID penjualan yang baru dibuat
            result = self.db.execute_query("SELECT @@IDENTITY AS id")
            penjualan_id = result[0].id if result else None
            
            # Insert detail penjualan
            for item in items:
                query_detail = """
                INSERT INTO DetailPenjualan (penjualan_id, produk_id, jumlah, harga, subtotal)
                VALUES (?, ?, ?, ?, ?)
                """
                self.db.execute_query(query_detail, (penjualan_id, item['produk_id'], item['jumlah'], item['harga'], item['subtotal']))
                
                # Update stok produk
                query_update_stok = "UPDATE Produk SET stok = stok - ? WHERE id = ?"
                self.db.execute_query(query_update_stok, (item['jumlah'], item['produk_id']))
            
            # Commit transaction
            self.db.connection.commit()
            
            # Cetak struk
            self.cetak_struk(no_transaksi, tanggal, customer.nama, items, total)
            
        except Exception as e:
            self.db.connection.rollback()
            print(f"Error saat menyimpan transaksi: {e}")
    
    def cetak_struk(self, no_transaksi, tanggal, customer, items, total):
        """Mencetak struk penjualan"""
        print("\n" + "=" * 50)
        print("           STRUK PENJUALAN KAOS KAKI")
        print("=" * 50)
        print(f"No. Transaksi : {no_transaksi}")
        print(f"Tanggal       : {tanggal}")
        print(f"Customer      : {customer}")
        print("-" * 50)
        
        for item in items:
            print(f"{item['nama']:<20} x{item['jumlah']:<3} Rp {item['subtotal']:>10,.0f}")
        
        print("-" * 50)
        print(f"TOTAL         : Rp {total:>10,.0f}")
        print("=" * 50)
        print("      Terima kasih atas pembeliannya!")
        print("=" * 50)
    
    # ===== LAPORAN =====
    def laporan_penjualan(self):
        print("\n=== LAPORAN PENJUALAN ===")
        
        query = """
        SELECT p.no_transaksi, p.tanggal, c.nama as customer, p.total
        FROM Penjualan p
        INNER JOIN Customer c ON p.customer_id = c.id
        ORDER BY p.tanggal DESC
        """
        
        penjualan = self.db.execute_query(query)
        
        if not penjualan:
            print("Belum ada transaksi penjualan.")
            return
        
        total_penjualan = 0
        for p in penjualan:
            print(f"{p.no_transaksi} - {p.tanggal}")
            print(f"Customer: {p.customer}")
            print(f"Total: Rp {p.total:,.0f}")
            print("-" * 30)
            total_penjualan += p.total
        
        print(f"\nTOTAL KESELURUHAN: Rp {total_penjualan:,.0f}")
    
    def laporan_stok(self):
        print("\n=== LAPORAN STOK ===")
        
        query = "SELECT kode, nama, stok FROM Produk ORDER BY nama"
        products = self.db.execute_query(query)
        
        if not products:
            print("Tidak ada data produk.")
            return
        
        for p in products:
            status = "HABIS" if p.stok == 0 else "RENDAH" if p.stok < 10 else "AMAN"
            print(f"{p.kode} - {p.nama}: {p.stok} pcs ({status})")
    
    # ===== MENU UTAMA =====
    def main_menu(self):
        while True:
            print("\n=== SISTEM PENJUALAN KAOS KAKI ===")
            print("1. Kelola Produk")
            print("2. Kelola Customer")
            print("3. Transaksi Penjualan")
            print("4. Laporan Penjualan")
            print("5. Laporan Stok")
            print("6. Keluar")
            
            pilihan = input("Pilih menu (1-6): ")
            
            if pilihan == '1':
                self.kelola_produk()
            elif pilihan == '2':
                self.kelola_customer()
            elif pilihan == '3':
                self.transaksi_penjualan()
            elif pilihan == '4':
                self.laporan_penjualan()
            elif pilihan == '5':
                self.laporan_stok()
            elif pilihan == '6':
                print("Terima kasih! Program selesai.")
                self.db.close()
                break
            else:
                print("Pilihan tidak valid!")
    
    def kelola_produk(self):
        while True:
            print("\n=== KELOLA PRODUK ===")
            print("1. Tambah Produk")
            print("2. Lihat Produk")
            print("3. Kembali")
            
            pilihan = input("Pilih menu (1-3): ")
            
            if pilihan == '1':
                self.tambah_produk()
            elif pilihan == '2':
                self.lihat_produk()
            elif pilihan == '3':
                break
            else:
                print("Pilihan tidak valid!")
    
    def kelola_customer(self):
        while True:
            print("\n=== KELOLA CUSTOMER ===")
            print("1. Tambah Customer")
            print("2. Kembali")
            
            pilihan = input("Pilih menu (1-2): ")
            
            if pilihan == '1':
                self.tambah_customer()
            elif pilihan == '2':
                break
            else:
                print("Pilihan tidak valid!")

# Jalankan program
if __name__ == "__main__":
    app = PenjualanKaosKaki()
    app.main_menu()