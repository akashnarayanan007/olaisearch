"""Training script for U-Net restoration model.

Usage:
    python backend/ml/restoration/train.py \
        --data-dir data/synthetic \
        --output-dir models/restoration \
        --epochs 50 \
        --batch-size 8 \
        --lr 1e-4
"""
import argparse
from pathlib import Path
import torch
import pytorch_lightning as pl
from pytorch_lightning.callbacks import ModelCheckpoint, EarlyStopping, LearningRateMonitor
from pytorch_lightning.loggers import TensorBoardLogger, MLFlowLogger

from backend.ml.restoration.train_module import RestorationModule
from backend.ml.restoration.dataset import get_dataloaders
from backend.core.logging import setup_logging, get_logger

setup_logging()
logger = get_logger(__name__)


def train(
    data_dir: str,
    output_dir: str = "models/restoration",
    epochs: int = 50,
    batch_size: int = 8,
    lr: float = 1e-4,
    image_size: int = 256,
    num_workers: int = 4,
    loss_type: str = "l1",
    gpus: int = 1,
    seed: int = 42,
):
    """Train U-Net restoration model.

    Args:
        data_dir: Directory containing synthetic training data
        output_dir: Directory to save trained models
        epochs: Number of training epochs
        batch_size: Batch size
        lr: Learning rate
        image_size: Training image size (will be square)
        num_workers: Number of data loading workers
        loss_type: Loss function ("l1" or "l2")
        gpus: Number of GPUs (0 for CPU)
        seed: Random seed
    """
    # Set seed
    pl.seed_everything(seed)

    # Create output directory
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    logger.info(
        "training_started",
        data_dir=data_dir,
        output_dir=output_dir,
        epochs=epochs,
        batch_size=batch_size,
        lr=lr,
        image_size=image_size,
    )

    # Create dataloaders
    train_loader, val_loader = get_dataloaders(
        data_dir=data_dir,
        batch_size=batch_size,
        num_workers=num_workers,
        image_size=(image_size, image_size),
    )

    logger.info(
        "dataloaders_ready",
        train_batches=len(train_loader),
        val_batches=len(val_loader),
    )

    # Create model
    model = RestorationModule(
        n_channels=1,  # Grayscale for now
        n_classes=1,
        learning_rate=lr,
        loss_type=loss_type,
    )

    # Callbacks
    checkpoint_callback = ModelCheckpoint(
        dirpath=output_path / "checkpoints",
        filename="restoration-{epoch:02d}-{val/loss:.4f}-{val/psnr:.2f}",
        monitor="val/psnr",
        mode="max",
        save_top_k=3,
        save_last=True,
    )

    early_stopping = EarlyStopping(
        monitor="val/loss",
        patience=10,
        mode="min",
        verbose=True,
    )

    lr_monitor = LearningRateMonitor(logging_interval="epoch")

    # Logger
    tb_logger = TensorBoardLogger(
        save_dir=output_path / "logs",
        name="restoration",
    )

    # Trainer
    trainer = pl.Trainer(
        max_epochs=epochs,
        accelerator="gpu" if gpus > 0 and torch.cuda.is_available() else "cpu",
        devices=gpus if gpus > 0 and torch.cuda.is_available() else None,
        callbacks=[checkpoint_callback, early_stopping, lr_monitor],
        logger=tb_logger,
        log_every_n_steps=10,
        val_check_interval=1.0,
        precision=16 if gpus > 0 else 32,  # Mixed precision on GPU
    )

    # Train
    logger.info("starting_training")
    trainer.fit(model, train_loader, val_loader)

    # Save best model
    best_model_path = output_path / "best_model.ckpt"
    torch.save(
        {
            "model_state_dict": model.model.state_dict(),
            "hparams": model.hparams,
        },
        best_model_path,
    )

    logger.info(
        "training_complete",
        best_model_path=str(best_model_path),
        best_val_loss=checkpoint_callback.best_model_score,
    )

    print(f"\n✅ Training complete!")
    print(f"   Best model saved to: {best_model_path}")
    print(f"   Best validation PSNR: {checkpoint_callback.best_model_score:.2f} dB")
    print(f"   TensorBoard logs: {tb_logger.log_dir}")


def main():
    parser = argparse.ArgumentParser(description="Train U-Net restoration model")
    parser.add_argument(
        "--data-dir",
        type=str,
        required=True,
        help="Directory containing synthetic training data",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="models/restoration",
        help="Directory to save trained models",
    )
    parser.add_argument("--epochs", type=int, default=50, help="Number of epochs")
    parser.add_argument("--batch-size", type=int, default=8, help="Batch size")
    parser.add_argument("--lr", type=float, default=1e-4, help="Learning rate")
    parser.add_argument("--image-size", type=int, default=256, help="Image size (square)")
    parser.add_argument("--num-workers", type=int, default=4, help="Data loading workers")
    parser.add_argument(
        "--loss-type",
        type=str,
        default="l1",
        choices=["l1", "l2"],
        help="Loss function",
    )
    parser.add_argument("--gpus", type=int, default=1, help="Number of GPUs (0 for CPU)")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")

    args = parser.parse_args()

    train(
        data_dir=args.data_dir,
        output_dir=args.output_dir,
        epochs=args.epochs,
        batch_size=args.batch_size,
        lr=args.lr,
        image_size=args.image_size,
        num_workers=args.num_workers,
        loss_type=args.loss_type,
        gpus=args.gpus,
        seed=args.seed,
    )


if __name__ == "__main__":
    main()
