"""Palm-leaf texture generation using Perlin noise."""
import numpy as np
from typing import Tuple
from scipy.ndimage import gaussian_filter


def generate_perlin_noise_2d(
    shape: Tuple[int, int], res: Tuple[int, int], seed: int = 0
) -> np.ndarray:
    """Generate 2D Perlin noise.

    Args:
        shape: Output shape (height, width)
        res: Resolution/scale (determines noise frequency)
        seed: Random seed for reproducibility

    Returns:
        Normalized noise array [0, 1]
    """
    rng = np.random.default_rng(seed)

    def f(t):
        return 6 * t**5 - 15 * t**4 + 10 * t**3

    # Cell dimensions
    cell_w, cell_h = shape[1] / res[1], shape[0] / res[0]

    # Create grid of points (y, x) for interpolation
    y, x = np.mgrid[0:shape[0], 0:shape[1]]
    x_norm = x / shape[1] * res[1]
    y_norm = y / shape[0] * res[0]

    # Integer cell indices
    x0 = np.floor(x_norm).astype(int)
    y0 = np.floor(y_norm).astype(int)
    x1 = x0 + 1
    y1 = y0 + 1

    # Fractional part within cell
    fx = x_norm - x0
    fy = y_norm - y0

    # Gradients at grid points (res[0]+1) x (res[1]+1)
    angles = 2 * np.pi * rng.random((res[0] + 1, res[1] + 1))
    gradients_x = np.cos(angles)
    gradients_y = np.sin(angles)

    # Clamp indices to valid range
    x1 = np.clip(x1, 0, res[1])
    y1 = np.clip(y1, 0, res[0])

    # Dot products at four corners
    g00_x = gradients_x[y0, x0]
    g00_y = gradients_y[y0, x0]
    g00 = g00_x * fx + g00_y * fy

    g10_x = gradients_x[y0, x1]
    g10_y = gradients_y[y0, x1]
    g10 = (g10_x * (fx - 1)) + g10_y * fy

    g01_x = gradients_x[y1, x0]
    g01_y = gradients_y[y1, x0]
    g01 = g01_x * fx + (g01_y * (fy - 1))

    g11_x = gradients_x[y1, x1]
    g11_y = gradients_y[y1, x1]
    g11 = (g11_x * (fx - 1)) + (g11_y * (fy - 1))

    # Smooth interpolation
    sx = f(fx)
    sy = f(fy)

    # Interpolate
    nx0 = g00 * (1 - sx) + g10 * sx
    nx1 = g01 * (1 - sx) + g11 * sx
    noise = nx0 * (1 - sy) + nx1 * sy

    return noise


def generate_palm_leaf_texture(
    height: int = 1000,
    width: int = 3000,
    seed: int = 42,
) -> np.ndarray:
    """Generate realistic palm-leaf texture with organic variation.

    Palm leaves have:
    - Longitudinal fiber patterns (vertical streaks)
    - Yellowing/browning age gradients
    - Natural color variation
    - Subtle surface texture

    Args:
        height: Texture height in pixels
        width: Texture width in pixels
        seed: Random seed for reproducibility

    Returns:
        RGB texture image (H, W, 3) uint8, range [0, 255]
    """
    rng = np.random.default_rng(seed)

    # Base color: aged palm leaf (yellowish-brown)
    base_r = 220 + rng.integers(-10, 10)
    base_g = 200 + rng.integers(-10, 10)
    base_b = 150 + rng.integers(-10, 10)

    # Create base texture with multiple noise octaves
    texture = np.zeros((height, width))

    # Coarse noise (overall variation)
    texture += 0.5 * generate_perlin_noise_2d((height, width), (4, 12), seed)

    # Medium noise (regional variation)
    texture += 0.3 * generate_perlin_noise_2d((height, width), (8, 24), seed + 1)

    # Fine noise (surface detail)
    texture += 0.2 * generate_perlin_noise_2d((height, width), (16, 48), seed + 2)

    # Normalize to [0, 1]
    texture = (texture - texture.min()) / (texture.max() - texture.min())

    # Add vertical fiber lines (palm leaves have longitudinal fibers)
    fiber_frequency = width // 50  # About 50 fibers across the width
    x = np.arange(width)
    fibers = np.sin(2 * np.pi * x / fiber_frequency * rng.uniform(0.9, 1.1))
    fibers = fibers * 0.05  # Subtle effect
    fiber_pattern = np.repeat(fibers[np.newaxis, :], height, axis=0)
    texture += fiber_pattern

    # Age gradient (darker toward edges, yellower in center)
    y_gradient = np.linspace(0, 1, height)
    y_gradient = 1 - 0.3 * (y_gradient**2 + (1 - y_gradient)**2)  # U-shaped darkening
    y_gradient = gaussian_filter(y_gradient, sigma=height / 20)  # Smooth
    age_mask = np.repeat(y_gradient[:, np.newaxis], width, axis=1)

    # Apply age gradient
    texture = texture * age_mask + (1 - age_mask) * 0.7

    # Clip to [0, 1]
    texture = np.clip(texture, 0, 1)

    # Convert to RGB with base color
    texture_rgb = np.zeros((height, width, 3), dtype=np.uint8)

    # R channel: yellow-brown
    texture_rgb[:, :, 0] = (base_r * texture).astype(np.uint8)

    # G channel: slightly less
    texture_rgb[:, :, 1] = (base_g * texture * 0.95).astype(np.uint8)

    # B channel: much less (brownish)
    texture_rgb[:, :, 2] = (base_b * texture * 0.85).astype(np.uint8)

    return texture_rgb
