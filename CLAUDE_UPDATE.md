"""Update CLAUDE.md with M3 progress."""

Update the "Current Milestone: M1" section to:

## Current Milestone: M3

**Goal**: Image restoration with classical CV + learned U-Net

**Tasks**:
- [x] Classical restoration techniques (background flatten, CLAHE, deskew, binarization)
- [ ] U-Net architecture for learned denoising
- [ ] Training script with PyTorch Lightning
- [ ] Dataset loader for synthetic (degraded, clean) pairs
- [ ] MLflow logging
- [ ] Evaluation metrics (PSNR, SSIM)
- [ ] Compare classical vs learned vs combined
- [ ] API endpoint for restoration

## Milestones Summary

- ✅ **M1**: Scaffolding + vertical slice (upload→Tesseract→search)
- ✅ **M2**: Synthetic degradation engine + real test set guide
- 🔄 **M3**: Image restoration (classical ✅, learned in progress)
- 📋 **M4**: Layout segmentation
- 📋 **M5**: Recognition ensemble (Tesseract + CRNN + VLM)
- 📋 **M6**: Post-correction & translation
- 📋 **M7**: Hybrid retrieval engine
- 📋 **M8**: ManuscriptChat
- 📋 **M9**: Frontend
- 📋 **M10**: Innovation features
- 📋 **M11**: Deployment & docs
