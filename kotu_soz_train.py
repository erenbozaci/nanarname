import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
from transformers import AutoModel, AutoTokenizer, get_linear_schedule_with_warmup
from datasets import load_dataset
import numpy as np
from tqdm import tqdm
from sklearn.metrics import f1_score, precision_score, recall_score, classification_report, confusion_matrix
from copy import deepcopy
from torch.amp import autocast, GradScaler
import warnings

# Gereksiz uyarıları gizlemek için
warnings.filterwarnings("ignore")

# 1. Model ve Tokenizer Tanımlamaları
class ToxicModel(nn.Module):
    """
    Türkçe dil yapısına uygun BERT modelini temel alan ikili (binary) sınıflandırma modelimiz.
    """
    def __init__(self):
        # HuggingFace üzerinden önceden eğitilmiş Türkçe BERT modelini çekiyoruz
        super().__init__()
        self.bert = AutoModel.from_pretrained("dbmdz/bert-base-turkish-cased")
        # Aşırı öğrenmeyi (overfitting) engellemek için %30 oranında nöronları rastgele kapatıyoruz
        self.dropout = nn.Dropout(0.3)
        # BERT'in 768 boyutlu vektör çıktısını, Toksik/Temiz kararı için 1 boyuta (tek bir olasılık değerine) indirgiyoruz
        self.fc = nn.Linear(768, 1)

    def forward(self, input_ids, attention_mask):
        out = self.bert(input_ids=input_ids, attention_mask=attention_mask)
        # Cümlenin bütünsel anlamını taşıyan [CLS] token'ının vektörünü alıyoruz
        cls = out.last_hidden_state[:, 0, :]
        x = self.dropout(cls)
        x = self.fc(x)
        return x

class ToxicDataset(Dataset):
    """
    HuggingFace veri setini PyTorch DataLoader'ın anlayabileceği Tensör formatına dönüştüren özel veri sınıfımız.
    """
    def __init__(self, ds):
        self.ds = ds

    def __len__(self):
        return len(self.ds)

    def __getitem__(self, idx):
        item = self.ds[idx]
        return {
            "input_ids": item["input_ids"].clone().detach() if torch.is_tensor(item["input_ids"]) else torch.tensor(item["input_ids"], dtype=torch.long),
            "attention_mask": item["attention_mask"].clone().detach() if torch.is_tensor(item["attention_mask"]) else torch.tensor(item["attention_mask"], dtype=torch.long),
            "labels": torch.tensor(item["is_toxic"], dtype=torch.float) 
        }

# 2. Yardımcı Fonksiyonlar
def find_best_threshold(probs, labels, start=0.10, end=0.90, step=0.02):
    """
    (Kritik Optimizasyon Adımı): Dengesiz veri setlerinde 0.5 eşik değeri yanıltıcı olacağından,
    F1-Skorunu maksimize edecek en ideal matematiksel karar sınırını (Threshold) dinamik olarak buluyoruz.
    """
    probs = np.asarray(probs)
    labels = np.asarray(labels).astype(int)
    print(f"Hesaplanan En Iyi Threshold: {best_t}")
    best_t = 0.5
    best_f1 = -1.0

# Belirlenen aralıklarda tarama yaparak en yüksek F1 skorunu veren threshold değerini yakalıyoruz
    for t in np.arange(start, end + 1e-8, step):
        preds = (probs >= t).astype(int)
        f1 = f1_score(labels, preds, zero_division=0)
        if f1 > best_f1:
            best_f1 = f1
            best_t = float(t)

    return best_t, best_f1

def evaluate(model, dataloader, criterion, device, threshold=0.5):
    """
    Modelin doğrulama (validation) ve test setlerindeki başarısını belirlenen eşik değerine göre ölçer.
    """
    model.eval()# Modeli değerlendirme moduna alıyoruz (Dropout vb. kapanır)
    total_loss = 0.0
    all_probs = []
    all_labels = []

    with torch.no_grad(): # Gradyan hesaplamalarını kapatarak bellek tasarrufu sağlıyoruz
        for batch in tqdm(dataloader, leave=False, desc="Evaluating"):
            input_ids = batch["input_ids"].to(device)
            attention_mask = batch["attention_mask"].to(device)
            labels = batch["labels"].unsqueeze(1).to(device)

            logits = model(input_ids, attention_mask)
            loss = criterion(logits, labels)
            total_loss += loss.item()

            # Sigmoid fonksiyonu ile ham logit çıktılarını 0 ile 1 arasında olasılıklara sıkıştırıyoruz
            probs = torch.sigmoid(logits).squeeze(1)
            all_probs.extend(probs.detach().cpu().numpy().tolist())
            all_labels.extend(labels.squeeze(1).detach().cpu().numpy().astype(int).tolist())

    probs_arr = np.asarray(all_probs)
    labels_arr = np.asarray(all_labels).astype(int)
    preds_arr = (probs_arr >= threshold).astype(int)

    precision = precision_score(labels_arr, preds_arr, zero_division=0)
    recall = recall_score(labels_arr, preds_arr, zero_division=0)
    f1 = f1_score(labels_arr, preds_arr, zero_division=0)

    return {
        "loss": total_loss / max(len(dataloader), 1),
        "precision": float(precision),
        "recall": float(recall),
        "f1": float(f1),
        "probs": all_probs,
        "labels": labels_arr.tolist(),
        "preds": preds_arr.tolist(),
    }

