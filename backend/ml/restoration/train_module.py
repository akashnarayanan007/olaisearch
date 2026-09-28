"""PyTorch Lightning module for U-Net restoration training."""
import torch
import torch.nn as nn
import torch.nn.functional as F
import pytorch_lightning as pl
from torchmetrics.image import PeakSignalNoiseRatio, StructuralSimilarityIndexMeasure
from typing import Tuple, Dict, Any

from backend.ml.restoration.model import UNet
from backend.core.logging import get_logger

logger = get_logger(__name__)


class RestorationModule(pl.LightningModule):
    """PyTorch Lightning module for image restoration training."""

    def __init__(
        self,
        n_channels: int = 1,
        n_classes: int = 1,
        learning_rate: float = 1e-4,
        loss_type: str = "l1",  # "l1", "l2", or "perceptual"
    ):
        """Initialize restoration module.

        Args:
            n_channels: Number of input channels (1 for grayscale, 3 for RGB)
            n_classes: Number of output channels
            learning_rate: Learning rate
            loss_type: Loss function type
        """
        super().__init__()
        self.save_hyperparameters()

        # Model
        self.model = UNet(n_channels=n_channels, n_classes=n_classes)

        # Loss function
        if loss_type == "l1":
            self.criterion = nn.L1Loss()
        elif loss_type == "l2":
            self.criterion = nn.MSELoss()
        else:
            raise ValueError(f"Unknown loss type: {loss_type}")

        # Metrics
        self.psnr = PeakSignalNoiseRatio(data_range=2.0)  # Input range [-1, 1]
        self.ssim = StructuralSimilarityIndexMeasure(data_range=2.0)

        logger.info(
            "restoration_module_initialized",
            n_channels=n_channels,
            loss_type=loss_type,
            learning_rate=learning_rate,
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Forward pass.

        Args:
            x: Input tensor (B, C, H, W)

        Returns:
            Restored tensor (B, C, H, W)
        """
        return self.model(x)

    def _compute_loss_and_metrics(
        self,
        batch: Tuple[torch.Tensor, torch.Tensor],
        stage: str,
    ) -> Dict[str, torch.Tensor]:
        """Compute loss and metrics for a batch.

        Args:
            batch: (degraded, clean) tuple
            stage: "train" or "val"

        Returns:
            Dictionary of losses and metrics
        """
        degraded, clean = batch

        # Forward pass
        restored = self(degraded)

        # Compute loss
        loss = self.criterion(restored, clean)

        # Compute metrics (only on validation to save time)
        if stage == "val":
            psnr = self.psnr(restored, clean)
            ssim = self.ssim(restored, clean)
        else:
            psnr = torch.tensor(0.0)
            ssim = torch.tensor(0.0)

        return {
            "loss": loss,
            "psnr": psnr,
            "ssim": ssim,
        }

    def training_step(self, batch: Tuple[torch.Tensor, torch.Tensor], batch_idx: int) -> torch.Tensor:
        """Training step.

        Args:
            batch: (degraded, clean) tuple
            batch_idx: Batch index

        Returns:
            Loss tensor
        """
        metrics = self._compute_loss_and_metrics(batch, "train")

        # Log metrics
        self.log("train/loss", metrics["loss"], on_step=True, on_epoch=True, prog_bar=True)

        return metrics["loss"]

    def validation_step(self, batch: Tuple[torch.Tensor, torch.Tensor], batch_idx: int) -> None:
        """Validation step.

        Args:
            batch: (degraded, clean) tuple
            batch_idx: Batch index
        """
        metrics = self._compute_loss_and_metrics(batch, "val")

        # Log metrics
        self.log("val/loss", metrics["loss"], on_step=False, on_epoch=True, prog_bar=True)
        self.log("val/psnr", metrics["psnr"], on_step=False, on_epoch=True, prog_bar=True)
        self.log("val/ssim", metrics["ssim"], on_step=False, on_epoch=True, prog_bar=True)

        # Log sample images (first batch only)
        if batch_idx == 0:
            self._log_images(batch)

    def _log_images(self, batch: Tuple[torch.Tensor, torch.Tensor], num_images: int = 4) -> None:
        """Log sample images to TensorBoard/MLflow.

        Args:
            batch: (degraded, clean) tuple
            num_images: Number of images to log
        """
        degraded, clean = batch
        restored = self(degraded)

        # Take first few images
        degraded = degraded[:num_images]
        clean = clean[:num_images]
        restored = restored[:num_images]

        # Denormalize from [-1, 1] to [0, 1] for visualization
        degraded = (degraded + 1) / 2
        clean = (clean + 1) / 2
        restored = (restored + 1) / 2
        restored = torch.clamp(restored, 0, 1)

        # Log as grid
        if self.logger:
            self.logger.experiment.add_images(
                "val/degraded",
                degraded,
                self.current_epoch,
            )
            self.logger.experiment.add_images(
                "val/clean",
                clean,
                self.current_epoch,
            )
            self.logger.experiment.add_images(
                "val/restored",
                restored,
                self.current_epoch,
            )

    def configure_optimizers(self) -> Dict[str, Any]:
        """Configure optimizers and schedulers.

        Returns:
            Optimizer and scheduler configuration
        """
        optimizer = torch.optim.Adam(
            self.parameters(),
            lr=self.hparams.learning_rate,
        )

        scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
            optimizer,
            mode="min",
            factor=0.5,
            patience=5,
            verbose=True,
        )

        return {
            "optimizer": optimizer,
            "lr_scheduler": {
                "scheduler": scheduler,
                "monitor": "val/loss",
            },
        }


if __name__ == "__main__":
    # Test module
    module = RestorationModule(n_channels=1, n_classes=1)

    # Dummy batch
    degraded = torch.randn(2, 1, 256, 256)
    clean = torch.randn(2, 1, 256, 256)
    batch = (degraded, clean)

    # Forward
    loss = module.training_step(batch, 0)
    print(f"Loss: {loss.item():.4f}")

    # Count parameters
    params = sum(p.numel() for p in module.parameters())
    print(f"Parameters: {params:,}")
