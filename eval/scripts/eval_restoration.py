"""Evaluation script for restoration models.

Compares:
- No restoration (baseline)
- Classical restoration
- Learned U-Net restoration
- Classical + Learned (combined)

Metrics: PSNR, SSIM on synthetic and real test sets.
"""
import argparse
from pathlib import Path
import torch
import cv2
import numpy as np
from typing import Dict, List, Tuple
import json
from tqdm import tqdm

from backend.ml.restoration.model import UNet
from backend.pipeline.restoration import ClassicalRestoration
from backend.core.logging import setup_logging, get_logger

setup_logging()
logger = get_logger(__name__)


def load_unet_model(checkpoint_path: str, device: str = "cpu") -> UNet:
    """Load trained U-Net model.

    Args:
        checkpoint_path: Path to model checkpoint
        device: Device to load model on

    Returns:
        Loaded UNet model
    """
    checkpoint = torch.load(checkpoint_path, map_location=device)

    # Get model hparams
    hparams = checkpoint.get("hparams", {})
    n_channels = hparams.get("n_channels", 1)
    n_classes = hparams.get("n_classes", 1)

    # Create model
    model = UNet(n_channels=n_channels, n_classes=n_classes)
    model.load_state_dict(checkpoint["model_state_dict"])
    model.to(device)
    model.eval()

    logger.info("unet_model_loaded", checkpoint=checkpoint_path)
    return model


def compute_psnr(img1: np.ndarray, img2: np.ndarray) -> float:
    """Compute PSNR between two images.

    Args:
        img1: First image (H, W) or (H, W, C), uint8 [0, 255]
        img2: Second image

    Returns:
        PSNR in dB
    """
    mse = np.mean((img1.astype(float) - img2.astype(float)) ** 2)
    if mse == 0:
        return float("inf")
    return 20 * np.log10(255.0 / np.sqrt(mse))


def compute_ssim(img1: np.ndarray, img2: np.ndarray) -> float:
    """Compute SSIM between two images.

    Args:
        img1: First image
        img2: Second image

    Returns:
        SSIM value [0, 1]
    """
    from skimage.metrics import structural_similarity

    # Convert to grayscale if needed
    if len(img1.shape) == 3:
        img1 = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY)
        img2 = cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY)

    return structural_similarity(img1, img2, data_range=255)


