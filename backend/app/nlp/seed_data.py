"""
Kategori bazlı örnek sorular ve FAQ şablonları.

Yeni kategori eklemek için:
1. CATEGORY_EXAMPLES sözlüğüne yeni anahtar ve örnek sorular ekleyin.
2. FAQ_TEMPLATES sözlüğüne aynı anahtarla bir şablon cevap ekleyin.
3. Uygulamayı yeniden başlatın – sınıflandırıcı otomatik olarak güncellenecektir.
"""

from __future__ import annotations

# ── Kategori bazlı örnek sorular ──────────────────────────────────────
CATEGORY_EXAMPLES: dict[str, list[str]] = {
    "Akademik": [
        "Ders kaydı nasıl yapılır?",
        "Transkript belgesini nereden alabilirim?",
        "Ders ekleme bırakma tarihleri ne zaman?",
        "Not ortalaması nasıl hesaplanır?",
        "Staj başvurusu nasıl yapılır?",
        "Mezuniyet için kaç kredi gerekiyor?",
        "Danışman hocamla nasıl görüşebilirim?",
        "Yatay geçiş başvurusu nasıl yapılır?",
        "Ders programı ne zaman açıklanacak?",
        "Devamsızlık sınırı kaç hafta?",
        "Bütünleme sınavına nasıl girerim?",
        "Çift anadal programına nasıl başvurabilirim?",
        "Yaz okulu başvuruları ne zaman?",
        "Derse geç kayıt yapabilir miyim?",
        "Muafiyet sınavı ne zaman yapılacak?",
        "Ders seçimi yaparken kontenjan doluysa ne yapmalıyım?",
        "Akademik takvimi nereden görebilirim?",
        "Final sınav programı açıklandı mı?",
        "Tez teslim tarihi ne zaman?",
        "Lisansüstü başvuru şartları nelerdir?",
    ],
    "Teknik": [
        "Öğrenci bilgi sistemi açılmıyor",
        "Şifremi unuttum nasıl sıfırlarım?",
        "E-posta hesabıma giriş yapamıyorum",
        "Wi-Fi'ye bağlanamıyorum",
        "Online sınav sistemi çalışmıyor",
        "Öğrenci portalı hata veriyor",
        "Ders videoları yüklenmiyor",
        "Sisteme giriş yaparken hata alıyorum",
        "Parola değiştirme nasıl yapılır?",
        "Kampüs internet bağlantısı yavaş",
        "Uzaktan eğitim platformuna giremiyorum",
        "Zoom toplantısına bağlanamıyorum",
        "Ödev yükleme sistemi hata veriyor",
        "Mail kutum dolu, nasıl temizlerim?",
        "VPN nasıl kurabilirim?",
        "Dijital kütüphaneye nasıl erişirim?",
        "Bilgisayar laboratuvarı saatleri nelerdir?",
        "Yazıcıdan çıktı alamıyorum",
        "Öğrenci bilgi sistemi şifresi nasıl alınır?",
        "İki faktörlü doğrulama nasıl aktifleştirilir?",
    ],
    "Ödeme": [
        "Harç ücretini nasıl ödeyebilirim?",
        "Burs başvurusu nasıl yapılır?",
        "Öğrenim kredisi başvurusu nereye yapılır?",
        "Harç iadesi alabilir miyim?",
        "Taksit seçenekleri var mı?",
        "Ödeme makbuzu nasıl alınır?",
        "KYK bursu ne zaman yatacak?",
        "Yurt ücreti ne kadar?",
        "Banka hesap numarası değişikliği nasıl yapılır?",
        "Yemek kartı ücreti ne kadar?",
        "Öğrenim ücretinde indirim var mı?",
        "Katkı payı son ödeme tarihi ne zaman?",
        "Ödemeyi geç yaptım, ceza uygulanır mı?",
        "İkinci öğretim ücreti ne kadar?",
        "Burs sonuçları ne zaman açıklanacak?",
        "Yemek kartına nasıl para yüklerim?",
        "Mali yardım başvurusu yapabilir miyim?",
        "Harç borcu olan öğrenci sınava girebilir mi?",
        "Ödeme dekontunu nereye göndermeliyim?",
        "Kredi kartıyla ödeme yapılıyor mu?",
    ],
    "İşletmede Mesleki Eğitim": [
        "İşletmede mesleki eğitim nedir?",
        "İşletmede mesleki eğitim staj mı?",
        "İşyeri uygulama eğitimi staj mıdır?",
        "Bu program staj mı?",
        "Staj mı bu?",
        "İşletmede eğitim stajdan farkı nedir?",
        "Devamsızlık sınırı nedir?",
        "Devamsızlık yaparsam ne olur?",
        "Kaç gün devamsızlık yapabilirim?",
        "Devam zorunluluğu var mı?",
        "Puantaj formu ne zaman teslim edilir?",
        "Puantaj nasıl doldurulur?",
        "Puantaj ne zaman yapılır?",
        "Ara rapor ne zaman teslim edilir?",
        "Ara rapor nasıl yazılır?",
        "Uygulama raporu ne zaman teslim edilir?",
        "Uygulama raporu nasıl hazırlanır?",
        "İşletmede eğitim ne kadar sürer?",
        "İşletme eğitiminde not nasıl verilir?",
        "İşletme danışmanı kim?",
        "Koordinatör hoca kimdir?",
        "İşletme eğitiminde sigorta var mı?",
        "Haftalık çalışma saati kaç?",
        "İşyeri eğitimi başarısızlık durumunda ne olur?",
        "Mesleki eğitim dersi zorunlu mu?",
    ],
    "Diğer": [
        "Öğrenci belgesi nasıl alınır?",
        "Yurt başvurusu nasıl yapılır?",
        "Kampüs ulaşım saatleri nelerdir?",
        "Spor tesisleri ne zaman açık?",
        "Öğrenci kulüplerine nasıl üye olurum?",
        "Psikolojik danışmanlık hizmeti var mı?",
        "Sağlık merkezi nerede?",
        "Erasmus başvurusu nasıl yapılır?",
        "Yemekhane menüsü nerede yayınlanıyor?",
        "Kütüphane çalışma saatleri nelerdir?",
        "Kayıp eşya bürosu nerede?",
        "Kimlik kartımı kaybettim ne yapmalıyım?",
        "Askerlik tecil işlemi nasıl yapılır?",
        "Öğrenci toplu taşıma indirimi nasıl alınır?",
        "Kariyer merkezi randevusu nasıl alınır?",
        "Engelli öğrenci hizmetleri nelerdir?",
        "Yabancı öğrenci ofisi nerede?",
        "Kampüs haritasını nereden bulabilirim?",
        "Okul etkinlikleri takvimi var mı?",
        "Genel bir sorum var, kiminle görüşmeliyim?",
    ],
}

