# Chilling-Amano - Self Hosting bot discord untuk memutar dari youtube

## Awalan

Pengen dengerin lagu selama mabar pake link dari youtube, tapi bot lain pada engga bisa karena kena "surat cinta" dari Google? Jalanin aja botnya di local machine kamu. **Chilling Amano** Self Hosting Discord Bot untuk memutar audio dari link youtube. Mau coba bot nya dulu sebelum download? [Join Discord](https://dc.lmcpsite.my.id) untuk testing dan melihat projek lain ku^ ~~kalo males setting dan mau pake bot nya dan mabar diserver ini pun boleh~~👀️

## Commands:

* `.play {youtube.links atau cari}` - Memutar atau memasukan antrian lagu.
  * alias `.p`
* `.skip` - Skip lagu. `.skip all` untuk menghapus semua antrian lagu
  * alias `.s`
* `.loop` - Toggle putar lagu yang sedang diputar terus menerus
  * alias `.l`
* `.radio` - Toggle untuk memainkan radio J-POP 7/24 jam secara random
  * alias `.r`
* `.help` - Memunculkan quick help guide commands
  * alias `.h`

## Memulai menjalankan bot di komputermu sendiri

Pertama tama, kamu perlu komputer / device yang bisa menjalankan bot ini dan mendukung python serta library yang dibutuhkan. bisa di Local Home Server, AWS / VPS, atau bahkan PC kamu sendiri pun bisa. setelah bot berhasil berjalan bisa langsung digunakan, tidak perlu untuk mengatur jaringan IP dsb.

### Step pertama: Buat bot kosongan discord

1. Buka [Discord Developer Portal](https://discord.com/developers/applications), Login menggunakan akun discord mu.
2. Buat aplikasi baru dengan klik "New Application".
3. Kasih nama apapun bebas, ini baru nama aplikasi bukan nama botnya.
4. Setelah dibuat, atur sesukamu untuk general information bot kamu
5. Di sisi kiri ada tab "Bot". Disini kamu isi nama botnya. ini akan tampil di profile bot. dibagian Token, klik "reset token" untuk mendapatkan kode rahasia bot. simpan untuk nanti, dan JANGAN DIBERIKAN KE SIAPAPUN TOKEN INI.
6. Scroll kebawah, dan aktifkan "Server Members Intent" dan "Message Content Intent". Semua selesai, klik "Save" untuk menyimpan.

### Step kedua: Masukkin bot ke server

1. Masih di Discord Developer Portal, di sisi kiri klik tab "OAuth2".
2. Scroll kebawah dan ada "OAuth2 URL Generator". Pilih kotak "bot", kemudian muncul opsi "bot permission", pilih "administrator". Jangan khawatir karena Administrator ini. Permission ini dibutuhkan hanya agar bot bisa join ke private voice channel, kalau user yang request ada di channel tersebut.
3. Dibawah akan muncul URL yang sudah digenerate. Copy link tersebut dan buka di browser. Kemudian, pilih server yang ingin bot dimasukkan.

### Step ketiga: Nyalain bot biar berfungsi

1. Download source code Chilling-Amano ini dengan `git clone` atau metode apaun yang kamu prefer.
2. Pastikan python terinstall di machine kamu, versi 3.9 keatas.

---



#### Untuk OS Linux/Unix semacamnya

1. Di folder Chilling-Amano, Buka terminal dan buat virtual environtment dengan menulis:
   `python3 -m venv venv`
2. Kemudian aktivasi venv dengan menulis:
   `source venv/bin/activate`
3. Download library yang dibutuhkan dengan menulis:
   `pip install -r Requirements.txt`
4. Bolehkan skrip start.sh untuk dijalankan dengan menulis:
   `chmod +x start.sh`

#### Untuk OS Windows

1. Di folder Chilling-Amano, Buka cmd dan buat virtual environtment dengan menulis:
   `python -m venv venv`
2. Kemudian aktivasi venv dengan menulis:
   `venv\Scripts\activate.bat`
3. Download library yang dibutuhkan dengan menulis:
   `pip install -r Requirements.txt`

---



3. Tutup Terminal / CMD. Masih di folder yang sama, copy dan paste file ".example_env" dan rename menjadi ".env"
4. buka file ini dengan notepad / text editor, dan masukkan bot token yang tadi disimpan ke BOT_TOKEN di .env
5. Jalankan bot dengan klik start.sh untuk os linux, dan start.bat untuk os windows.
6. Terminal / CMD akan terbuka, menampilkan status bot kamu. perlu diingat, kamu harus biarkan terminal ini terbuka. jika kamu tutup maka bot akan langsung offline.

Selamat! Bot sudah online, dan bisa langsung digunakan. tinggal masuk ke voice channel, dan jalankan commands di text channel server discord kamu 😄
