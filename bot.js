// 1. VARIABLE & TIPE DATA
const namaBot = "TI-Helper Bot"; // String
const versi = 1.0;               // Float
let totalCommandDijalankan = 0;   // Integer
const isActive = true;           // Boolean

// 2. OBJECT (Data Server)
const serverConfig = {
    namaServer: "Mahasiswa TI Server",
    maxMember: 100,
    prefix: "!"
};

// 3. ARRAY (Daftar Kata Terlarang)
const kataKasar = ["jelek", "bodoh", "cupu"];

// 4. FUNCTION (Fungsi untuk Mengecek Kata Kasar)
function celatKataKasar(pesan) {
    // LOOPING (Mengecek isi Array satu per satu)
    for (let i = 0; i < kataKasar.length; i++) {
        // IF-ELSE (Kondisi percabangan)
        if (pesan.includes(kataKasar[i])) {
            return true; // Ditemukan kata kasar!
        }
    }
    return false; // Aman
}

// 5. FUNCTION MAIN (Simulasi Event Pesan Masuk di Discord)
function saatAdaPesanMasuk(userObject, isiPesan) {
    console.log(`[LOG] Pesan dari ${userObject.nama}: "${isiPesan}"`);
    
    // Cek kata kasar menggunakan Function yang kita buat
    if (celatKataKasar(isiPesan)) {
        return `⚠️ Peringatan untuk ${userObject.nama}! Harap menjaga ketikan Anda.`;
    }

    // Simulasi Perintah / Command Bot
    if (isiPesan === "!info") {
        totalCommandDijalankan++;
        // Mengambil data dari Object menggunakan tanda titik (.)
        return `Bot: ${namaBot} (v${versi}) | Server: ${serverConfig.namaServer}`;
    } 
    else if (isiPesan === "!spam-belajar") {
        totalCommandDijalankan++;
        // LOOPING (Spam motivasi 3 kali)
        for (let i = 0; i < 3; i++) {
            console.log(`Semangat Ngoding ke-${i + 1}! 🚀`);
        }
        return "Berhasil mengirim motivasi!";
    }
    else {
        return "Pesan diterima.";
    }
}

// ==========================================
// SIMULASI JALANNYA BOT
// ==========================================

// Data User dalam bentuk OBJECT
const user1 = { nama: "Budi", level: 5 };
const user2 = { nama: "Andi", level: 1 };

// Uji Coba 1: User mengirim pesan biasa
console.log(saatAdaPesanMasuk(user1, "!info"));

// Uji Coba 2: User melanggar aturan kata kasar
console.log(saatAdaPesanMasuk(user2, "Dasar kau bodoh"));