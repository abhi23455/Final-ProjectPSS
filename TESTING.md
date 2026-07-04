# TESTING DOCUMENTATION

## Cara Menjalankan Test
Pastikan project sudah berjalan (`docker-compose up -d`).

### 1. Test API Dasar
Jalankan script test manual untuk endpoint utama:
```bash
python test_api.py
```

### 2. Test Benchmark Kecepatan
Menjalankan benchmark untuk melihat manfaat caching Redis:
```bash
docker-compose exec web python benchmark.py
```

### 3. Test Optimasi Query
Menjalankan demo optimasi untuk melihat perbedaan N+1 problem dan solusinya:
```bash
docker-compose exec web python optimization_demo.py
```

---

## Test Case yang Telah Dilengkapi
| No | Test Case | Keterangan | Status |
|----|-----------|------------|--------|
| 1 | Registrasi User Baru | Membuat user baru | ✅ |
| 2 | Login User | Mendapatkan token JWT | ✅ |
| 3 | Auth Me | Mendapatkan informasi user saat ini | ✅ |
| 4 | List Course (Public) | Melihat daftar course tanpa login | ✅ |
| 5 | Enrollment Student | Mendaftarkan student ke course | ✅ |
| 6 | My Courses | Melihat daftar course yang diikuti student | ✅ |
| 7 | Benchmark Kecepatan | Membandingkan kecepatan dengan & tanpa caching | ✅ |
| 8 | Query Optimization | Demo N+1 problem & solusinya | ✅ |
