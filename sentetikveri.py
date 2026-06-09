import pandas as pd
import os
import multiprocessing as mp
import numpy as np
import warnings
from datasets import load_dataset

warnings.filterwarnings("ignore")

# --- AYARLAR ---
CUSTOM_DATASET_PATH = "uc_ornekler_1000.csv" 
FINAL_OUTPUT_FILE = "1_milyon_toksik_veri_zenginlestirilmis.csv"
NUM_GPUS = 3
SAMPLES_PER_ROW = 12
BATCH_SIZE = 50

def load_and_merge_data():
    print("1. Aşama: HuggingFace veri seti indiriliyor...")
    try:
        dataset = load_dataset("Overfit-GM/turkish-toxic-language")
        df_hf = dataset['train'].to_pandas()[['text', 'is_toxic']]
    except Exception as e:
        print(f"HuggingFace verisi çekilemedi: {e}")
        df_hf = pd.DataFrame(columns=['text', 'is_toxic'])
    
    print(f"2. Aşama: Özel uç örnek veri seti ({CUSTOM_DATASET_PATH}) yükleniyor...")
    if os.path.exists(CUSTOM_DATASET_PATH):
        df_custom = pd.read_csv(CUSTOM_DATASET_PATH)
        if 'text' in df_custom.columns and 'is_toxic' in df_custom.columns:
            df_custom = df_custom[['text', 'is_toxic']]
            df_combined = pd.concat([df_custom, df_hf], ignore_index=True)
            print(f"-> {len(df_custom)} satır uç örnek eklendi. Toplam ham veri: {len(df_combined)}")
            return df_combined
    
    print("UYARI: Özel veri seti bulunamadı, sadece HF verisi kullanılacak.")
    return df_hf

def gpu_worker(worker_id, gpu_id, df_chunk, samples_per_row, batch_size):
    """Her bir GPU'nun çalıştıracağı paralel fonksiyon"""
    
    # NLPaug kütüphanesini process içinde import ediyoruz ki CUDA çakışması olmasın
    import nlpaug.augmenter.word as naw
    from tqdm import tqdm
    
    output_file = f"temp_part_{worker_id}.csv"
    
    print(f"[GPU {gpu_id}] Model Yükleniyor... Hedef: {output_file}")
    
    # Modeli ilgili GPU'ya atıyoruz (cuda:0, cuda:1, cuda:2)
    try:
        aug = naw.ContextualWordEmbsAug(
            model_path='dbmdz/bert-base-turkish-cased',
            action="substitute",
            aug_p=0.3,
            device=f'cuda:{gpu_id}' 
        )
    except Exception as e:
        print(f"[GPU {gpu_id}] MODEL YÜKLEME HATASI: {e}")
        return

    # Eğer yarım kaldıysa kaldığı yerden devam etme mekanizması
    start_index = 0
    if os.path.exists(output_file):
        try:
            mevcut_df = pd.read_csv(output_file)
            start_index = len(mevcut_df) // samples_per_row
            print(f"[GPU {gpu_id}] {output_file} bulundu. {start_index}. satırdan devam ediliyor...")
        except:
            pass
    else:
        pd.DataFrame(columns=['text', 'is_toxic', 'is_synthetic']).to_csv(output_file, index=False)

    synthetic_rows = []
    df_to_process = df_chunk.iloc[start_index:]
    
    print(f"[GPU {gpu_id}] Üretim Başladı! İşlenecek veri: {len(df_to_process)}")

    # TQDM progress bar sadece 0 numaralı worker'da düzgün görünür, o yüzden process_id belirttik
    for index, row in tqdm(df_to_process.iterrows(), total=df_to_process.shape[0], position=worker_id, desc=f"GPU-{gpu_id}"):
        original_text = str(row['text'])
        
        if original_text.strip() == "nan" or original_text.strip() == "":
            continue
            
        toxic_label = row['is_toxic']

        try:
            augmented_texts = aug.augment(original_text, n=samples_per_row)
            if isinstance(augmented_texts, str):
                augmented_texts = [augmented_texts]
                
            for aug_text in augmented_texts:
                synthetic_rows.append({
                    'text': aug_text,
                    'is_toxic': toxic_label,
                    'is_synthetic': 1
                })
        except Exception as e:
            print(f"\n[GPU {gpu_id} HATA] Satır atlandı. Hata: {e} | Metin: {original_text[:20]}...")
            continue

        # Küçük batch'ler halinde yaz (Veri kaybetmemek için)
        if len(synthetic_rows) >= batch_size:
            pd.DataFrame(synthetic_rows).to_csv(output_file, mode='a', header=False, index=False)
            synthetic_rows = []

    # Kalan verileri yaz
    if len(synthetic_rows) > 0:
        pd.DataFrame(synthetic_rows).to_csv(output_file, mode='a', header=False, index=False)
        
    print(f"[GPU {gpu_id}] İşlemini başarıyla tamamladı!")

if __name__ == "__main__":
    # PyTorch/CUDA çoklu işlem (multiprocessing) için spawn zorunludur
    mp.set_start_method('spawn', force=True)

    df_main = load_and_merge_data()
    
    # Veriyi 3 GPU için 3 eşit parçaya bölüyoruz
    chunks = np.array_split(df_main, NUM_GPUS)
    
    processes = []
    
    print("\n--- 3x RTX 3090 MOTORLARI ATEŞLENİYOR ---")
    for i in range(NUM_GPUS):
        gpu_id = i # 0, 1, 2
        p = mp.Process(target=gpu_worker, args=(i, gpu_id, chunks[i], SAMPLES_PER_ROW, BATCH_SIZE))
        p.start()
        processes.append(p)

    # Bütün işlemlerin bitmesini bekle
    for p in processes:
        p.join()
        
    print("\nÜretim Aşaması Bitti. Parçalar birleştiriliyor...")
    
    # Üretilen 3 parçayı al ve tek bir dosyada birleştir
    final_df_list = []
    for i in range(NUM_GPUS):
        temp_file = f"temp_part_{i}.csv"
        if os.path.exists(temp_file):
            temp_df = pd.read_csv(temp_file)
            final_df_list.append(temp_df)
            
    if len(final_df_list) > 0:
        final_dataset = pd.concat(final_df_list, ignore_index=True)
        final_dataset.to_csv(FINAL_OUTPUT_FILE, index=False)
        print(f"\n🚀 MUAZZAM! Toplam {len(final_dataset)} sentetik veri {FINAL_OUTPUT_FILE} dosyasına kaydedildi.")
        
        # Temp dosyalarını temizle (İstersen burayı yoruma alıp parçaları da saklayabilirsin)
        for i in range(NUM_GPUS):
            temp_file = f"temp_part_{i}.csv"
            if os.path.exists(temp_file):
                os.remove(temp_file)
    else:
        print("HATA: Birleştirilecek geçici dosya bulunamadı!")
