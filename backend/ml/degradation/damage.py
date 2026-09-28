"""Damage models for palm-leaf degradation.

Physically-motivated damage that occurs on real palm-leaf manuscripts:
- Water stains from humidity/flooding
- Ink fading due to age
- Ink bleed from moisture
- String holes (manuscripts bound with thread)
- Insect holes
- Cracks and tears
- Fungal spots
- Uneven lighting
- Camera blur and noise
"""
import numpy as np
import cv2
from scipy.ndimage import gaussian_filter, binary_dilation
from typing import Tuple, List


def apply_water_stains(
    image: np.ndarray,
    rng: np.random.Generator,
    num_stains: int = 3,
    severity: float = 0.3,
) -> np.ndarray:
    """Apply organic water stain patterns.

    Args:
        image: Input image (H, W, 3) uint8
        rng: Random number generator for reproducibility
        num_stains: Number of stain regions
        severity: Stain darkness [0, 1]

    Returns:
        Stained image
    """
    h, w = image.shape[:2]
    result = image.copy().astype(np.float32)

    for _ in range(num_stains):
        # Random stain center
        cx = rng.integers(0, w)
        cy = rng.integers(0, h)

        # Random stain size
        radius = rng.integers(h // 10, h // 3)

        # Create blob mask
        y, x = np.ogrid[:h, :w]
        dist = np.sqrt((x - cx)**2 + (y - cy)**2)

        # Soft falloff
        mask = np.exp(-(dist / radius)**2)

        # Irregular shape (use noise)
        noise = rng.random((h, w))
        noise = gaussian_filter(noise, sigma=radius / 5)
        mask = mask * (0.5 + 0.5 * noise)

        # Apply brownish stain
        stain_color = np.array([160, 140, 100], dtype=np.float32)  # Brown
        for c in range(3):
            result[:, :, c] = (
                result[:, :, c] * (1 - mask * severity) +
                stain_color[c] * mask * severity
            )

    return np.clip(result, 0, 255).astype(np.uint8)


def apply_ink_fade(
    image: np.ndarray,
    text_mask: np.ndarray,
    rng: np.random.Generator,
    fade_factor: float = 0.4,
) -> np.ndarray:
    """Fade ink due to age.

    Args:
        image: Input image (H, W, 3) uint8
        text_mask: Binary mask of text regions (H, W) bool
        rng: Random generator
        fade_factor: How much to fade [0, 1]

    Returns:
        Faded image
    """
    result = image.copy().astype(np.float32)

    # Get background color (median of non-text regions)
    bg_color = np.median(result[~text_mask], axis=0)

    # Create variable fade mask (some areas fade more)
    h, w = image.shape[:2]
    fade_variation = rng.random((h, w))
    fade_variation = gaussian_filter(fade_variation, sigma=min(h, w) / 20)
    fade_variation = (fade_variation - fade_variation.min()) / (fade_variation.max() - fade_variation.min())

    # Apply fade only to text regions
    fade_mask = text_mask.astype(np.float32) * fade_variation * fade_factor

    for c in range(3):
        result[:, :, c] = (
            result[:, :, c] * (1 - fade_mask) +
            bg_color[c] * fade_mask
        )

    return np.clip(result, 0, 255).astype(np.uint8)


def apply_ink_bleed(
    image: np.ndarray,
    text_mask: np.ndarray,
    rng: np.random.Generator,
    blur_sigma: float = 1.5,
) -> np.ndarray:
    """Apply ink bleeding effect from moisture.

    Args:
        image: Input image (H, W, 3) uint8
        text_mask: Binary mask of text regions
        rng: Random generator
        blur_sigma: Gaussian blur sigma for bleeding

    Returns:
        Image with ink bleed
    """
    result = image.copy().astype(np.float32)

    # Blur text regions to simulate bleed
    text_only = result * text_mask[:, :, np.newaxis]
    text_blurred = gaussian_filter(text_only, sigma=(blur_sigma, blur_sigma, 0))

    # Blend back
    result = np.where(text_mask[:, :, np.newaxis], text_blurred, result)

    return np.clip(result, 0, 255).astype(np.uint8)


def apply_holes(
    image: np.ndarray,
    bboxes: List[Tuple[int, int, int, int]],
    rng: np.random.Generator,
    num_holes: int = 5,
    hole_type: str = "mixed",
) -> Tuple[np.ndarray, List[Tuple[int, int, int, int]]]:
    """Apply insect holes and string holes.

    Args:
        image: Input image (H, W, 3) uint8
        bboxes: Text bounding boxes [(x, y, w, h), ...]
        rng: Random generator
        num_holes: Number of holes
        hole_type: "string", "insect", or "mixed"

    Returns:
        (damaged_image, updated_bboxes)
    """
    h, w = image.shape[:2]
    result = image.copy()

    # Get background color
    bg_color = np.median(result, axis=(0, 1)).astype(np.uint8)

    for _ in range(num_holes):
        if hole_type == "mixed":
            is_string = rng.random() > 0.7
        else:
            is_string = hole_type == "string"

        if is_string:
            # String holes: circular, near edges, larger
            if rng.random() > 0.5:
                cx = rng.integers(w // 10, w // 5)  # Left edge
            else:
                cx = rng.integers(4 * w // 5, 9 * w // 10)  # Right edge
            cy = rng.integers(h // 4, 3 * h // 4)
            radius = rng.integers(h // 40, h // 20)
        else:
            # Insect holes: smaller, random locations
            cx = rng.integers(0, w)
            cy = rng.integers(0, h)
            radius = rng.integers(h // 100, h // 50)

        # Create hole mask
        y, x = np.ogrid[:h, :w]
        dist = np.sqrt((x - cx)**2 + (y - cy)**2)
        hole_mask = dist <= radius

        # Make irregular edge
        hole_mask = binary_dilation(hole_mask, iterations=rng.integers(1, 3))

        # Fill with background color (as if leaf is torn away)
        result[hole_mask] = bg_color

    # Note: bboxes are not updated in this simplified version
    # In full implementation, would need to check overlap and mark affected bboxes
    return result, bboxes


def apply_camera_effects(
    image: np.ndarray,
    rng: np.random.Generator,
    blur_sigma: float = 0.8,
    noise_stddev: float = 5.0,
) -> np.ndarray:
    """Apply camera blur and noise.

    Args:
        image: Input image (H, W, 3) uint8
        rng: Random generator
        blur_sigma: Gaussian blur sigma
        noise_stddev: Noise standard deviation

    Returns:
        Degraded image
    """
    result = image.copy().astype(np.float32)

    # Apply blur
    if blur_sigma > 0:
        result = cv2.GaussianBlur(result, (0, 0), blur_sigma)

    # Add Gaussian noise
    if noise_stddev > 0:
        noise = rng.normal(0, noise_stddev, result.shape)
        result = result + noise

    return np.clip(result, 0, 255).astype(np.uint8)


def apply_uneven_lighting(
    image: np.ndarray,
    rng: np.random.Generator,
    intensity: float = 0.3,
) -> np.ndarray:
    """Apply uneven lighting gradient.

    Args:
        image: Input image (H, W, 3) uint8
        rng: Random generator
        intensity: Lighting variation intensity [0, 1]

    Returns:
        Image with lighting gradient
    """
    h, w = image.shape[:2]
    result = image.copy().astype(np.float32)

    # Random gradient direction
    angle = rng.uniform(0, 2 * np.pi)

    # Create gradient
    y, x = np.mgrid[0:h, 0:w]
    gradient = np.sin(angle) * x / w + np.cos(angle) * y / h
    gradient = (gradient - gradient.min()) / (gradient.max() - gradient.min())

    # Smooth
    gradient = gaussian_filter(gradient, sigma=min(h, w) / 10)

    # Apply multiplicative lighting
    lighting = 1 + intensity * (gradient - 0.5)
    lighting = lighting[:, :, np.newaxis]

    result = result * lighting

    return np.clip(result, 0, 255).astype(np.uint8)
