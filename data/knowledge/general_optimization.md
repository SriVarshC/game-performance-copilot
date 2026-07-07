# General PC Gaming Optimization Guide

## Understanding DLSS
DLSS (Deep Learning Super Sampling) is an NVIDIA technology that renders games at
a lower internal resolution, then uses an AI model trained on higher-resolution
reference images to reconstruct detail and upscale the output. This trades a
small amount of image sharpness for a substantial FPS increase. DLSS has several
modes:
- Quality: renders at a higher internal resolution, smallest FPS gain, best
  visual fidelity
- Balanced: middle ground between quality and performance
- Performance: renders at a much lower internal resolution, largest FPS gain,
  most noticeable softness especially at 1080p
- Ultra Performance: extreme upscaling, reserved for very high target
  resolutions like 4K where the internal render resolution is still reasonably
  detailed

## Understanding FSR (AMD FidelityFX Super Resolution)
FSR is AMD's equivalent to DLSS, but it uses spatial upscaling algorithms rather
than a trained AI model, meaning it works on virtually any GPU including
NVIDIA cards. It generally provides a smaller image quality improvement than
DLSS at equivalent settings, but is a universally compatible fallback when DLSS
isn't supported by a game or GPU.

## Ray Tracing Trade-offs
Ray tracing simulates realistic light behavior (reflections, shadows, global
illumination) by tracing individual light rays, which is dramatically more
computationally expensive than traditional rasterized rendering. On mid-range
and lower VRAM GPUs, ray tracing can cost 40-60% of available frame rate. It's
generally only worth enabling when combined with an upscaling technology like
DLSS or FSR to recover the lost performance, and even then, mainly on titles
where ray tracing meaningfully changes visual fidelity (open-world and
narrative-driven games benefit more than fast-paced competitive shooters).

## Thermal Throttling — General Causes and Fixes
Thermal throttling occurs when a GPU or CPU exceeds a safe temperature
threshold, causing the hardware to automatically reduce clock speed to lower
heat output. Common causes on laptops specifically:
- Dust buildup blocking intake/exhaust vents (cleaning typically recovers
  5-10°C)
- Using the laptop on a soft surface (bed, couch) that blocks bottom-mounted
  intake vents
- Aggressive power limits set higher than the cooling system can sustain
- Poor thermal paste application (only relevant after months/years of use, or
  after any hardware servicing)

Fixes, roughly in order of ease:
1. Elevate the laptop or use a hard, flat surface to ensure vents aren't
   blocked
2. Use a cooling pad with active fans
3. Clean dust from vents (compressed air, or professional cleaning)
4. Lower the GPU power limit via vendor software (e.g. MSI Afterburner) — this
   directly reduces heat output at a modest FPS cost
5. Switch to a Balanced or Power Saver Windows power plan during less demanding
   games

## VRAM Management
VRAM (Video RAM) stores textures, frame buffers, and other GPU-resident data.
When a game's texture and rendering demands exceed available VRAM, data
"overflows" into much slower system RAM accessed over the PCIe bus, causing
severe stuttering and inconsistent frame times — often worse than simply having
lower visual quality would have been. On GPUs with limited VRAM (4-6GB), the
single most effective fix for VRAM pressure is lowering texture quality, since
textures are typically the largest VRAM consumer among all graphics settings.
Enabling upscaling (DLSS/FSR) also reduces VRAM pressure somewhat, since it
lowers the actual render resolution.

## CPU vs GPU Bottlenecks
A CPU bottleneck occurs when the CPU cannot feed the GPU with frames fast enough
— visible as GPU utilization staying below 100% (often well below) while frame
rate is limited and CPU utilization on one or more threads stays very high. This
is common in simulation-heavy games (strategy games, life sims, games with
large numbers of AI-controlled units). Fixes include reducing simulation-related
settings (crowd density, physics detail, view distance) and closing background
applications competing for CPU cycles.

A GPU bottleneck is the more common case in most modern games: GPU utilization
stays near 100% while CPU utilization is comparatively low. This means the
graphics workload itself (resolution, shadow quality, ray tracing, anti-
aliasing) is the limiting factor. Fixes include lowering resolution, reducing
graphics preset, or enabling upscaling.