// script.js
let cart = [];
let modal = null;
let closeBtn = null;

// Fungsi untuk handle API calls dengan authentication check
async function handleApiCall(apiCall) {
    try {
        const isLoggedIn = await checkLoginStatus();
        if (!isLoggedIn) {
            throw new Error('Not authenticated');
        }
        
        const response = await apiCall();
        
        // Handle 403 Forbidden (insufficient permissions)
        if (response.status === 403) {
            const error = await response.json();
            alert(`Error: ${error.error}\nHanya admin yang dapat melakukan aksi ini.`);
            throw new Error('Insufficient permissions');
        }
        
        return response;
    } catch (error) {
        if (error.message === 'Not authenticated') {
            showLoginRequired();
        } else if (error.message === 'Insufficient permissions') {
            // Already handled above
        } else {
            console.error('API call error:', error);
        }
        throw error;
    }
}

// Fungsi untuk cek status login
async function checkLoginStatus() {
    try {
        const response = await fetch('/api/current-user');
        return response.ok;
    } catch (error) {
        return false;
    }
}

// Fungsi untuk menampilkan pesan login required
function showLoginRequired() {
    document.querySelectorAll('.content-section, nav').forEach(el => {
        el.style.display = 'none';
    });
    document.getElementById('login-required-message').style.display = 'block';
    document.getElementById('user-info').style.display = 'none';
}

// Fungsi untuk redirect ke login
function redirectToLogin() {
    window.location.href = '/login';
}

// Fungsi logout
async function logout() {
    try {
        const response = await fetch('/logout');
        if (response.ok) {
            window.location.href = '/login';
        }
    } catch (error) {
        console.error('Logout error:', error);
    }
}

document.addEventListener('DOMContentLoaded', function() {
    // Inisialisasi modal
    modal = document.getElementById('productModal');
    closeBtn = document.querySelector('.close');
    
    // Cek login status saat page load
    checkLoginStatus().then(isLoggedIn => {
        if (!isLoggedIn) {
            showLoginRequired();
            return;
        }
        
        // Load user info
        loadUserInfo();
        
        // Setup navigation hanya jika sudah login
        setupNavigation();
        
        // Load initial data
        loadDashboard();
    });

    // Modal functionality
    if (closeBtn) {
        closeBtn.onclick = function() {
            modal.style.display = 'none';
        }
    }
    
    window.onclick = function(event) {
        if (event.target === modal) {
            modal.style.display = 'none';
        }
    }

    // Product form submission
    const productForm = document.getElementById('product-form');
    if (productForm) {
        productForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const productData = {
                kode: document.getElementById('kode').value,
                nama: document.getElementById('nama').value,
                warna: document.getElementById('warna').value,
                ukuran: document.getElementById('ukuran').value,
                bahan: document.getElementById('bahan').value,
                harga_beli: parseFloat(document.getElementById('harga_beli').value),
                harga_jual: parseFloat(document.getElementById('harga_jual').value),
                stok: parseInt(document.getElementById('stok').value)
            };
            
            try {
                const response = await handleApiCall(() => 
                    fetch('/api/produk', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify(productData)
                    })
                );
                
                if (response.ok) {
                    alert('Produk berhasil ditambahkan!');
                    modal.style.display = 'none';
                    loadProduk();
                    document.getElementById('product-form').reset();
                } else {
                    const error = await response.json();
                    alert('Error: ' + error.error);
                }
            } catch (error) {
                if (error.message !== 'Not authenticated') {
                    alert('Error: ' + error.message);
                }
            }
        });
    }
});

// Panggil fungsi ini setelah login berhasil
async function loadUserInfo() {
    try {
        const response = await fetch('/api/current-user');
        if (response.ok) {
            const user = await response.json();
            document.getElementById('user-name').textContent = user.nama;
            document.getElementById('user-info').style.display = 'flex';
            
            // Update UI berdasarkan role
            await updateUIBasedOnRole();
        }
    } catch (error) {
        console.error('Error loading user info:', error);
    }
}

// Tambahkan fungsi untuk check role dan update UI
async function checkUserRole() {
    try {
        const response = await fetch('/api/user-role');
        if (response.ok) {
            const data = await response.json();
            return data.role;
        }
        return null;
    } catch (error) {
        console.error('Error checking user role:', error);
        return null;
    }
}

// Fungsi untuk update UI berdasarkan role
async function updateUIBasedOnRole() {
    const role = await checkUserRole();
    
    if (role === 'admin') {
        // Admin bisa akses semua
        document.getElementById('nav-produk').style.display = 'block';
        document.getElementById('btn-tambah-produk').style.display = 'block';
    } else if (role === 'kasir') {
        // Kasir hanya bisa lihat penjualan dan laporan
        document.getElementById('nav-produk').style.display = 'none';
        document.getElementById('btn-tambah-produk').style.display = 'none';
        
        // Jika sedang di halaman produk, redirect ke dashboard
        if (window.location.hash === '#produk') {
            window.location.hash = '#dashboard';
            document.getElementById('dashboard').classList.add('active');
            document.getElementById('produk').classList.remove('active');
        }
    }
    
    // Update tampilan role
    if (role) {
        document.getElementById('user-role').textContent = role;
    }
}

