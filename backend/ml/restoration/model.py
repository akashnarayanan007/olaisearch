"""U-Net architecture for image restoration.

Based on the original U-Net paper (Ronneberger et al., 2015) but adapted
for palm-leaf manuscript restoration:
- Input: Degraded grayscale/color image
- Output: Restored image (same size)
- Skip connections for fine detail preservation
"""
import torch
import torch.nn as nn
import torch.nn.functional as F


class DoubleConv(nn.Module):
    """Two consecutive conv layers with BN and ReLU."""

    def __init__(self, in_channels: int, out_channels: int):
        super().__init__()
        self.conv = nn.Sequential(
            nn.Conv2d(in_channels, out_channels, kernel_size=3, padding=1, bias=False),
            nn.BatchNorm2d(out_channels),
            nn.ReLU(inplace=True),
            nn.Conv2d(out_channels, out_channels, kernel_size=3, padding=1, bias=False),
            nn.BatchNorm2d(out_channels),
            nn.ReLU(inplace=True),
        )

    def forward(self, x):
        return self.conv(x)


class Down(nn.Module):
    """Downsampling block: maxpool + double conv."""

    def __init__(self, in_channels: int, out_channels: int):
        super().__init__()
        self.maxpool_conv = nn.Sequential(
            nn.MaxPool2d(2),
            DoubleConv(in_channels, out_channels),
        )

    def forward(self, x):
        return self.maxpool_conv(x)


class Up(nn.Module):
    """Upsampling block: upsample + concat skip + double conv."""

    def __init__(self, in_channels: int, out_channels: int):
        super().__init__()
        self.up = nn.ConvTranspose2d(in_channels, in_channels // 2, kernel_size=2, stride=2)
        self.conv = DoubleConv(in_channels, out_channels)

    def forward(self, x1, x2):
        """Forward pass.

        Args:
            x1: Upsampled tensor from deeper layer
            x2: Skip connection tensor from encoder
        """
        x1 = self.up(x1)

        # Handle size mismatch (input size not divisible by 16)
        diff_y = x2.size()[2] - x1.size()[2]
        diff_x = x2.size()[3] - x1.size()[3]

        x1 = F.pad(x1, [diff_x // 2, diff_x - diff_x // 2,
                        diff_y // 2, diff_y - diff_y // 2])

        # Concatenate skip connection
        x = torch.cat([x2, x1], dim=1)
        return self.conv(x)


class UNet(nn.Module):
    """U-Net for image restoration.

    Architecture:
    - Encoder: 4 downsampling stages (64 -> 128 -> 256 -> 512 channels)
    - Bottleneck: 1024 channels
    - Decoder: 4 upsampling stages with skip connections
    - Output: Same size as input
    """

    def __init__(self, n_channels: int = 3, n_classes: int = 3):
        """Initialize U-Net.

        Args:
            n_channels: Number of input channels (1 for grayscale, 3 for RGB)
            n_classes: Number of output channels (same as input for restoration)
        """
        super().__init__()
        self.n_channels = n_channels
        self.n_classes = n_classes

        # Encoder
        self.inc = DoubleConv(n_channels, 64)
        self.down1 = Down(64, 128)
        self.down2 = Down(128, 256)
        self.down3 = Down(256, 512)
        self.down4 = Down(512, 512)  # Reduced from 1024 for memory

        # Decoder
        self.up1 = Up(1024, 256)
        self.up2 = Up(512, 128)
        self.up3 = Up(256, 64)
        self.up4 = Up(128, 64)

        # Output
        self.outc = nn.Conv2d(64, n_classes, kernel_size=1)

    def forward(self, x):
        """Forward pass.

        Args:
            x: Input tensor (B, C, H, W)

        Returns:
            Restored tensor (B, C, H, W)
        """
        # Encoder with skip connections
        x1 = self.inc(x)
        x2 = self.down1(x1)
        x3 = self.down2(x2)
        x4 = self.down3(x3)
        x5 = self.down4(x4)

        # Decoder
        x = self.up1(x5, x4)
        x = self.up2(x, x3)
        x = self.up3(x, x2)
        x = self.up4(x, x1)

        # Output
        logits = self.outc(x)
        return logits


if __name__ == "__main__":
    # Test model
    model = UNet(n_channels=3, n_classes=3)
    x = torch.randn(1, 3, 256, 256)
    y = model(x)
    print(f"Input shape: {x.shape}")
    print(f"Output shape: {y.shape}")
    print(f"Parameters: {sum(p.numel() for p in model.parameters()):,}")