# ── Kategori bazlı FAQ cevap şablonları ───────────────────────────────
FAQ_TEMPLATES: dict[str, str] = {
    "Akademik": (
        "📚 Akademik konularda yardımcı olabilirim!\n\n"
        "Ders kayıtları, transkript, devamsızlık ve sınavlarla ilgili işlemler "
        "için Öğrenci İşleri Daire Başkanlığı'nın web sitesini ziyaret edebilir "
        "veya danışman hocanızla iletişime geçebilirsiniz.\n\n"
       
    ),
    "Teknik": (
        "🔧 Teknik sorunlarda yardımcı olabilirim!\n\n"
        "Şifre sıfırlama, sistem erişimi ve bağlantı sorunları için "
        "Bilgi İşlem Daire Başkanlığı'na başvurabilirsiniz.\n\n"
       
    ),
    "Ödeme": (
        "💰 Ödeme ve burs konularında bilgi:\n\n"
        "Harç ödemeleri banka şubeleri veya online bankacılık üzerinden yapılabilir. "
        "Burs başvuruları için Burs Ofisi'ne, KYK kredisi için e-Devlet üzerinden "
        "başvuru yapabilirsiniz.\n\n"
        
    ),
    "İşletmede Mesleki Eğitim": (
        "🏢 İşletmede Mesleki Eğitim hakkında bilgi:\n\n"
        "Bu program son dönemde alınan zorunlu bir derstir (staj değildir). "
        "Haftanın 5 günü işletmede çalışılır, %90 devam zorunluluğu vardır.\n\n"
        "• Puantaj formu: Her ayın 1-7'si arasında önceki ay için teslim edilir.\n"
        "• Ara rapor: Eğitim süresinin ortasında teslim edilir.\n"
        "• Uygulama raporu: Eğitim sonunda teslim edilir.\n"
        "• Ardışık 3 gün mazeretsiz devamsızlık → başarısız sayılma.\n\n"
        "Detaylı bilgi için koordinatör hocanıza danışınız.\n\n"
        "Kaynak: İşletmede Mesleki Eğitim sunumu"
    ),
    "Diğer": (
        "ℹ️ Genel bilgiler:\n\n"
        "Öğrenci belgesi, yurt başvurusu, kulüpler ve kampüs hizmetleri "
        "hakkında detaylı bilgiye üniversite web sitesinden ulaşabilirsiniz.\n\n"
        
    ),
}
