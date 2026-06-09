import torch
import torch.nn as nn
from transformers import AutoModel, AutoTokenizer
from pathlib import Path

class ToxicModel(nn.Module):
    def __init__(self):
        super().__init__()
        self.bert = AutoModel.from_pretrained("dbmdz/bert-base-turkish-cased")
        self.dropout = nn.Dropout(0.3)
        self.fc = nn.Linear(768, 1)

    def forward(self, input_ids, attention_mask):
        out = self.bert(input_ids=input_ids, attention_mask=attention_mask)
        cls = out.last_hidden_state[:, 0, :]
        x = self.dropout(cls)
        x = self.fc(x)
        return x

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
tokenizer = AutoTokenizer.from_pretrained("dbmdz/bert-base-turkish-cased")

def find_checkpoint_path():
    candidates = [
        Path("models/best_toxic_model.pt"),
        Path("../models/best_toxic_model.pt"),
    ]
    for path in candidates:
        if path.exists():
            return path
    raise FileNotFoundError("best_toxic_model.pt bulunamadi. Dosyayi test.py ile ayni klasore ya da bir ust klasore koyun.")


def load_model_and_threshold(device):
    checkpoint_path = find_checkpoint_path()
    checkpoint = torch.load(checkpoint_path, map_location=device)

    model = ToxicModel().to(device)
    if isinstance(checkpoint, dict) and "model_state_dict" in checkpoint:
        model.load_state_dict(checkpoint["model_state_dict"])
        threshold = float(checkpoint.get("threshold", 0.5))
    else:
        model.load_state_dict(checkpoint)
        threshold = 0.5

    return model, 0.46

# 4 -> A
# 0 -> O
# 1 -> I
# 5 -> S
# 2 -> iki
# 3 -> E
# 6 -> G
def leetspeak_to_normal(text):
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

model, best_threshold = load_model_and_threshold(device)

def predict_text(model, tokenizer, text, device, max_length=128, threshold=0.5):
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
        print(f"Text: {text}\nToxicity Probability: {prob:.4f}")
        return 1 if prob > threshold else 0