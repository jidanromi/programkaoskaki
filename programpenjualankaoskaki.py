# program_penjualan_kaos_kaki.py
import json
import os
from datetime import datetime

# File penyimpanan data
FILE_PRODUK = "data_produk.json"
FILE_CUSTOMER = "data_customer.json"
FILE_SUPPLIER = "data_supplier.json"
FILE_PENJUALAN = "data_penjualan.json"
FILE_PEMBELIAN = "data_pembelian.json"

def muat_data(nama_file):
    """Memuat data dari file JSON"""
    if os.path.exists(nama_file):
        with open(nama_file, 'r') as file:
            return json.load(file)
    return []

def simpan_data(nama_file, data):
    """Menyimpan data ke file JSON"""
    with open(nama_file, 'w') as file:
        json.dump(data, file, indent=4)

# ===== MASTER PRODUK =====
def kelola_produk():
    """Menu kelola data produk"""
    while True:
        print("\n=== KELOLA PRODUK KAOS KAKI ===")
        print("1. Tambah Produk")
        print("2. Lihat Produk")
        print("3. Edit Produk")
        print("4. Hapus Produk")
        print("5. Kembali")
        
        pilihan = input("Pilih menu (1-5): ")
        produk = muat_data(FILE_PRODUK)
        
        if pilihan == '1':
            tambah_produk(produk)
        elif pilihan == '2':
            lihat_produk(produk)
        elif pilihan == '3':
            edit_produk(produk)
        elif pilihan == '4':
            hapus_produk(produk)
        elif pilihan == '5':
            break
        else:
            print("Pilihan tidak valid!")

def tambah_produk(produk):
    """Menambah produk baru"""
    print("\n=== TAMBAH PRODUK ===")
    
    kode = input("Kode produk: ")
    # Cek jika kode sudah ada
    for p in produk:
        if p['kode'] == kode:
            print("Kode produk sudah ada!")
            return
    
    data = {
        'kode': kode,
        'nama': input("Nama produk: "),
        'warna': input("Warna: "),
        'ukuran': input("Ukuran: "),
        'bahan': input("Bahan: "),
        'harga_beli': float(input("Harga beli: ")),
        'harga_jual': float(input("Harga jual: ")),
        'stok': int(input("Stok awal: "))
    }
    
    produk.append(data)
    simpan_data(FILE_PRODUK, produk)
    print("Produk berhasil ditambahkan!")

def lihat_produk(produk):
    """Menampilkan semua produk"""
    print("\n=== DAFTAR PRODUK ===")
    if not produk:
        print("Tidak ada data produk.")
        return
    
    for i, p in enumerate(produk, 1):
        print(f"{i}. {p['kode']} - {p['nama']}")
        print(f"   Warna: {p['warna']}, Ukuran: {p['ukuran']}")
        print(f"   Harga: Rp {p['harga_jual']:,.0f}, Stok: {p['stok']}")
        print("-" * 40)

# ===== TRANSAKSI PENJUALAN =====
def transaksi_penjualan():
    """Menu transaksi penjualan"""
    produk_list = muat_data(FILE_PRODUK)
    customer_list = muat_data(FILE_CUSTOMER)
    penjualan_list = muat_data(FILE_PENJUALAN)
    
    print("\n=== TRANSAKSI PENJUALAN ===")
    
    # Pilih customer
    print("Customer:")
    for i, c in enumerate(customer_list, 1):
        print(f"{i}. {c['nama']}")
    
    try:
        cust_idx = int(input("Pilih customer: ")) - 1
        customer = customer_list[cust_idx]
    except:
        print("Customer tidak valid!")
        return
    
    # Input items
    items = []
    while True:
        print("\nDaftar Produk:")
        lihat_produk(produk_list)
        
        try:
            prod_idx = int(input("Pilih produk (0 untuk selesai): ")) - 1
            if prod_idx == -1:
                break
                
            produk = produk_list[prod_idx]
            if produk['stok'] <= 0:
                print("Stok habis!")
                continue
                
            jumlah = int(input("Jumlah: "))
            if jumlah > produk['stok']:
                print(f"Stok tidak cukup! Stok tersedia: {produk['stok']}")
                continue
                
            # Kurangi stok
            produk['stok'] -= jumlah
            items.append({
                'kode_produk': produk['kode'],
                'nama_produk': produk['nama'],
                'jumlah': jumlah,
                'harga': produk['harga_jual'],
                'subtotal': jumlah * produk['harga_jual']
            })
            
            print("Item ditambahkan!")
            
        except:
            print("Input tidak valid!")
    
    if not items:
        print("Tidak ada item yang dibeli!")
        return
    
    # Simpan transaksi
    transaksi = {
        'no_transaksi': f"TRX-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
        'tanggal': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'customer': customer['nama'],
        'items': items,
        'total': sum(item['subtotal'] for item in items)
    }
    
    penjualan_list.append(transaksi)
    simpan_data(FILE_PENJUALAN, penjualan_list)
    simpan_data(FILE_PRODUK, produk_list)  # Update stok
    
    # Cetak struk
    print("\n=== STRUK PENJUALAN ===")
    print(f"No. Transaksi: {transaksi['no_transaksi']}")
    print(f"Tanggal: {transaksi['tanggal']}")
    print(f"Customer: {transaksi['customer']}")
    print("-" * 40)
    for item in items:
        print(f"{item['nama_produk']} x{item['jumlah']}: Rp {item['subtotal']:,.0f}")
    print("-" * 40)
    print(f"TOTAL: Rp {transaksi['total']:,.0f}")
    print("Terima kasih telah berbelanja!")

# ===== LAPORAN =====
def laporan_penjualan():
    """Menampilkan laporan penjualan"""
    penjualan = muat_data(FILE_PENJUALAN)
    
    print("\n=== LAPORAN PENJUALAN ===")
    if not penjualan:
        print("Belum ada transaksi penjualan.")
        return
    
    total_penjualan = 0
    for p in penjualan:
        print(f"{p['no_transaksi']} - {p['tanggal']}")
        print(f"Customer: {p['customer']}")
        print(f"Total: Rp {p['total']:,.0f}")
        print("-" * 30)
        total_penjualan += p['total']
    
    print(f"\nTOTAL KESELURUHAN: Rp {total_penjualan:,.0f}")

def laporan_stok():
    """Menampilkan laporan stok"""
    produk = muat_data(FILE_PRODUK)
    
    print("\n=== LAPORAN STOK ===")
    if not produk:
        print("Tidak ada data produk.")
        return
    
    for p in produk:
        status = "HABIS" if p['stok'] == 0 else "RENDAH" if p['stok'] < 10 else "AMAN"
        print(f"{p['kode']} - {p['nama']}: {p['stok']} pcs ({status})")

# ===== MENU UTAMA =====
def main():
    """Menu utama program"""
    # Inisialisasi file data jika belum ada
    for file in [FILE_PRODUK, FILE_CUSTOMER, FILE_SUPPLIER, FILE_PENJUALAN, FILE_PEMBELIAN]:
        if not os.path.exists(file):
            simpan_data(file, [])
    
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
            kelola_produk()
        elif pilihan == '2':
            print("Fitur kelola customer sedang dikembangkan...")
        elif pilihan == '3':
            transaksi_penjualan()
        elif pilihan == '4':
            laporan_penjualan()
        elif pilihan == '5':
            laporan_stok()
        elif pilihan == '6':
            print("Terima kasih! Program selesai.")
            break
        else:
            print("Pilihan tidak valid!")

if __name__ == "__main__":
    main()