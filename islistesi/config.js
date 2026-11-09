/* İş listesi bağlantı ayarları.
   "firebase" bölümü Firebase konsolundaki web uygulaması ayarlarıdır; gizli değildir.
   Erişim, Firebase'deki kullanıcı şifreleri ve firestore.rules dosyasındaki kurallarla korunur.
   Şifreler burada DEĞİL, yalnızca Firebase konsolunda tutulur. */
window.ISLISTE_CONFIG = {
  firebase: null, // Firebase'den alınan firebaseConfig buraya gelecek
  users: {
    ibrahim: { name: "İbrahim Kurban", email: "ibrahimkurban@ifhukuk.com" },
    firat:   { name: "Fırat Talha Özdemir", email: "firattalhaozdemir@ifhukuk.com" },
    harun:   { name: "Harun Enes Maden", email: "harunenesmaden@ifhukuk.com" }
  }
};