def predict_text(model, tokenizer, text, device, max_length=128, threshold=0.5):
    """
    Dışarıdan gelen tekil bir metnin (kullanıcı yorumunun) toksik olup olmadığını tahmin eder.
    """
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

    with torch.no_grad():
        logits = model(input_ids, attention_mask)
        prob = torch.sigmoid(logits).item()
        # Eğer hesaplanan olasılık optimize ettiğimiz threshold'dan büyükse 1 (Toksik), değilse 0 (Temiz) döner
        return 1 if prob > threshold else 0

# 3. Ana Çalıştırma Bloğu (Main)
def main():
    print("Modeller ve yerel CSV veri seti yükleniyor...")
    tokenizer = AutoTokenizer.from_pretrained("dbmdz/bert-base-turkish-cased")
    
    # Sistemin veri ihtiyacını karşılamak için ürettiğimiz 1 milyonluk yerel ve zenginleştirilmiş veri setini yüklüyoruz
    dataset = load_dataset("csv", data_files={"train": "1_milyon_toksik_veri_zenginlestirilmis.csv"}, delimiter=",")

    def tokenize(example):
        return tokenizer(
            example["text"],
            padding="max_length",
            truncation=True,
            max_length=128
        )
        
    dataset = dataset.map(tokenize, batched=True)
    dataset.set_format(
        type="torch",
        columns=["input_ids", "attention_mask", "is_toxic"]
    )

    # Veriyi Eğitim (%90) ve Test (%10) olarak ikiye bölüyoruz
    dataset = dataset["train"].train_test_split(test_size=0.1)
    train_ds = dataset["train"]
    val_ds = dataset["test"]

    print(dataset)

