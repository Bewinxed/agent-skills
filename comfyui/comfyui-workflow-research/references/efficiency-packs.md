# ComfyUI Efficiency Node Packs Reference (Jan 2026)

## Actively Maintained Packs

### rgthree-comfy (2.7k stars)
- GitHub: rgthree/rgthree-comfy
- Focus: Workflow organization, context passing, node control
- Key patterns: Context system (bundles model/clip/vae/conditioning), Fast Muter dashboard, improved Reroute
- FLUX: Full support

### Impact Pack (2.9k stars)
- GitHub: ltdrdata/ComfyUI-Impact-Pack
- Focus: Pipe system, face/detail enhancement, detection
- Key patterns: BASIC_PIPE (bundles model/clip/vae/pos/neg), FaceDetailer, SEGS detection
- FLUX: V6.0+ required

### Efficiency Nodes (1.4k stars)
- GitHub: jags111/efficiency-nodes-comfyui
- Focus: Aggressive consolidation, XY plots, tiled upscaling
- Key patterns: Efficient Loader (checkpoint+VAE+LoRA+caching), script nodes
- FLUX: Partial (may need manual loaders)

### ComfyUI-Easy-Use (2.3k stars)
- GitHub: yolain/ComfyUI-Easy-Use
- Focus: Beginner-friendly all-in-one nodes, A1111 compatibility
- Key patterns: fullLoader, fullkSampler, stacks
- FLUX: Full support with dedicated nodes

### Crystools (1.1k stars)
- GitHub: crystian/ComfyUI-Crystools
- Focus: System monitoring, debugging, metadata
- Key patterns: Switch nodes, resource monitoring, metadata comparison

## Archived/Maintenance-Only

| Pack | Status | Notes |
|------|--------|-------|
| WAS Node Suite | Archived Jun 2025 | Fork at ltdrdata/was-node-suite-comfyui |
| ComfyUI Essentials | Maintenance-only Apr 2025 | Many features merged to core |

## Overlap Conflicts

Avoid mixing:
- Context systems: rgthree Context vs Impact BASIC_PIPE
- Loaders: Efficiency Efficient Loader vs Easy-Use fullLoader
- Switches: rgthree Any Switch vs Crystools Switch any

## Consolidation Ratios

| Node | Replaces ~N nodes |
|------|-------------------|
| Efficient Loader | 5-7 |
| FaceDetailer (pipe) | 8-10 |
| XY Plot script | 10+ |
| Context Big | 5 connections |
| BASIC_PIPE | 5 connections |
