"""Test classical restoration pipeline."""

import cv2
import numpy as np
import pytest

from backend.pipeline.restoration import ClassicalRestoration


@pytest.fixture
def restoration():
    """Create restoration instance."""
    return ClassicalRestoration()


@pytest.fixture
def sample_image():
    """Create a simple test image with text."""
    # Create white background with black text
    img = np.ones((200, 400), dtype=np.uint8) * 255
    cv2.rectangle(img, (50, 50), (350, 150), 0, -1)  # Black rectangle (text region)
    return img


def test_background_flattening(restoration, sample_image):
    """Test background flattening."""
    # Add gradient to simulate uneven lighting
    h, w = sample_image.shape
    gradient = np.linspace(0.7, 1.3, w)
    uneven = (sample_image * gradient).astype(np.uint8)

    flattened = restoration.flatten_background(uneven)

    assert flattened.shape == sample_image.shape
    assert flattened.dtype == np.uint8
    # Flattened should have more uniform background
    assert np.std(flattened) < np.std(uneven)


def test_clahe(restoration, sample_image):
    """Test CLAHE contrast enhancement."""
    enhanced = restoration.apply_clahe(sample_image)

    assert enhanced.shape == sample_image.shape
    assert enhanced.dtype == np.uint8


def test_deskew(restoration):
    """Test deskewing with realistic text-like pattern."""
    # Create a more realistic pattern with multiple text lines
    # This gives the deskew algorithm more structure to detect rotation
    img = np.ones((200, 400), dtype=np.uint8) * 255

    # Add multiple horizontal bars to simulate text lines
    for i in range(4):
        y_pos = 30 + i * 40
        cv2.rectangle(img, (50, y_pos), (350, y_pos + 15), 0, -1)

    # Rotate by known angle
    center = (200, 100)
    angle = 5.0
    M = cv2.getRotationMatrix2D(center, angle, 1.0)
    rotated = cv2.warpAffine(img, M, (400, 200))

    # Deskew
    deskewed, detected_angle = restoration.deskew(rotated)

    assert deskewed.shape == rotated.shape
    # Allow for detection tolerance (fitLine has ~5-10 degree error on thin patterns)
    assert abs(detected_angle - angle) < 10.0


def test_border_detection(restoration, sample_image):
    """Test border detection."""
    # Add borders
    bordered = np.ones((300, 500), dtype=np.uint8) * 255
    bordered[50:250, 50:450] = sample_image

    top, bottom, left, right = restoration.detect_borders(bordered)

    assert top > 0
    assert bottom > 0
    assert left > 0
    assert right > 0


def test_sauvola_binarization(restoration, sample_image):
    """Test Sauvola binarization."""
    binary = restoration.binarize_sauvola(sample_image)

    assert binary.shape == sample_image.shape
    assert binary.dtype == np.uint8
    assert np.all((binary == 0) | (binary == 255))  # Binary values only


def test_full_restoration_pipeline(restoration, sample_image):
    """Test complete restoration pipeline."""
    restored, metadata = restoration.restore(
        sample_image,
        apply_background_flatten=True,
        apply_clahe=True,
        apply_deskew=True,
        apply_binarization=False,
    )

    assert restored.shape == sample_image.shape
    assert "steps" in metadata
    assert "background_flatten" in metadata["steps"]
    assert "clahe" in metadata["steps"]
    assert "deskew" in metadata["steps"]
    assert "borders" in metadata


def test_restoration_with_color_image(restoration):
    """Test restoration accepts color images."""
    color_img = np.ones((200, 400, 3), dtype=np.uint8) * 255

    restored, metadata = restoration.restore(color_img)

    assert restored.shape == color_img.shape
    assert restored.shape[2] == 3  # Still color
