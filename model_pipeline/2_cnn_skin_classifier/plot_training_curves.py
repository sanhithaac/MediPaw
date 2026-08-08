import os
import json
import matplotlib.pyplot as plt
import numpy as np

def plot_curves():
    # Set high-resolution, presentation-ready formatting
    style = 'seaborn-v0_8-whitegrid' if 'seaborn-v0_8-whitegrid' in plt.style.available else 'default'
    plt.style.use(style)
    plt.rcParams.update({
        'font.size': 12,
        'axes.labelsize': 14,
        'axes.titlesize': 15,
        'xtick.labelsize': 11,
        'ytick.labelsize': 11,
        'legend.fontsize': 12,
        'figure.titlesize': 17,
        'font.family': 'sans-serif'
    })

    # Load Colab training history
    json_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'colab_training_history.json')
    with open(json_path, 'r') as f:
        history = json.load(f)

    epochs = np.arange(1, len(history['train_loss']) + 1)

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6.5), dpi=300)

    # ================= 1. LOSS CURVES (Left Plot) =================
    ax1.plot(epochs, history['train_loss'], label='Training Loss', color='#1f77b4', linewidth=2.5, marker='o', markersize=5)
    ax1.plot(epochs, history['val_loss'], label='Validation Loss', color='#ff7f0e', linewidth=2.5, marker='s', markersize=5, linestyle='--')

    # Annotate minimum validation loss
    min_val_idx = np.argmin(history['val_loss'])
    min_val_epoch = epochs[min_val_idx]
    min_val_loss = history['val_loss'][min_val_idx]

    ax1.annotate(f'Min Val Loss: {min_val_loss:.4f}\n(Epoch {min_val_epoch})',
                 xy=(min_val_epoch, min_val_loss), xytext=(max(1, min_val_epoch - 10), min_val_loss + 2.2),
                 arrowprops=dict(facecolor='black', shrink=0.05, width=1.5, headwidth=6),
                 bbox=dict(boxstyle="round,pad=0.4", fc="white", ec="black", lw=1, alpha=0.9),
                 fontsize=11, fontweight='bold')

    ax1.set_title('CNN 1: Cross-Entropy & Focal Loss Progression\n(3-Way Stratified Training Suite)', fontweight='bold', pad=12)
    ax1.set_xlabel('Epochs', fontweight='bold')
    ax1.set_ylabel('Loss Value ($L_{CE}$)', fontweight='bold')
    ax1.set_xlim([1, len(epochs)])
    ax1.set_xticks(np.arange(1, len(epochs) + 1, 2))
    ax1.legend(loc='upper right', frameon=True, facecolor='white', framealpha=0.95)
    ax1.grid(True, linestyle=':', alpha=0.7)

    # ================= 2. ACCURACY CURVES (Right Plot) =================
    ax2.plot(epochs, history['train_acc'], label='Training Accuracy (%)', color='#2ca02c', linewidth=2.5, marker='o', markersize=5)
    ax2.plot(epochs, history['val_acc'], label='Validation Accuracy (%)', color='#d62728', linewidth=2.5, marker='s', markersize=5, linestyle='--')

    # Annotate Peak Validation Accuracy
    max_val_idx = np.argmax(history['val_acc'])
    max_val_epoch = epochs[max_val_idx]
    max_val_acc = history['val_acc'][max_val_idx]

    ax2.annotate(f'Peak Val Accuracy: {max_val_acc:.2f}%\n(Epoch {max_val_epoch})',
                 xy=(max_val_epoch, max_val_acc), xytext=(max(1, max_val_epoch - 13), max_val_acc - 18.0),
                 arrowprops=dict(facecolor='black', shrink=0.05, width=1.5, headwidth=6),
                 bbox=dict(boxstyle="round,pad=0.4", fc="white", ec="darkred", lw=1.5, alpha=0.95),
                 fontsize=11, fontweight='bold', color='darkred')

    # Benchmark Line: Untouched Test Accuracy
    ax2.axhline(y=91.45, color='#6a0dad', linestyle='-.', linewidth=2.2, label='Untouched Test Accuracy (91.45%)')

    ax2.set_title('CNN 1: Diagnostic Accuracy Over Epochs\n(EfficientNet-V2-Small Backbone)', fontweight='bold', pad=12)
    ax2.set_xlabel('Epochs', fontweight='bold')
    ax2.set_ylabel('Accuracy (%)', fontweight='bold')
    ax2.set_ylim([15, 100])
    ax2.set_xlim([1, len(epochs)])
    ax2.set_xticks(np.arange(1, len(epochs) + 1, 2))
    ax2.legend(loc='lower right', frameon=True, facecolor='white', framealpha=0.95)
    ax2.grid(True, linestyle=':', alpha=0.7)

    # Final presentation polish and saving
    plt.tight_layout()
    output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'cnn1_training_curves.png')
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"[SUCCESS] High-resolution evaluation curves successfully saved to: {output_path}")

if __name__ == '__main__':
    plot_curves()