// Setup navigation
function setupNavigation() {
    const navButtons = document.querySelectorAll('.nav-btn');
    const contentSections = document.querySelectorAll('.content-section');
    
    navButtons.forEach(button => {
        button.addEventListener('click', async () => {
            const isLoggedIn = await checkLoginStatus();
            if (!isLoggedIn) {
                showLoginRequired();
                return;
            }
            
            const target = button.dataset.target;
            const role = await checkUserRole();
            
            // Blokir akses untuk kasir ke halaman produk
            if (role === 'kasir' && target === 'produk') {
                alert('Akses ditolak. Hanya admin yang dapat mengelola produk.');
                return;
            }
            
            // Update active button
            navButtons.forEach(btn => btn.classList.remove('active'));
            button.classList.add('active');
            
            // Show target section
            contentSections.forEach(section => section.classList.remove('active'));
            document.getElementById(target).classList.add('active');
            
            // Load data for the section
            if (target === 'produk') loadProduk();
            if (target === 'penjualan') loadProductsForSale();
            if (target === 'laporan') loadLaporan();
            if (target === 'dashboard') loadDashboard();
        });
    });
}

// Auto-generate kode produk saat modal dibuka
window.showAddProductModal = async function() {
    const role = await checkUserRole();
    if (role !== 'admin') {
        alert('Hanya admin yang dapat menambah produk.');
        return;
    }
    
    const isLoggedIn = await checkLoginStatus();
    if (!isLoggedIn) {
        showLoginRequired();
        return;
    }
    
    try {
        const response = await handleApiCall(() => 
            fetch('/api/generate-kode-produk')
        );
        
        const data = await response.json();
        document.getElementById('kode').value = data.kode;
        document.getElementById('kode').readOnly = true;
    } catch (error) {
        console.error('Error generating product code:', error);
        document.getElementById('kode').value = 'KK0001';
    }
    
    if (modal) {
        modal.style.display = 'block';
    }
}

async function loadProduk() {
    try {
        const response = await handleApiCall(() => 
            fetch('/api/produk')
        );
        
        const produk = await response.json();
        
        const tbody = document.querySelector('#produk-table tbody');
        if (tbody) {
            tbody.innerHTML = '';
            
            produk.forEach(p => {
                const row = document.createElement('tr');
                row.innerHTML = `
                    <td>${p.kode}</td>
                    <td>${p.nama}</td>
                    <td>${p.warna}</td>
                    <td>${p.ukuran}</td>
                    <td>Rp ${p.harga_jual.toLocaleString()}</td>
                    <td>${p.stok}</td>
                    <td>
                        <button class="btn-danger" onclick="deleteProduct(${p.id})">
                            <i class="fas fa-trash"></i>
                        </button>
                    </td>
                `;
                tbody.appendChild(row);
            });
        }
    } catch (error) {
        if (error.message !== 'Not authenticated') {
            console.error('Error loading products:', error);
        }
    }
}

async function loadProductsForSale() {
    try {
        const response = await handleApiCall(() => 
            fetch('/api/produk')
        );
        
        const produk = await response.json();
        
        const select = document.getElementById('product-select');
        if (select) {
            select.innerHTML = '<option value="">-- Pilih Produk --</option>';
            
            produk.filter(p => p.stok > 0).forEach(p => {
                const option = document.createElement('option');
                option.value = p.id;
                option.textContent = `${p.nama} - Rp ${p.harga_jual.toLocaleString()} (Stok: ${p.stok})`;
                option.dataset.price = p.harga_jual;
                select.appendChild(option);
            });
        }
    } catch (error) {
        if (error.message !== 'Not authenticated') {
            console.error('Error loading products for sale:', error);
        }
    }
}

function addToCart() {
    const select = document.getElementById('product-select');
    const qtyInput = document.getElementById('product-qty');
    
    if (!select || !select.value || !qtyInput || !qtyInput.value) {
        alert('Pilih produk dan masukkan jumlah!');
        return;
    }
    
    const productId = select.value;
    const productName = select.options[select.selectedIndex].text.split(' - ')[0];
    const price = parseFloat(select.options[select.selectedIndex].dataset.price);
    const quantity = parseInt(qtyInput.value);
    
    // Check if product already in cart
    const existingItem = cart.find(item => item.produk_id == productId);
    if (existingItem) {
        existingItem.jumlah += quantity;
        existingItem.subtotal = existingItem.jumlah * existingItem.harga;
    } else {
        cart.push({
            produk_id: productId,
            nama: productName,
            harga: price,
            jumlah: quantity,
            subtotal: price * quantity
        });
    }
    
    updateCartDisplay();
    qtyInput.value = '';
}

