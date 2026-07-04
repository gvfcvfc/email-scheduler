import csv
import re
from collections import Counter
from pathlib import Path

import numpy as np
import torch
from sklearn.metrics import classification_report
from torch import nn
from torch.utils.data import DataLoader, TensorDataset, random_split


PAD_TOKEN = "<pad>"
UNK_TOKEN = "<unk>"
MAX_LENGTH = 200
EPOCHS = 10
BATCH_SIZE = 32
LEARNING_RATE = 0.001
PRETRAINED_EMBEDDINGS_PATH = (Path(__file__).parent / "app" / "ml" / "data" / "glove.6B.100d.txt")
FREEZE_EMBEDDINGS = False


def tokenize(text):
    return re.findall(r"[a-z0-9']+", text.lower())


def build_vocab(texts, max_vocab_size=10000):
    counts = Counter()
    for text in texts:
        counts.update(tokenize(text))

    vocab = {PAD_TOKEN: 0, UNK_TOKEN: 1}
    for word, _ in counts.most_common(max_vocab_size - len(vocab)):
        vocab[word] = len(vocab)

    return vocab


def encode_text(text, vocab, max_length=MAX_LENGTH):
    token_ids = [vocab.get(token, vocab[UNK_TOKEN]) for token in tokenize(text)]
    token_ids = token_ids[:max_length]
    padding_needed = max_length - len(token_ids)
    return token_ids + [vocab[PAD_TOKEN]] * padding_needed


def load_pretrained_embeddings(vocab, embedding_path):
    if not embedding_path.exists():
        print(f"No pretrained embeddings found at {embedding_path}")
        print("Using random embeddings instead.")
        return None

    weights = None
    found_words = 0

    with open(embedding_path, "r", encoding="utf-8") as f:
        for line in f:
            parts = line.rstrip().split(" ")
            if len(parts) <= 2:
                continue

            word = parts[0]
            if word not in vocab:
                continue

            vector = torch.tensor([float(value) for value in parts[1:]], dtype=torch.float)

            if weights is None:
                embedding_dim = len(vector)
                weights = torch.empty(len(vocab), embedding_dim)
                nn.init.normal_(weights, mean=0.0, std=0.05)
                weights[vocab[PAD_TOKEN]].zero_()

            if len(vector) != weights.shape[1]:
                continue

            weights[vocab[word]] = vector
            found_words += 1

    if weights is None:
        print(f"No vocabulary words matched embeddings in {embedding_path}")
        print("Using random embeddings instead.")
        return None

    print(f"Loaded pretrained embeddings for {found_words}/{len(vocab)} vocab words.")
    return weights


def load_data(
    file_path,
    label_column="email_type",
    max_vocab_size=10000,
    max_length=MAX_LENGTH,
):
    texts = []
    raw_labels = []

    with open(file_path, "r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            text = f"{row['subject']} {row['body']}"
            texts.append(text)
            raw_labels.append(row[label_column])

    vocab = build_vocab(texts, max_vocab_size=max_vocab_size)
    label_names = sorted(set(raw_labels))
    label_to_index = {label: index for index, label in enumerate(label_names)}

    data = [encode_text(text, vocab, max_length=max_length) for text in texts]
    labels = [label_to_index[label] for label in raw_labels]

    return np.array(data), np.array(labels), vocab, label_names


class EmailClassifier(nn.Module):
    def __init__(
        self,
        vocab_size,
        embedding_dim=64,
        hidden_size=64,
        output_size=2,
        padding_idx=0,
        pretrained_embeddings=None,
        freeze_embeddings=False,
    ):
        super().__init__()
        if pretrained_embeddings is not None:
            embedding_dim = pretrained_embeddings.shape[1]
            self.embedding = nn.Embedding.from_pretrained(
                pretrained_embeddings,
                freeze=freeze_embeddings,
                padding_idx=padding_idx,
            )
        else:
            self.embedding = nn.Embedding(
                vocab_size,
                embedding_dim,
                padding_idx=padding_idx,
            )
        self.network = nn.Sequential(
            nn.Linear(embedding_dim, hidden_size),
            nn.LayerNorm(hidden_size),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(hidden_size, 32),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(32, output_size),
        )

    def forward(self, x):
        embedded = self.embedding(x)
        mask = (x != 0).unsqueeze(-1)
        summed = (embedded * mask).sum(dim=1)
        lengths = mask.sum(dim=1).clamp(min=1)
        averaged = summed / lengths
        return self.network(averaged)


def train_model(model, dataloader, criterion, optimizer, device, epochs=10):
    model.to(device)

    for epoch in range(epochs):
        model.train()
        total_loss = 0

        for features, targets in dataloader:
            features = features.to(device)
            targets = targets.to(device)
            optimizer.zero_grad()
            outputs = model(features)
            loss = criterion(outputs, targets)
            loss.backward()
            optimizer.step()
            total_loss += loss.item()

        average_loss = total_loss / len(dataloader)
        print(f"Epoch {epoch + 1}/{epochs} - loss: {average_loss:.4f}")


def evaluate_model(model, dataloader, device, label_names):
    model.to(device)
    model.eval()

    all_predictions = []
    all_targets = []

    with torch.no_grad():
        for features, targets in dataloader:
            features = features.to(device)
            targets = targets.to(device)
            outputs = model(features)
            predictions = torch.argmax(outputs, dim=1)
            all_predictions.extend(predictions.cpu().numpy())
            all_targets.extend(targets.cpu().numpy())

    report = classification_report(
        all_targets,
        all_predictions,
        labels=list(range(len(label_names))),
        target_names=label_names,
        zero_division=0,
    )
    print(report)
    return report


def main():
    file_path = Path(__file__).parent / "app" / "ml" / "data" / "email_type.csv"
    data, labels, vocab, label_names = load_data(file_path)

    dataset = TensorDataset(
        torch.tensor(data, dtype=torch.long),
        torch.tensor(labels, dtype=torch.long),
    )
    train_size = int(0.8 * len(dataset))
    test_size = len(dataset) - train_size
    train_dataset, test_dataset = random_split(
        dataset,
        [train_size, test_size],
        generator=torch.Generator().manual_seed(42),
    )

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    train_dataloader = DataLoader(
        train_dataset,
        batch_size=BATCH_SIZE,
        shuffle=True,
    )
    test_dataloader = DataLoader(
        test_dataset,
        batch_size=BATCH_SIZE,
        shuffle=False,
    )

    torch.manual_seed(42)
    pretrained_embeddings = load_pretrained_embeddings(vocab, PRETRAINED_EMBEDDINGS_PATH)
    model = EmailClassifier(
        vocab_size=len(vocab),
        output_size=len(label_names),
        pretrained_embeddings=pretrained_embeddings,
        freeze_embeddings=FREEZE_EMBEDDINGS,
    )
    criterion = nn.CrossEntropyLoss()
    optimizer = torch.optim.AdamW(
        model.parameters(),
        lr=LEARNING_RATE,
        weight_decay=0.1
    )

    train_model(
        model,
        train_dataloader,
        criterion,
        optimizer,
        device,
        epochs=EPOCHS,
    )
    evaluate_model(model, test_dataloader, device, label_names)


if __name__ == "__main__":
    main()
