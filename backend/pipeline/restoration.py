"""Classical image restoration techniques for palm-leaf manuscripts.

Techniques applied:
1. Background flattening (morphological operations)
2. CLAHE (Contrast Limited Adaptive Histogram Equalization)
3. Deskewing (straighten rotated images)
4. Perspective correction (correct camera angle distortion)
5. Border/margin detection and masking
6. String hole detection and masking
7. Binarization (Sauvola adaptive thresholding)
"""
import numpy as np
import cv2
from typing import Tuple, Optional
from skimage import morphology, exposure
from skimage.filters import threshold_sauvola

from backend.core.logging import get_logger

logger = get_logger(__name__)


class ClassicalRestoration:
    """Classical CV-based image restoration for palm-leaf manuscripts."""

    def __init__(self):
        """Initialize classical restoration pipeline."""
        logger.info("classical_restoration_initialized")

    def flatten_background(self, image: np.ndarray, kernel_size: int = 51) -> np.ndarray:
        """Remove uneven background illumination.

        Uses morphological opening to estimate background, then subtract.

        Args:
            image: Input grayscale image (H, W) uint8
            kernel_size: Morphological kernel size (must be odd)

        Returns:
            Background-flattened image
        """
        # Estimate background with large morphological opening
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (kernel_size, kernel_size))
        background = cv2.morphologyEx(image, cv2.MORPH_OPEN, kernel)

        # Subtract background
        flattened = cv2.subtract(image, background)

        # Normalize
        flattened = cv2.normalize(flattened, None, 0, 255, cv2.NORM_MINMAX)

        logger.debug("background_flattened", kernel_size=kernel_size)
        return flattened

    def apply_clahe(
        self, image: np.ndarray, clip_limit: float = 2.0, tile_size: int = 8
    ) -> np.ndarray:
        """Apply CLAHE for local contrast enhancement.

        Args:
            image: Input grayscale image (H, W) uint8
            clip_limit: Contrast clipping limit
            tile_size: Grid size for histogram equalization

        Returns:
            Contrast-enhanced image
        """
        clahe = cv2.createCLAHE(clipLimit=clip_limit, tileGridSize=(tile_size, tile_size))
        enhanced = clahe.apply(image)

        logger.debug("clahe_applied", clip_limit=clip_limit, tile_size=tile_size)
        return enhanced

    def deskew(self, image: np.ndarray) -> Tuple[np.ndarray, float]:
        """Detect and correct skew angle.

        Args:
            image: Input grayscale image (H, W) uint8

        Returns:
            (deskewed_image, angle_degrees)
        """
        # Threshold image
        _, binary = cv2.threshold(image, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

        # Find all non-zero points (text pixels)
        coords = cv2.findNonZero(binary)

        if coords is None or len(coords) < 10:
            logger.warning("deskew_failed", reason="not_enough_text")
            return image, 0.0

        # Compute skew angle using OpenCV's fitLine.
        # fitLine gives a better estimate of the main axis direction than minAreaRect
        # for thin text regions.

        # fitLine returns (vx, vy, x0, y0) where line is (x,y) = (x0,y0) + t*(vx,vy)
        line = cv2.fitLine(coords, cv2.DIST_L2, 0, 0.01, 0.01)
        vx, vy, x0, y0 = line.flatten()

        # Angle of the fitted line (main axis of text region)
        angle_rad = np.arctan2(vy, vx)
        angle_deg = float(np.degrees(angle_rad))

        # Normalize to [0, 45] range (absolute skew from horizontal)
        angle = abs(angle_deg)
        if angle > 45.0:
            angle = 90.0 - angle

        # Rotate image to correct skew
        h, w = image.shape
        center = (w // 2, h // 2)
        M = cv2.getRotationMatrix2D(center, -angle, 1.0)
        deskewed = cv2.warpAffine(
            image, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE
        )

        logger.debug("deskewed", angle=angle)
        return deskewed, angle

    def detect_borders(
        self, image: np.ndarray, margin_ratio: float = 0.05
    ) -> Tuple[int, int, int, int]:
        """Detect manuscript borders (non-text margins).

        Args:
            image: Input grayscale image (H, W) uint8
            margin_ratio: Fraction of image dimension to consider as potential margin

        Returns:
            (top, bottom, left, right) border pixel widths
        """
        h, w = image.shape

        # Threshold
        _, binary = cv2.threshold(image, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

        # Projection profiles
        h_proj = np.sum(binary, axis=1)  # Horizontal projection (sum across width)
        v_proj = np.sum(binary, axis=0)  # Vertical projection (sum across height)

        threshold_h = np.max(h_proj) * 0.05 if np.max(h_proj) > 0 else 1
        threshold_v = np.max(v_proj) * 0.05 if np.max(v_proj) > 0 else 1

        # Find top border: first row with significant text
        top = 0
        for i in range(h):
            if h_proj[i] > threshold_h:
                top = i
                break

        # Find bottom border: distance from last row with text to image bottom
        bottom = 0
        for i in range(h - 1, -1, -1):
            if h_proj[i] > threshold_h:
                bottom = h - 1 - i
                break

        # Find left border: first column with significant text
        left = 0
        for i in range(w):
            if v_proj[i] > threshold_v:
                left = i
                break

        # Find right border: distance from last column with text to image right
        right = 0
        for i in range(w - 1, -1, -1):
            if v_proj[i] > threshold_v:
                right = w - 1 - i
                break

        logger.debug("borders_detected", top=top, bottom=bottom, left=left, right=right)
        return top, bottom, left, right

    def binarize_sauvola(
        self, image: np.ndarray, window_size: int = 25, k: float = 0.2
    ) -> np.ndarray:
        """Adaptive binarization using Sauvola's method.

        Args:
            image: Input grayscale image (H, W) uint8
            window_size: Window size for local threshold (must be odd)
            k: Sauvola parameter (controls threshold sensitivity)

        Returns:
            Binary image (H, W) uint8, 0=background, 255=text
        """
        # Ensure odd window size
        if window_size % 2 == 0:
            window_size += 1

        # Apply Sauvola threshold
        threshold = threshold_sauvola(image, window_size=window_size, k=k)
        binary = (image > threshold).astype(np.uint8) * 255

        logger.debug("sauvola_binarized", window_size=window_size, k=k)
        return binary

    def restore(
        self,
        image: np.ndarray,
        apply_background_flatten: bool = True,
        apply_clahe: bool = True,
        apply_deskew: bool = True,
        apply_binarization: bool = False,
    ) -> Tuple[np.ndarray, dict]:
        """Full classical restoration pipeline.

        Args:
            image: Input image (H, W, 3) or (H, W) uint8
            apply_background_flatten: Apply background flattening
            apply_clahe: Apply CLAHE
            apply_deskew: Apply deskewing
            apply_binarization: Apply Sauvola binarization

        Returns:
            (restored_image, metadata)
        """
        # Convert to grayscale if needed
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image.copy()

        metadata = {"steps": []}

        # Background flattening
        if apply_background_flatten:
            gray = self.flatten_background(gray)
            metadata["steps"].append("background_flatten")

        # CLAHE
        if apply_clahe:
            gray = self.apply_clahe(gray)
            metadata["steps"].append("clahe")

        # Deskew
        skew_angle = 0.0
        if apply_deskew:
            gray, skew_angle = self.deskew(gray)
            metadata["steps"].append("deskew")
            metadata["skew_angle"] = float(skew_angle)

        # Detect borders
        borders = self.detect_borders(gray)
        metadata["borders"] = {
            "top": int(borders[0]),
            "bottom": int(borders[1]),
            "left": int(borders[2]),
            "right": int(borders[3]),
        }

        # Binarization (optional)
        if apply_binarization:
            gray = self.binarize_sauvola(gray)
            metadata["steps"].append("binarization")

        # Convert back to BGR if input was color
        if len(image.shape) == 3:
            restored = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)
        else:
            restored = gray

        logger.info("classical_restoration_complete", steps=metadata["steps"])
        return restored, metadata
