# RTX 3050 Ti Laptop + i7-12650H Hardware Reference

## GPU Specifications
The NVIDIA GeForce RTX 3050 Ti Laptop GPU has 4GB of dedicated GDDR6 VRAM. This is
the single biggest limiting factor on this system — many modern AAA titles at high
or ultra settings want 6-8GB of VRAM, so texture quality and resolution scaling
need to be managed carefully to avoid VRAM overflow into slower shared system RAM.

Base clock speed is approximately 1695 MHz under normal thermal conditions. When
the GPU exceeds 85°C, clock speed drops roughly 15 MHz per degree above that
threshold — this is thermal throttling, and it directly reduces FPS even though
GPU utilization may still read high.

Typical power draw ranges from 45-80 watts depending on load. Power draw scales
roughly linearly with GPU utilization: idle draws under 15W, while heavy gaming
loads can approach the 80W ceiling on this laptop's power delivery.

## NVIDIA Optimus Hybrid Graphics
This laptop uses NVIDIA Optimus, meaning it has both an integrated Intel GPU and
the discrete RTX 3050 Ti. When not actively rendering a game (browsing, idle
desktop, video playback in some cases), the RTX 3050 Ti powers down almost
completely. This shows up as 0% GPU utilization, near-zero power draw, and low
clock speed. This is completely normal and not a hardware problem — it only
means the discrete GPU isn't currently in use.

## Thermal Thresholds (specific to this hardware)
- Below 75°C: normal operating range, no action needed
- 75-85°C: warm but acceptable under sustained load
- Above 85°C: thermal throttling begins — clock speed drops, FPS suffers
- Above 91°C: critical — severe throttling, consider immediate intervention
  (lower power limit, improve airflow, reduce settings)

## CPU Specifications
The Intel i7-12650H is a hybrid architecture CPU with 10 cores and 16 threads,
combining Performance cores (P-cores) and Efficiency cores (E-cores). Windows'
thread scheduler decides which core type handles which task — games generally
benefit most from P-core allocation. CPU thermal warning threshold on this chip
is around 90°C.

## RAM Behavior
This system has 16GB total RAM and characteristically idles at 82-85% usage even
with nothing gaming-related running — this is normal for this machine's typical
background process load and should not be mistaken for a memory problem. RAM
usage becomes a genuine concern only above 90-92%, where page file swapping can
start impacting frame times.

## VRAM Thresholds (4GB total)
- Below 75% (under ~3.07GB): safe operating range
- 75-90% (3.07GB-3.69GB): VRAM pressure — consider lowering texture quality
- Above 90% (over 3.69GB): critical — textures will overflow into shared system
  RAM, causing significant stuttering and frame time spikes

## DLSS and Ray Tracing on This Hardware
The RTX 3050 Ti supports NVIDIA DLSS (Deep Learning Super Sampling), which uses
AI upscaling to render at a lower internal resolution and reconstruct a
higher-resolution image. On this GPU, DLSS typically provides up to a 1.90x FPS
boost depending on the mode (Quality, Balanced, or Performance) — Performance
mode gives the largest FPS gain at some cost to image clarity.

Ray tracing is supported but expensive on 4GB of VRAM. Enabling ray tracing
typically costs approximately 48% of available FPS on this GPU. Combined with
DLSS, ray tracing becomes far more viable since DLSS recovers much of that lost
performance — enabling both together is usually the best approach if ray
tracing is desired at all on this hardware.