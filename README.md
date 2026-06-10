# Nanar Kültürdeki Sinema Filmlerini Değerlendirme Sitesi

**Bursa Uludağ Üniversitesi - Bilgisayar Mühendisliği Bölümü**
**Python Programlamaya Giriş Projesi**

**Proje Ekibi:**

* Eren BOZACI (032490035)
* Emine TABAN (032490060)
* Batuhan ÖZDEMİR (032490064)

### [Drive Linki](https://drive.google.com/drive/folders/1mZD5N3nDHRiEa-_DUv3_SHZlrnPHnPi_?usp=sharing)

## Proje Özeti

Nanar Kültürdeki Sinema Filmlerini Değerlendirme Sitesi, kullanıcıların filmler hakkında yorum yapabildiği ve puan verebildiği interaktif bir web platformudur. Projenin yenilikçi yönü, Doğal Dil İşleme (NLP) algoritmaları ve dbmdz/bert-base-turkish-cased dönüştürücü (transformer) mimarisi kullanarak geliştirilen Yapay Zeka destekli Akıllı Filtreleme sistemidir. Sistem, nefret söylemi ve argo ifadeleri tespit edip gizlemek yerine, cümlenin bağlamına uygun pozitif kelimelerle dinamik olarak değiştirerek güvenli bir deneyim sunar.

## Motivasyon ve Gerçek Hayat Problemi

Sosyal medya ve açık platformlardaki anonimlik, siber zorbalığı artırmaktadır. Mevcut sistemlerdeki statik kelime listeleri (regex), harf veya sembol manipülasyonlarıyla (leetspeak) kolayca aşılabilmektedir. Bu proje, manipüle edilmiş ifadeleri algılayabilen, Türkçe'nin morfolojik yapısını anlayan ve moderatör yükünü ortadan kaldıran yapay zeka tabanlı kalıcı bir çözüm üretmeyi hedefler.

## Özgün Değer

Klasik "yıkıcı" sansür mekanizmaları (kelimeleri sansürleme veya silme) yerine "yapıcı" bir sistem sunulmuştur. Kötü kelimeler tespit edildiğinde sistem havuzundaki "harika", "şahane" gibi bağlama zarar vermeyen pozitif kelimelerle otomatik olarak değiştirilir.

## Kurulum ve Çalıştırma

Projeyi yerel makinenizde çalıştırmak için aşağıdaki adımları takip edebilirsiniz.

### 1. Gereksinimler

Proje çalışmak için Python 3.10+ sürümüne ihtiyaç duyar. Ayrıca derin öğrenme modeli için `torch` ve `transformers` kütüphaneleri kullanılmaktadır.

### 2. Sanal Ortam Oluşturma

Projeyi izole bir ortamda çalıştırmak için bir sanal ortam oluşturmanız önerilir:

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/macOS
python3 -m venv venv
source venv/bin/activate
```

### 3. Bağımlılıkların Yüklenmesi

Gerekli tüm kütüphaneleri `requirements.txt` dosyasından yükleyin:

```bash
pip install -r requirements.txt
```

### 4. Veritabanı Yapılandırması

Django veritabanı tablolarını oluşturmak için migrasyonları uygulayın:

```bash
python manage.py migrate
```

Yönetim paneline erişmek için bir süper kullanıcı (admin) oluşturun:

```bash
python manage.py createsuperuser
```

### 5. Uygulamayı Çalıştırma

Geliştirme sunucusunu başlatın:

```bash
python manage.py runserver
```

Sunucu başladıktan sonra tarayıcınızdan `http://127.0.0.1:8000/` adresine giderek projeye erişebilirsiniz.

### Önemli Not
Projenin akıllı filtreleme özelliğinin çalışması için `models/best_toxic_model.pt` dosyasının mevcut olması gerekmektedir. Eğer bu dosya eksikse sistem hata verecektir.

## Python Uygulaması ve Mimarisi

* **Veri Üretimi ve Ön İşleme:** sentetikveri.py modülü kullanılarak 1_milyon_toksik_veri_zenginlestirilmis.csv veri seti oluşturulmuştur.
* **Model Eğitimi:** kotu_soz_train.py ve kotu_soz_train.ipynb üzerinden dbmdz/bert-base-turkish-cased modeline eğitim verilmiş, en iyi ağırlıklar kaydedilmiştir.
* **Test ve Tahmin:** test.ipynb dosyasında leetspeak_to_normal() fonksiyonuyla veriler temizlenmiş ve predict_text() ile toksisite analizi yapılmıştır.
* **Web Entegrasyonu:** Model, Django tabanlı web projesine movies/toxic_utils.py modülü üzerinden entegre edilmiştir.