# Bellek yönetimi için Batch Size ayarlamaları
    BATCH_SIZE = 900
    train_loader = DataLoader(ToxicDataset(train_ds), batch_size=BATCH_SIZE, shuffle=True)
    val_loader = DataLoader(ToxicDataset(val_ds), batch_size=BATCH_SIZE * 2, shuffle=False)

    # Cihaz ve Model Ayarlamaları (TEK GPU)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"✅ Kullanılan cihaz: {device}")
    model = ToxicModel()
    
    # Eğer sistemde birden fazla GPU varsa DataParallel ile eğitimi hızlandırıyoruz
    if torch.cuda.device_count() >= 3:
        print("✅ 3 GPU birleştiriliyor! Tek epoch 3 kat hızlı bitecek...")
        model = nn.DataParallel(model, device_ids=[0, 1, 2])

    model = model.to(device)

    # Kayıp Fonksiyonu Ağırlıklandırması (Pos Weight)
    # Dengesiz Sınıf (Imbalanced Data) Problemini Çözme
    # Toksik verilerin sayıca azlığını dengelemek için pozitif sınıfa ağırlık (pos_weight) atıyoruz
    train_labels = torch.tensor(
        [float(train_ds[i]["is_toxic"]) for i in range(len(train_ds))],
        dtype=torch.float,
    )
    num_pos = train_labels.sum().item()
    num_neg = len(train_labels) - num_pos
    pos_weight = torch.tensor([num_neg / max(num_pos, 1.0)], device=device)
    criterion = nn.BCEWithLogitsLoss(pos_weight=pos_weight)

    optimizer = torch.optim.AdamW(model.parameters(), lr=2e-5, weight_decay=0.01)

    num_epochs = 10
    total_steps = len(train_loader) * num_epochs
    num_warmup_steps = int(0.1 * total_steps)
    # Öğrenme oranını (learning rate) dinamik olarak ayarlayan scheduler
    scheduler = get_linear_schedule_with_warmup(
        optimizer,
        num_warmup_steps=num_warmup_steps,
        num_training_steps=total_steps,
    )

    # Bellek tasarrufu ve hız için Mixed Precision (FP16) ölçeklendiricisi
    scaler = GradScaler(enabled=(device.type == "cuda"))

    # Early Stopping (Erken Durdurma) Parametreleri
    best_val_f1 = 0.0
    best_threshold = 0.5
    best_state_dict = None
    patience = 2
    patience_counter = 0

    print("Eğitim Başlıyor...")
    for epoch in range(num_epochs):
        model.train()
        total_loss = 0.0

        for batch in tqdm(train_loader, desc=f"Epoch {epoch+1}/{num_epochs}"):
            input_ids = batch["input_ids"].to(device)
            attention_mask = batch["attention_mask"].to(device)
            labels = batch["labels"].unsqueeze(1).to(device) # Label sorunu düzeltildi

            optimizer.zero_grad(set_to_none=True)
            
            # Mixed Precision (autocast) ile ileri yayılım ve kayıp hesaplama
            with autocast(device_type=device.type, enabled=(device.type == "cuda")):
                outputs = model(input_ids, attention_mask)
                loss = criterion(outputs, labels)

            # Geri yayılım (Backpropagation) ve ağırlık güncellemeleri
            scaler.scale(loss).backward()
            scaler.unscale_(optimizer)
            torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)# Patlayan gradyanları engellemek için
            scaler.step(optimizer)
            scaler.update()
            scheduler.step()

            total_loss += loss.item()

        # Her Epoch sonunda kendi bulduğumuz ideal threshold değerine göre validation metriklerini ölçüyoruz
        val_for_threshold = evaluate(model, val_loader, criterion, device, threshold=best_threshold)
        tuned_threshold, _ = find_best_threshold(val_for_threshold["probs"], val_for_threshold["labels"])
        val_metrics = evaluate(model, val_loader, criterion, device, threshold=tuned_threshold)

        avg_train_loss = total_loss / max(len(train_loader), 1)

        print(f"\nEpoch {epoch+1}/{num_epochs}")
        print(f"Train Loss: {avg_train_loss:.4f}")
        print(f"Val Loss: {val_metrics['loss']:.4f}")
        print(f"Val Precision: {val_metrics['precision']:.4f}")
        print(f"Val Recall: {val_metrics['recall']:.4f}")
        print(f"Val F1: {val_metrics['f1']:.4f}")
        print(f"Best Threshold (this epoch): {tuned_threshold:.2f}")

        # Eğer F1-Skoru bir önceki iterasyondan daha iyiyse modeli güncelliyoruz (Early Stopping Mantığı)
        if val_metrics["f1"] > best_val_f1:
            best_val_f1 = val_metrics["f1"]
            best_threshold = tuned_threshold
            
            if isinstance(model, nn.DataParallel):
                best_state_dict = deepcopy(model.module.state_dict())
            else:
                best_state_dict = deepcopy(model.state_dict())
                
            patience_counter = 0
            print("Best model updated.")
        else:
            patience_counter += 1
            print(f"No improvement. Early stopping counter: {patience_counter}/{patience}")

# Model kendini tekrar etmeye başlarsa zaman kaybetmemek için eğitimi erken durduruyoruz
        if patience_counter >= patience:
            print("Early stopping triggered.")
            break

    # Eğitilen En İyi Ağırlıkları ve Hesaplanan Threshold Değerini Kaydet
    if best_state_dict is not None:
        if isinstance(model, nn.DataParallel):
            model.module.load_state_dict(best_state_dict)
        else:
            model.load_state_dict(best_state_dict)

    checkpoint = {
        "model_state_dict": best_state_dict,
        "threshold": best_threshold,# Entegre sistemde kullanılacak karar sınırı
    }
    torch.save(checkpoint, "best_toxic_model_v2.pt")
    print(f"\nTraining complete. Best Val F1: {best_val_f1:.4f}, threshold: {best_threshold:.2f}")

    # Notebook'un Sonundaki TEST Senaryoları
    # 4. TEST VE DEĞERLENDİRME ÇIKTILARI
    print("\n--- TEST VE DEĞERLENDİRME ---")
    final_metrics = evaluate(model, val_loader, criterion, device, threshold=best_threshold)
    print("Classification Report:")
    print(classification_report(final_metrics["labels"], final_metrics["preds"], digits=4))
    # Modelin doğru ve yanlış tahmin (False Positive, False Negative) sayılarını matris formatında raporluyoruz
    print("Confusion Matrix:")
    print(confusion_matrix(final_metrics["labels"], final_metrics["preds"]))

    # Basit bir örnek tahmin testi
    # Uçtan uca (end-to-end) bir deneme senaryosu
    sample_text = "NAber"
    test_prediction = predict_text(model, tokenizer, sample_text, device, threshold=best_threshold)
    print(f"Örnek Cümle: '{sample_text}' -> Tahmin (1: Toksik, 0: Temiz): {test_prediction}")

if __name__ == "__main__":
    main()
