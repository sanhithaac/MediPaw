import os
import glob
import hashlib
from PIL import Image
import torch
from torch.utils.data import Dataset, DataLoader
import torchvision.transforms as transforms

def compute_md5(image_path):
    try:
        with open(image_path, "rb") as f:
            return hashlib.md5(f.read()).hexdigest()
    except Exception:
        return None

class MediPawSkinDataset(Dataset):
    def __init__(self, root_dir, split="train", transform=None, filter_duplicates=True, ignore_hashes=None):
        self.split_dir = os.path.join(root_dir, split)
        self.transform = transform
        self.filter_duplicates = filter_duplicates
        self.image_paths = []
        self.labels = []
        self.seen_hashes = set() if ignore_hashes is None else ignore_hashes
        
        if not os.path.exists(self.split_dir):
            raise FileNotFoundError(f"[ERROR] Split directory not found: {self.split_dir}")

        self.classes = sorted([d for d in os.listdir(self.split_dir) if os.path.isdir(os.path.join(self.split_dir, d))])
        self.class_to_idx = {cls_name: i for i, cls_name in enumerate(self.classes)}

        print(f"[DataLoader: {split.upper()}] Indexing dataset across {len(self.classes)} classes...")
        skipped = 0

        for cls_name in self.classes:
            cls_idx = self.class_to_idx[cls_name]
            cls_dir = os.path.join(self.split_dir, cls_name)
            files = []
            for ext in ('*.jpg', '*.jpeg', '*.png', '*.webp'):
                files.extend(glob.glob(os.path.join(cls_dir, ext)))
            
            for f in sorted(files):
                if self.filter_duplicates:
                    f_hash = compute_md5(f)
                    if not f_hash or f_hash in self.seen_hashes:
                        skipped += 1
                        continue
                    self.seen_hashes.add(f_hash)
                
                self.image_paths.append(f)
                self.labels.append(cls_idx)

        msg = f"(Filtered {skipped} duplicates via MD5)" if filter_duplicates else "(Full Stratified Evaluation Dataset)"
        print(f"[DataLoader: {split.upper()}] Loaded {len(self.image_paths)} valid images {msg}.")

    def __len__(self):
        return len(self.image_paths)

    def __getitem__(self, idx):
        try:
            image = Image.open(self.image_paths[idx]).convert("RGB")
        except Exception:
            image = Image.new("RGB", (224, 224), (128, 128, 128))

        if self.transform:
            image = self.transform(image)

        return image, self.labels[idx]

def get_dataloaders(dataset_root, batch_size=32, num_workers=0, filter_duplicates=True):
    custom_normalize = transforms.Normalize(
        mean=[0.5263, 0.4534, 0.4237],
        std=[0.2104, 0.1994, 0.1972]
    )

    train_transform = transforms.Compose([
        transforms.RandomResizedCrop(224, scale=(0.8, 1.0)),
        transforms.RandomHorizontalFlip(p=0.5),
        transforms.RandomRotation(degrees=15),
        transforms.ColorJitter(brightness=0.2, contrast=0.2),
        transforms.ToTensor(),
        custom_normalize
    ])

    eval_transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        custom_normalize
    ])

    print("\n[INFO] Initializing PyTorch DataLoaders with Custom Veterinary RGB Normalization...")
    
    train_dataset = MediPawSkinDataset(dataset_root, split="train", transform=train_transform, filter_duplicates=filter_duplicates)
    val_dataset = MediPawSkinDataset(dataset_root, split="val", transform=eval_transform, filter_duplicates=filter_duplicates, ignore_hashes=train_dataset.seen_hashes.copy())
    test_dataset = MediPawSkinDataset(dataset_root, split="test", transform=eval_transform, filter_duplicates=filter_duplicates, ignore_hashes=train_dataset.seen_hashes.union(val_dataset.seen_hashes))

    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True, num_workers=num_workers, pin_memory=True)
    val_loader = DataLoader(val_dataset, batch_size=batch_size, shuffle=False, num_workers=num_workers, pin_memory=True)
    test_loader = DataLoader(test_dataset, batch_size=batch_size, shuffle=False, num_workers=num_workers, pin_memory=True)

    return train_loader, val_loader, test_loader, train_dataset.classes