## Kullanılan Matematiksel Temel

* **Olasılık Hesaplaması:** BERT ham logit çıktıları Sigmoid fonksiyonuyla 0-1 aralığına sıkıştırılır. Denklem: P = 1 / (1 + e^-z)
* **Ağırlıklı Kayıp Fonksiyonu (Weighted Loss):** Dengesiz veri setleri için formül: Loss = - (1/N) * Σ [ w * y * log(p) + (1 - y) * log(1 - p) ]
* **Eşik Değeri Optimizasyonu:** Karar sınırı F1-Skorunu maksimize etmek üzere F1 = 2 * (Precision * Recall) / (Precision + Recall) formülüyle dinamik olarak ayarlanmıştır.

## Test ve Deneyler

* **Accuracy (Doğruluk):** %96.11
* **F1-Skoru:** 0.9617
* **Dinamik Eşik Değeri:** 0.46
* **Karmaşıklık Matrisi (Confusion Matrix):** Test verisindeki 48241 toksik ifadenin 46125'i doğru (True Positive) tespit edilerek gerçek dünya verilerindeki başarısı kanıtlanmıştır.

## Tespit Edilen Uç Durumlar (Edge Cases)

Geliştirilen model aşağıdaki uç durum başlıklarında test edilmiş ve sınıflandırılmıştır:

* Paradoksal Övgü ve Çelişkili Duygu İfadesi
* Kurgusal Alıntı ve Bağlamsal Hakaret
* Kurgusal Şiddet Söyleminin Alıntılanması
* Özel İsim ve Eser Adlarında Geçen Hakaret İfadeleri
* Öz-Eleştirel Hakaret ve İroni
* Leetspeak ve Karakter Manipülasyonu ile Gizleme
* Üstü Kapalı Nefret Söylemi (Dog-Whistling)
* Kasıtlı Yanlış Yönlendirme ve Aşırı Mübalağalı Saldırganlık
* Zalgo Text ve Gürültülü Karakter Manipülasyonu
* Agresif Modifiye Edilmiş Övgü ve Kirli Jargon
* Rastgele Karakter Dizileri ve Gürültü Yanılgısı
* Agresif Takdir ve Aşırı Şiddet İçerikli Metaforlar
* Kurgusal Karaktere Yönelik Sövgü
* Çift Anlamlılık ve Üstü Kapalı Cinsel İmalar
* Kısaltma Odaklı Sansür Aşma

## Sınırlılıklar ve Geliştirme Önerileri

* **Donanım:** BERT gibi büyük modeller eğitim ve çıkarım (inference) aşamalarında yüksek GPU gücüne ihtiyaç duyar. CPU kullanımında süreler uzamaktadır. Daha düşük maliyet için DistilBERT gibi hafif mimarilere geçiş yapılabilir.
* **Bağlam ve İroni:** Açıkça toksik kelime içermeyen kinayeli yapıların tespiti model için zorlayıcıdır.
* **Gelecek Çalışmalar:** İkili sınıflandırma (Toksik/Temiz) yerine "Küfür", "Irkçılık", "Cinsiyetçilik" gibi çoklu sınıflandırma altyapısı geliştirilebilir.

İstediğin güncel metrikler ve karmaşıklık matrisi tabloları şu şekildedir:

**Sınıflandırma Raporu (Classification Report)**

| Class | Precision | Recall | F1-Score | Support |
| --- | --- | --- | --- | --- |
| 0 | 0.9549 | 0.9664 | 0.9606 | 46319 |
| 1 | 0.9673 | 0.9561 | 0.9617 | 48241 |
| Accuracy | - | - | 0.9611 | 94560 |
| Macro Avg | 0.9611 | 0.9613 | 0.9611 | 94560 |
| Weighted Avg | 0.9612 | 0.9611 | 0.9611 | 94560 |

En İyi Eşik Değeri (Best Threshold): 0.46

**Karmaşıklık Matrisi (Confusion Matrix)**

| Actual \ Predicted | 0 | 1 |
| --- | --- | --- |
| 0 | 44761 | 1558 |
| 1 | 2116 | 46125 |

---


