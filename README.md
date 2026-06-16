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

## Kurulum ve Çalıştırma (Docker)

Bu proje, kurulum sürecini basitleştirmek ve çevre farklılıklarını ortadan kaldırmak için tamamen Dockerize edilmiştir. Docker; Python, PyTorch ve BERT modeli gibi tüm bağımlılıkları otomatik olarak yapılandırır.

### 1. Projenin İndirilmesi
Öncelikle projeyi bilgisayarınıza klonlayın ve proje dizinine gidin:

```bash
git clone https://github.com/erenbozaci/nanarname.git
cd nanarname
```

### 2. Model Dosyasının Hazırlanması
Projenin akıllı filtreleme özelliğinin çalışması için eğitilmiş model dosyasını eklemeniz gerekmektedir:
- `best_toxic_model.pt` dosyasını projenin kök dizininde bulunan **`models/`** klasörünün içine yerleştirin.
- Bu dosya eksik olduğunda sistem model yükleme hatası verecektir.

### 3. Gereksinimler
Sisteminizde aşağıdaki araçların yüklü olduğundan emin olun:
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (Windows ve macOS için) veya Docker Engine (Linux için).
- [Docker Compose](https://docs.docker.com/compose/install/) (Genellikle Docker Desktop ile birlikte gelir).

### 4. Uygulamayı Başlatma
Terminalinizi veya komut satırınızı proje kök dizininde açın ve aşağıdaki komutu çalıştırın:

```bash
docker compose up --build
```

**Bu komut sırasıyla şunları gerçekleştirir:**
- Gerekli Python sürümünü ve sistem bağımlılıklarını hazırlar.
- `requirements.txt` dosyasındaki kütüphaneleri yükler.
- **BERT modelini (dbmdz/bert-base-turkish-cased) indirir ve imaj içerisine önbelleğe alır.**
- Veritabanı migrasyonlarını (migrations) otomatik olarak uygular.
- Statik dosyaları toplar (collectstatic).
- Geliştirme sunucusunu `http://localhost:8000` adresinde başlatır.

### 5. Uygulamaya Erişim
Sunucu ayağa kalktıktan sonra tarayıcınızdan aşağıdaki adreslere erişebilirsiniz:
- **Web Sitesi:** [http://localhost:8000](http://localhost:8000)
- **Yönetim Paneli:** [http://localhost:8000/admin](http://localhost:8000/admin)

### 6. Yönetici (Admin) Hesabı Oluşturma
Sisteme giriş yapabilmek ve filmleri yönetebilmek için bir süper kullanıcı (superuser) oluşturmanız gerekir. Uygulama çalışırken yeni bir terminal açın ve şu komutu çalıştırın:

```bash
docker compose exec web python manage.py createsuperuser
```
Ardından ekrandaki talimatları izleyerek kullanıcı adı, e-posta ve şifrenizi belirleyin.

### 7. Faydalı Komutlar

- **Arka Planda Çalıştırma:** Uygulamayı arka planda başlatmak için:
  ```bash
  docker compose up -d
  ```
- **Logları İzleme:** Arka planda çalışan uygulamanın çıktılarını canlı görmek için:
  ```bash
  docker compose logs -f
  ```
- **Durdurma:** Konteynerleri durdurmak için:
  ```bash
  docker compose down
  ```
- **Yeniden Yapılandırma:** `requirements.txt` veya `Dockerfile` üzerinde değişiklik yaptıysanız imajı yeniden oluşturmak için:
  ```bash
  docker compose up --build
  ```

### Önemli Not
- **Model Dosyası:** Projenin akıllı filtreleme özelliğinin çalışması için `models/best_toxic_model.pt` dosyasının mevcut olması gerekmektedir. Eğer bu dosya eksikse sistem hata verecektir.
- **BERT Modeli:** Akıllı filtreleme özelliğinin tam performanslı çalışabilmesi için BERT modelinin indirilmesi gerekmektedir. İlk kurulumda (build aşamasında) internet hızınıza bağlı olarak model indirme işlemi birkaç dakika sürebilir. İndirilen model Docker imajı içerisinde saklanacağı için sonraki çalıştırmalarda tekrar indirme yapılmaz.

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

## 📂 Proje Mimarisi ve Klasör Yapısı

Bu proje, Django web framework'ü ile PyTorch tabanlı NLP (Doğal Dil İşleme) modelinin entegre çalıştığı hibrit bir mimariye sahiptir. Proje dizin yapısı ve modüllerin görevleri aşağıda detaylandırılmıştır:

### ⚙️ Ana Proje ve Konfigürasyon
* **`eksicaciklar/`**: Projenin ana ayar dizinidir (Django Root). 
    * Sistemin veritabanı bağlantıları, güvenlik ayarları (`settings.py`), global URL yönlendirmeleri (`urls.py`) ve sunucu dağıtım konfigürasyonlarını (WSGI/ASGI) içerir.
* **`manage.py`**: Django'nun komut satırı yöneticisidir. Sunucuyu başlatma, veritabanı migrasyonları ve test süreçleri bu dosya üzerinden yürütülür.
* **`requirements.txt`**: Projenin bağımlılıklarını (Django, PyTorch, Transformers vb.) barındıran kütüphane listesidir.

### 🧠 Web Uygulaması ve Yapay Zeka Entegrasyonu
* **`movies/`**: Sistemin kalbini oluşturan ana Django uygulamasıdır (App).
    * `models.py`: Veritabanı mimarisi (Filmler, Kullanıcılar, Yorumlar ve Ceza/Ban tabloları).
    * `views.py`: Arka plan mantığı ve HTTP isteklerinin işlendiği kontrolcü (Controller) dosyası.
    * `forms.py`: Kullanıcıdan alınan verilerin yapılandırıldığı ve doğrulandığı formlar.
    * **`toxic_utils.py`**: **Projenin en kritik bileşenidir.** Eğitilmiş BERT yapay zeka modelinin web sitesine köprü kurduğu, anlık toksisite (siber zorbalık) analizi ve leetspeak manipülasyon filtrelemesinin yapıldığı NLP entegrasyon modülüdür.

### 📊 Veri Bilimi ve Model Eğitimi
* **`sentetikveri/`**: Yapay zeka modelinin beslendiği verilerin işlendiği dizindir. Veri setinin oluşturulması, temizlenmesi ve model eğitimine (Jupyter Notebooks üzerinden) hazır hale getirilmesi süreçlerini kapsar.
* **`1_milyon_toksik_veri_zenginlestirilmis.csv`**: BERT modelinin ince ayarı (fine-tuning) için kullanılan, zenginleştirilmiş ve etiketlenmiş geniş çaplı veri setidir.

### 🎨 Arayüz ve Statik Dosyalar (Frontend)
* **`templates/`**: Kullanıcıya sunulan HTML dosyalarının bulunduğu dizindir (MVC mimarisindeki View katmanı).
* **`static/`**: Sitenin görsel ve dinamik istemci tarafı dosyalarını barındırır (CSS stilleri, JS scriptleri).
* **`media/`**: Kullanıcılar tarafından sisteme dinamik olarak yüklenen dosyaların (örn. profil fotoğrafları - `profile_pics/`) saklandığı dizindir.

### 🛠️ Geliştirme Ortamı
* **`.venv/`**: Projenin izole bir şekilde çalışmasını sağlayan Python sanal ortamıdır (Virtual Environment).
* **`.github/`**: (Varsa) GitHub Actions gibi sürekli entegrasyon (CI/CD) süreçlerinin yapılandırma dosyalarını tutar.


---


