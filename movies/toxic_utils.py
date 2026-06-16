import torch
import torch.nn as nn
from transformers import AutoModel, AutoTokenizer
from pathlib import Path

# YAPAY ZEKA (NLP) MODEL MİMARİSİ
class ToxicModel(nn.Module):
    """
    Siber zorbalık ve toksik kelime tespiti (Akıllı Sansür) için özelleştirilmiş Derin Öğrenme modeli.
    Önceden eğitilmiş (pre-trained) Türkçe BERT modeli taban alınarak, 
    ikili sınıflandırma (binary classification) yapacak şekilde fine-tune edilmiştir.
    """
    def __init__(self):
        super().__init__()
        # Türkçe doğal dil işleme görevleri için optimize edilmiş BERT tabanı
        self.bert = AutoModel.from_pretrained("dbmdz/bert-base-turkish-cased")
        # Aşırı öğrenmeyi (overfitting) engellemek için Dropout katmanı
        self.dropout = nn.Dropout(0.3)
        # BERT'ten çıkan 768 boyutlu vektörü, tek bir çıktıya (toksik mi, değil mi?) indirgeyen Lineer katman
        self.fc = nn.Linear(768, 1)

    def forward(self, input_ids, attention_mask):
        """
        Modelin ileri yayılım (forward pass) fonksiyonu.
        Gelen metin token'larını alır, BERT'ten geçirir ve sınıflandırma (CLS) token'ını döndürür.
        """
        out = self.bert(input_ids=input_ids, attention_mask=attention_mask)
        # Sadece tüm cümlenin anlamsal özetini taşıyan ilk token'ı (CLS) alıyoruz
        cls = out.last_hidden_state[:, 0, :]
        x = self.dropout(cls)
        x = self.fc(x)
        return x

# Donanım hızlandırma kontrolü: GPU (CUDA) varsa kullan, yoksa işlemciye (CPU) geç
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
# BERT modeline uygun, metni matematiksel dizilere çevirecek Türkçe Tokenizer
tokenizer = AutoTokenizer.from_pretrained("dbmdz/bert-base-turkish-cased")

# MODEL AĞIRLIKLARINI (WEIGHTS) YÜKLEME
def find_checkpoint_path():
    """
    Eğitilmiş modelin ağırlık dosyasını (best_toxic_model.pt) sistemde dinamik olarak arar.
    Django web sunucusu farklı dizinlerden çalıştırılabileceği için esnek bir yol bulucu tasarlanmıştır.
    """
    candidates = [
        Path("models/best_toxic_model.pt"),
        Path("../models/best_toxic_model.pt"),
    ]
    for path in candidates:
        if path.exists():
            return path
    raise FileNotFoundError("best_toxic_model.pt bulunamadi. Dosyayi test.py ile ayni klasore ya da bir ust klasore koyun.")


def load_model_and_threshold(device):
    """
    Önceden eğitilmiş PyTorch modelini (.pt) belleğe yükler.
    Modelin durum sözlüğünü (state_dict) eşleştirir ve karar verme eşiğini ayarlar.
    """
    checkpoint_path = find_checkpoint_path()
    checkpoint = torch.load(checkpoint_path, map_location=device)

    model = ToxicModel().to(device)
    if isinstance(checkpoint, dict) and "model_state_dict" in checkpoint:
        model.load_state_dict(checkpoint["model_state_dict"])
        threshold = float(checkpoint.get("threshold", 0.5))
    else:
        model.load_state_dict(checkpoint)
        threshold = 0.5

    # 0.46 değeri model eğitimi sırasında hesaplanan en optimum (F1-score) eşik değeridir.
    return model, 0.46

# 4 -> A
# 0 -> O
# 1 -> I
# 5 -> S
# 2 -> iki
# 3 -> E
# 6 -> G
def leetspeak_to_normal(text):
    """
    Kullanıcıların yapay zeka sansürünü aşmak için kullandığı 'Leetspeak' (harf yerine sayı/sembol)
    yöntemini bertaraf eden metin ön işleme fonksiyonu. (Örn: 's@l4k' -> 'salak').
    Bu sayede model manipüle edilmiş toksik metinleri bile başarıyla yakalar.
    """
    leet_dict = {
        'a': ['4', '@', "/\\"],
        'o': ['0'],
        'i': ['1','|', '!'],
        'l': ['1'],
        's': ['5'],
        'iki': ['2'],
        'e': ['3'],
        'g': ['6'],
    }
    for normal_char, leet_variants in leet_dict.items():
        for leet in leet_variants:
            text = text.replace(leet, normal_char)
    return text

# API istekleri gelmeden önce model bir kez Global olarak yüklenir (Sunucu her istekte yorulmaz)
model, best_threshold = load_model_and_threshold(device)

# TAHMİN / İNFERENCE YAPISI
def predict_text(model, tokenizer, text, device, max_length=128, threshold=0.5):
    """
    Gelen ham metni alır, token'lara ayırır ve BERT modeline sokarak 
    siber zorbalık/toksisite oranını (0 ile 1 arası bir olasılık) hesaplar.
    """
    # Modeli değerlendirme (eval) moduna alıyoruz ki Dropout vb. katmanlar sabit kalsın
    model.eval()
    tokens = tokenizer(
        text,
        padding="max_length",
        truncation=True,
        max_length=max_length,
        return_tensors="pt"
    )
    input_ids = tokens["input_ids"].to(device)
    attention_mask = tokens["attention_mask"].to(device)
    # Gradyan hesaplamasını kapatarak tahmini hızlandırıyoruz (Büyük bellek tasarrufu)
    with torch.no_grad():
        logits = model(input_ids, attention_mask)
        # Logits (ham skorlar), Sigmoid fonksiyonu ile 0-1 arası bir olasılık değerine dönüştürülür
        prob = torch.sigmoid(logits).item()
        # Sunucu konsolunda anlık izleme için log yazdırma
        print(f"Text: {text}\nToxicity Probability: {prob:.4f}")
        # Eğer hesaplanan olasılık, modelimizin ideal eşik değerinden yüksekse toksik (1) kabul edilir
        return 1 if prob > threshold else 0