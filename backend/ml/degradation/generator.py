"""Main palm-leaf degradation generator.

Generates synthetic palm-leaf manuscript images with:
1. Realistic palm-leaf texture (Perlin noise)
2. Handwriting-style text rendering with elastic distortion
3. Physically-motivated damage layers
4. Perfect labels (degraded, clean, text, bboxes)
"""
from pathlib import Path
from typing import Any

import cv2
import numpy as np
import yaml
from PIL import Image, ImageDraw, ImageFont
from scipy.ndimage import gaussian_filter as scipy_gaussian_filter
from scipy.ndimage import map_coordinates

from backend.core.logging import get_logger
from backend.ml.degradation import damage
from backend.ml.degradation.textures import generate_palm_leaf_texture

logger = get_logger(__name__)


class PalmLeafDegradationGenerator:
    """Generate synthetic degraded palm-leaf manuscripts."""

    def __init__(self, config_path: str | None = None):
        """Initialize generator.

        Args:
            config_path: Path to YAML config file. Uses default if None.
        """
        if config_path is None:
            config_path = Path(__file__).parent / "config.yaml"

        with open(config_path) as f:
            self.config = yaml.safe_load(f)

        logger.info("degradation_generator_initialized", config=config_path)

    def _sample_range(self, value: Any, rng: np.random.Generator) -> Any:
        """Sample from a range or return value.

        Args:
            value: Single value or [min, max] range
            rng: Random generator

        Returns:
            Sampled value
        """
        if isinstance(value, list) and len(value) == 2:
            return rng.uniform(value[0], value[1])
        return value

    def _elastic_distortion(
        self,
        image: np.ndarray,
        alpha: float,
        sigma: float,
        rng: np.random.Generator,
    ) -> np.ndarray:
        """Apply elastic distortion to simulate handwriting variation.

        Args:
            image: Input image
            alpha: Distortion strength
            sigma: Gaussian filter sigma
            rng: Random generator

        Returns:
            Distorted image
        """
        shape = image.shape[:2]

        # Random displacement fields
        dx = scipy_gaussian_filter((rng.random(shape) * 2 - 1), sigma) * alpha
        dy = scipy_gaussian_filter((rng.random(shape) * 2 - 1), sigma) * alpha

        # Meshgrid
        y, x = np.mgrid[0:shape[0], 0:shape[1]]
        indices = np.reshape(y + dy, (-1, 1)), np.reshape(x + dx, (-1, 1))

        # Apply distortion to each channel
        if len(image.shape) == 3:
            distorted = np.zeros_like(image)
            for i in range(image.shape[2]):
                distorted[:, :, i] = map_coordinates(
                    image[:, :, i], indices, order=1, mode='reflect'
                ).reshape(shape)
        else:
            distorted = map_coordinates(image, indices, order=1, mode='reflect').reshape(shape)

        return distorted

    def render_text_on_texture(
        self,
        text_lines: list[str],
        texture: np.ndarray,
        font_path: str | None = None,
        seed: int = 42,
    ) -> tuple[np.ndarray, np.ndarray, list[dict[str, int]]]:
        """Render text on palm-leaf texture with handwriting-style fonts.

        Args:
            text_lines: List of text lines to render
            texture: Background texture (H, W, 3) uint8
            font_path: Path to handwriting-style TTF font
            seed: Random seed

        Returns:
            (composite_image, text_mask, bounding_boxes)
            - composite: texture with text rendered (H, W, 3) uint8
            - text_mask: binary mask of text regions (H, W) bool
            - bboxes: [{x, y, width, height, text, line_idx}, ...]
        """
        rng = np.random.default_rng(seed)
        h, w = texture.shape[:2]

        # Create PIL image from texture
        pil_texture = Image.fromarray(texture)
        draw = ImageDraw.Draw(pil_texture)

        # Load font (handwriting-style if provided, else default)
        cfg = self.config['text_rendering']
        font_size = int(self._sample_range(cfg['font_size'], rng))

        try:
            if font_path and Path(font_path).exists():
                font = ImageFont.truetype(font_path, font_size)
            else:
                # Fallback to system font
                font = ImageFont.truetype("arial.ttf", font_size)
        except Exception:
            font = ImageFont.load_default()
            logger.warning("font_load_failed", using="default")

        # Render text lines
        bboxes = []
        text_mask = np.zeros((h, w), dtype=bool)

        y_pos = cfg['margin_top']
        line_spacing = int(self._sample_range(cfg['line_spacing'], rng))

        for line_idx, line in enumerate(text_lines):
            if not line.strip():
                continue

            # Get text bounding box
            bbox = draw.textbbox((cfg['margin_left'], y_pos), line, font=font)
            x1, y1, x2, y2 = bbox

            # Draw text
            text_color = tuple(cfg['text_color'])
            draw.text((cfg['margin_left'], y_pos), line, fill=text_color, font=font)

            # Store bbox
            bboxes.append({
                'x': x1,
                'y': y1,
                'width': x2 - x1,
                'height': y2 - y1,
                'text': line,
                'line_idx': line_idx,
            })

            # Update mask
            text_mask[y1:y2, x1:x2] = True

            y_pos += line_spacing

            # Stop if we exceed image height
            if y_pos > h - cfg['margin_top']:
                logger.warning("text_overflow", num_lines_rendered=line_idx + 1)
                break

        # Convert back to numpy
        composite = np.array(pil_texture)

        # Apply elastic distortion if enabled
        if cfg.get('elastic_distortion', False):
            alpha = self._sample_range(cfg['distortion_alpha'], rng)
            sigma = self._sample_range(cfg['distortion_sigma'], rng)
            composite = self._elastic_distortion(composite, alpha, sigma, rng)

        return composite, text_mask, bboxes

    def generate(
        self,
        text_lines: list[str],
        seed: int = 42,
        level: str = "medium",
        font_path: str | None = None,
    ) -> dict[str, Any]:
        """Generate a complete degraded palm-leaf manuscript.

        Args:
            text_lines: List of text lines
            seed: Random seed for reproducibility
            level: Degradation level ("clean", "light", "medium", "heavy")
            font_path: Path to handwriting-style font

        Returns:
            Dict with keys:
            - 'degraded': Degraded image (H, W, 3) uint8
            - 'clean': Clean composite (text on texture) (H, W, 3) uint8
            - 'texture': Pure texture (H, W, 3) uint8
            - 'text_mask': Binary text mask (H, W) bool
            - 'bboxes': List of bounding boxes with text
            - 'metadata': Generation metadata
        """
        rng = np.random.default_rng(seed)

        # Generate texture
        tex_cfg = self.config['texture']
        texture = generate_palm_leaf_texture(
            height=tex_cfg['height'],
            width=tex_cfg['width'],
            seed=seed,
        )

        # Render text
        clean, text_mask, bboxes = self.render_text_on_texture(
            text_lines, texture, font_path, seed
        )

        # Apply degradation
        degraded = clean.copy()

        # Get level-specific config
        level_overrides = self.config['levels'].get(level, {})
        dmg_cfg = self.config['damage'].copy()

        # Merge level overrides
        for key, overrides in level_overrides.items():
            if key in dmg_cfg:
                dmg_cfg[key].update(overrides)

        # Apply each damage model
        applied_damage = []

        # Water stains
        if dmg_cfg['water_stains']['enabled'] and rng.random() < dmg_cfg['water_stains']['probability']:
            num_stains = int(self._sample_range(dmg_cfg['water_stains']['num_stains'], rng))
            severity = self._sample_range(dmg_cfg['water_stains']['severity'], rng)
            degraded = damage.apply_water_stains(degraded, rng, num_stains, severity)
            applied_damage.append('water_stains')

        # Ink fade
        if dmg_cfg['ink_fade']['enabled'] and rng.random() < dmg_cfg['ink_fade']['probability']:
            fade_factor = self._sample_range(dmg_cfg['ink_fade']['fade_factor'], rng)
            degraded = damage.apply_ink_fade(degraded, text_mask, rng, fade_factor)
            applied_damage.append('ink_fade')

        # Ink bleed
        if dmg_cfg['ink_bleed']['enabled'] and rng.random() < dmg_cfg['ink_bleed']['probability']:
            blur_sigma = self._sample_range(dmg_cfg['ink_bleed']['blur_sigma'], rng)
            degraded = damage.apply_ink_bleed(degraded, text_mask, rng, blur_sigma)
            applied_damage.append('ink_bleed')

        # Holes
        if dmg_cfg['holes']['enabled'] and rng.random() < dmg_cfg['holes']['probability']:
            num_holes = int(self._sample_range(dmg_cfg['holes']['num_holes'], rng))
            hole_type = dmg_cfg['holes']['hole_type']
            degraded, bboxes = damage.apply_holes(degraded, bboxes, rng, num_holes, hole_type)
            applied_damage.append('holes')

        # Uneven lighting
        if dmg_cfg['uneven_lighting']['enabled'] and rng.random() < dmg_cfg['uneven_lighting']['probability']:
            intensity = self._sample_range(dmg_cfg['uneven_lighting']['intensity'], rng)
            degraded = damage.apply_uneven_lighting(degraded, rng, intensity)
            applied_damage.append('uneven_lighting')

        # Camera effects (usually always applied)
        if dmg_cfg['camera_effects']['enabled'] and rng.random() < dmg_cfg['camera_effects']['probability']:
            blur_sigma = self._sample_range(dmg_cfg['camera_effects']['blur_sigma'], rng)
            noise_stddev = self._sample_range(dmg_cfg['camera_effects']['noise_stddev'], rng)
            degraded = damage.apply_camera_effects(degraded, rng, blur_sigma, noise_stddev)
            applied_damage.append('camera_effects')

        result = {
            'degraded': degraded,
            'clean': clean,
            'texture': texture,
            'text_mask': text_mask,
            'bboxes': bboxes,
            'metadata': {
                'seed': seed,
                'level': level,
                'applied_damage': applied_damage,
                'num_lines': len(bboxes),
                'image_shape': degraded.shape,
            }
        }

        logger.info(
            "manuscript_generated",
            seed=seed,
            level=level,
            num_lines=len(bboxes),
            damage=applied_damage,
        )

        return result