def evaluate_restoration(
    test_dir: str,
    model_checkpoint: str = None,
    output_file: str = None,
    device: str = "cpu",
) -> Dict[str, any]:
    """Evaluate restoration methods on test set.

    Args:
        test_dir: Directory containing degraded_*.jpg and clean_*.jpg
        model_checkpoint: Path to trained U-Net checkpoint (optional)
        output_file: Path to save results JSON
        device: Device for U-Net inference

    Returns:
        Dictionary of results
    """
    test_path = Path(test_dir)

    # Find test images
    degraded_images = sorted(test_path.glob("degraded_*.jpg"))

    if len(degraded_images) == 0:
        raise ValueError(f"No test images found in {test_dir}")

    logger.info("evaluation_started", num_images=len(degraded_images))

    # Initialize restoration methods
    classical = ClassicalRestoration()

    if model_checkpoint and Path(model_checkpoint).exists():
        unet = load_unet_model(model_checkpoint, device)
        has_unet = True
    else:
        unet = None
        has_unet = False
        logger.warning("no_unet_model", checkpoint=model_checkpoint)

    # Results storage
    results = {
        "no_restoration": {"psnr": [], "ssim": []},
        "classical": {"psnr": [], "ssim": []},
    }

    if has_unet:
        results["learned"] = {"psnr": [], "ssim": []}
        results["combined"] = {"psnr": [], "ssim": []}

    # Evaluate each image
    for degraded_path in tqdm(degraded_images, desc="Evaluating"):
        # Load images
        clean_path = degraded_path.parent / degraded_path.name.replace("degraded_", "clean_")

        if not clean_path.exists():
            logger.warning("clean_image_missing", degraded=str(degraded_path))
            continue

        degraded = cv2.imread(str(degraded_path), cv2.IMREAD_GRAYSCALE)
        clean = cv2.imread(str(clean_path), cv2.IMREAD_GRAYSCALE)

        if degraded is None or clean is None:
            continue

        # 1. No restoration (baseline)
        psnr_none = compute_psnr(degraded, clean)
        ssim_none = compute_ssim(degraded, clean)
        results["no_restoration"]["psnr"].append(psnr_none)
        results["no_restoration"]["ssim"].append(ssim_none)

        # 2. Classical restoration
        restored_classical, _ = classical.restore(degraded, apply_binarization=False)
        psnr_classical = compute_psnr(restored_classical, clean)
        ssim_classical = compute_ssim(restored_classical, clean)
        results["classical"]["psnr"].append(psnr_classical)
        results["classical"]["ssim"].append(ssim_classical)

        # 3. Learned restoration (if model available)
        if has_unet:
            # Preprocess for U-Net
            img_tensor = torch.from_numpy(degraded).float().unsqueeze(0).unsqueeze(0) / 255.0
            img_tensor = (img_tensor - 0.5) / 0.5  # Normalize to [-1, 1]
            img_tensor = img_tensor.to(device)

            # Inference
            with torch.no_grad():
                restored_tensor = unet(img_tensor)

            # Postprocess
            restored_learned = restored_tensor.cpu().squeeze().numpy()
            restored_learned = ((restored_learned * 0.5 + 0.5) * 255).clip(0, 255).astype(np.uint8)

            psnr_learned = compute_psnr(restored_learned, clean)
            ssim_learned = compute_ssim(restored_learned, clean)
            results["learned"]["psnr"].append(psnr_learned)
            results["learned"]["ssim"].append(ssim_learned)

            # 4. Combined (classical + learned)
            # Apply classical first, then learned
            restored_classical_for_unet, _ = classical.restore(degraded, apply_binarization=False)
            img_tensor = torch.from_numpy(restored_classical_for_unet).float().unsqueeze(0).unsqueeze(0) / 255.0
            img_tensor = (img_tensor - 0.5) / 0.5
            img_tensor = img_tensor.to(device)

            with torch.no_grad():
                restored_tensor = unet(img_tensor)

            restored_combined = restored_tensor.cpu().squeeze().numpy()
            restored_combined = ((restored_combined * 0.5 + 0.5) * 255).clip(0, 255).astype(np.uint8)

            psnr_combined = compute_psnr(restored_combined, clean)
            ssim_combined = compute_ssim(restored_combined, clean)
            results["combined"]["psnr"].append(psnr_combined)
            results["combined"]["ssim"].append(ssim_combined)

    # Compute averages
    summary = {}
    for method, metrics in results.items():
        if len(metrics["psnr"]) > 0:
            summary[method] = {
                "psnr_mean": float(np.mean(metrics["psnr"])),
                "psnr_std": float(np.std(metrics["psnr"])),
                "ssim_mean": float(np.mean(metrics["ssim"])),
                "ssim_std": float(np.std(metrics["ssim"])),
                "num_images": len(metrics["psnr"]),
            }

    # Save results
    if output_file:
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w") as f:
            json.dump(summary, f, indent=2)

        logger.info("results_saved", output_file=output_file)

    # Print summary
    print("\n" + "=" * 60)
    print("RESTORATION EVALUATION RESULTS")
    print("=" * 60)
    for method, stats in summary.items():
        print(f"\n{method.upper()}:")
        print(f"  PSNR: {stats['psnr_mean']:.2f} ± {stats['psnr_std']:.2f} dB")
        print(f"  SSIM: {stats['ssim_mean']:.4f} ± {stats['ssim_std']:.4f}")
        print(f"  Images: {stats['num_images']}")
    print("=" * 60 + "\n")

    return summary


def main():
    parser = argparse.ArgumentParser(description="Evaluate restoration methods")
    parser.add_argument(
        "--test-dir",
        type=str,
        required=True,
        help="Directory containing test images",
    )
    parser.add_argument(
        "--model-checkpoint",
        type=str,
        default=None,
        help="Path to trained U-Net checkpoint",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="eval/results/restoration_synthetic.json",
        help="Output JSON file for results",
    )
    parser.add_argument(
        "--device",
        type=str,
        default="cuda" if torch.cuda.is_available() else "cpu",
        help="Device for inference",
    )

    args = parser.parse_args()

    evaluate_restoration(
        test_dir=args.test_dir,
        model_checkpoint=args.model_checkpoint,
        output_file=args.output,
        device=args.device,
    )


if __name__ == "__main__":
    main()