function updateCartDisplay() {
    const tbody = document.querySelector('#cart-table tbody');
    const totalElement = document.getElementById('cart-total');
    
    if (tbody && totalElement) {
        tbody.innerHTML = '';
        let total = 0;
        
        cart.forEach((item, index) => {
            total += item.subtotal;
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${item.nama}</td>
                <td>Rp ${item.harga.toLocaleString()}</td>
                <td>${item.jumlah}</td>
                <td>Rp ${item.subtotal.toLocaleString()}</td>
                <td>
                    <button class="btn-danger" onclick="removeFromCart(${index})">
                        <i class="fas fa-trash"></i>
                    </button>
                </td>
            `;
            tbody.appendChild(row);
        });
        
        totalElement.textContent = `Rp ${total.toLocaleString()}`;
    }
}

function removeFromCart(index) {
    cart.splice(index, 1);
    updateCartDisplay();
}

async function processPayment() {
    if (cart.length === 0) {
        alert('Keranjang belanja kosong!');
        return;
    }
    
    const total = cart.reduce((sum, item) => sum + item.subtotal, 0);
    
    try {
        const response = await handleApiCall(() => 
            fetch('/api/penjualan', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    customer_id: 1, // Default customer
                    total: total,
                    items: cart
                })
            })
        );
        
        if (response.ok) {
            const result = await response.json();
            alert(`Transaksi berhasil! No. Transaksi: ${result.no_transaksi}`);
            cart = [];
            updateCartDisplay();
            loadProductsForSale();
        } else {
            const error = await response.json();
            alert('Error: ' + error.error);
        }
    } catch (error) {
        if (error.message !== 'Not authenticated') {
            alert('Error: ' + error.message);
        }
    }
}

async function loadLaporan() {
    try {
        const response = await handleApiCall(() => 
            fetch('/api/penjualan')
        );
        
        const penjualan = await response.json();
        
        const tbody = document.querySelector('#laporan-table tbody');
        if (tbody) {
            tbody.innerHTML = '';
            
            penjualan.forEach(p => {
                const row = document.createElement('tr');
                row.innerHTML = `
                    <td>${p.no_transaksi}</td>
                    <td>${new Date(p.tanggal).toLocaleDateString()}</td>
                    <td>${p.customer}</td>
                    <td>Rp ${p.total.toLocaleString()}</td>
                `;
                tbody.appendChild(row);
            });
        }
    } catch (error) {
        if (error.message !== 'Not authenticated') {
            console.error('Error loading reports:', error);
        }
    }
}

async function loadDashboard() {
    try {
        const [produkResponse, penjualanResponse] = await Promise.all([
            handleApiCall(() => fetch('/api/produk')),
            handleApiCall(() => fetch('/api/penjualan'))
        ]);
        
        const produk = await produkResponse.json();
        const penjualan = await penjualanResponse.json();
        
        const today = new Date().toLocaleDateString();
        const penjualanHariIni = penjualan.filter(p => 
            new Date(p.tanggal).toLocaleDateString() === today
        );
        
        const totalPendapatan = penjualan.reduce((sum, p) => sum + p.total, 0);
        
        if (document.getElementById('total-produk')) {
            document.getElementById('total-produk').textContent = produk.length;
        }
        if (document.getElementById('penjualan-hari-ini')) {
            document.getElementById('penjualan-hari-ini').textContent = penjualanHariIni.length;
        }
        if (document.getElementById('total-pendapatan')) {
            document.getElementById('total-pendapatan').textContent = 
                `Rp ${totalPendapatan.toLocaleString()}`;
        }
    } catch (error) {
        if (error.message !== 'Not authenticated') {
            console.error('Error loading dashboard:', error);
        }
    }
}

// Fungsi delete product
async function deleteProduct(productId) {
    const role = await checkUserRole();
    if (role !== 'admin') {
        alert('Hanya admin yang dapat menghapus produk.');
        return;
    }
    
    if (!confirm('Apakah Anda yakin ingin menghapus produk ini?')) {
        return;
    }
    
    try {
        const response = await handleApiCall(() => 
            fetch(`/api/produk/${productId}`, {
                method: 'DELETE'
            })
        );
        
        if (response.ok) {
            alert('Produk berhasil dihapus!');
            loadProduk();
        } else {
            const error = await response.json();
            alert('Error: ' + error.error);
        }
    } catch (error) {
        if (error.message !== 'Not authenticated' && error.message !== 'Insufficient permissions') {
            alert('Error: ' + error.message);
        }
    }
}