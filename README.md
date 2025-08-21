Tentu, berikut adalah panduan langkah demi langkah untuk menggunakan aplikasi Streamlit yang Anda buat.

---

### **Panduan Penggunaan Aplikasi Profiling Dosen**

Aplikasi ini dirancang untuk membantu Anda memprofiling dosen berdasarkan data penelitian dari berbagai sumber ilmiah, yaitu **Google Scholar**, **SINTA**, dan **Scopus**. Aplikasi ini juga akan memberikan rekomendasi mata kuliah yang sesuai dengan kompetensi dosen.

Berikut adalah langkah-langkah untuk menggunakannya:

#### **1. Buka Aplikasi di Browser**

Setelah Anda menjalankan skrip Python (`streamlit run app.py`) di terminal, aplikasi akan terbuka secara otomatis di peramban web Anda.

#### **2. Masukkan Informasi Dosen**

Di bagian atas halaman, Anda akan menemukan beberapa kolom isian:
* **Masukkan URL Google Scholar:** Ini adalah kolom wajib. Anda harus memasukkan URL profil Google Scholar dari dosen yang ingin Anda teliti. Pastikan URL-nya lengkap dan benar, seperti `https://scholar.google.com/citations?hl=id&user=fzCJZDAAAAAJ`.
* **Masukkan Sinta ID (opsional):** Jika Anda memiliki SINTA ID dosen tersebut, Anda bisa memasukkannya di sini. Aplikasi akan menampilkan tautan langsung ke profil SINTA.
* **Masukkan Scopus ID (opsional):** Jika Anda memiliki Scopus ID dosen, masukkan di sini. Aplikasi akan mencoba mengambil data dari API Scopus jika Anda telah menyiapkan kunci API di file `.env`.

#### **3. Pilih Program Studi**

Di bagian **Pilih Program Studi**, Anda harus memilih program studi yang relevan (**Teknik Informatika**, **Sistem Informasi**, atau **Magister**). Pilihan ini akan menentukan daftar mata kuliah yang akan digunakan untuk pemetaan kompetensi.

#### **4. Proses Profiling**

Setelah semua data dimasukkan, klik tombol **"🔍 Proses Profiling"**.

Aplikasi akan melakukan langkah-langkah berikut:
1.  Mengambil data profil, publikasi, dan minat penelitian dari Google Scholar.
2.  Menggunakan algoritma **Cosine Similarity** untuk membandingkan teks dari profil dosen dengan daftar mata kuliah yang telah Anda tentukan. 
3.  Menghitung skor kesesuaian untuk setiap mata kuliah.

#### **5. Lihat Hasil Profiling**

Setelah proses selesai, Anda akan melihat beberapa hasil yang ditampilkan di halaman:
* **Informasi Dosen:** Nama, afiliasi, h-index, dan i10-index dari Google Scholar.
* **Tautan SINTA:** Jika SINTA ID dimasukkan, sebuah tautan ke profil SINTA akan ditampilkan.
* **Pemetaan Kompetensi:** Sebuah tabel akan muncul yang menampilkan daftar mata kuliah yang relevan, diurutkan berdasarkan persentase kesesuaian. Semakin tinggi persentasenya, semakin cocok mata kuliah tersebut dengan kompetensi dosen.

#### **6. Unduh Laporan PDF**

Di bagian bawah hasil, Anda akan menemukan tombol **"⬇️ Download PDF"**. Klik tombol ini untuk mengunduh laporan ringkas dalam format PDF yang berisi informasi profil dosen dan tabel pemetaan kompetensi. Laporan ini bisa berguna untuk dokumentasi atau presentasi.