# CLI interface
if __name__ == "__main__":
    import argparse
    import json
    from pathlib import Path

    parser = argparse.ArgumentParser(description="Generate synthetic palm-leaf manuscripts")
    parser.add_argument("--count", type=int, default=10, help="Number of samples to generate")
    parser.add_argument("--output", type=str, default="data/synthetic", help="Output directory")
    parser.add_argument("--level", type=str, default="medium", choices=["clean", "light", "medium", "heavy"])
    parser.add_argument("--seed", type=int, default=42, help="Base random seed")

    args = parser.parse_args()

    # Sample Tamil text (you would load this from a corpus)
    sample_texts = [
        ["தமிழ் கையெழுத்து பிரதி", "பழைய இலக்கியம்"],
        ["பனை ஓலை நூல்", "வரலாற்று ஆவணம்"],
    ]

    # Create output directory
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Generate
    generator = PalmLeafDegradationGenerator()

    for i in range(args.count):
        text = sample_texts[i % len(sample_texts)]
        seed = args.seed + i
        sample_dir = output_dir / f"sample_{i:04d}"

        # Create sample directory
        sample_dir.mkdir(parents=True, exist_ok=True)

        result = generator.generate(text, seed=seed, level=args.level)

        # Save images to sample directory
        cv2.imwrite(str(sample_dir / "degraded.jpg"), result['degraded'])
        cv2.imwrite(str(sample_dir / "clean.jpg"), result['clean'])

        # Save labels
        labels = {
            'text': [bbox['text'] for bbox in result['bboxes']],
            'bboxes': result['bboxes'],
            'metadata': result['metadata'],
        }
        with open(sample_dir / "labels.json", 'w', encoding='utf-8') as f:
            json.dump(labels, f, ensure_ascii=False, indent=2)

        print(f"Generated sample {i+1}/{args.count}")

    print(f"\n✅ Generated {args.count} samples in {output_dir}")
