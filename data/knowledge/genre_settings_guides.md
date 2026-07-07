# Genre-Specific Settings Recommendations

## Competitive FPS (Valorant, CS2, Apex Legends style games)
Competitive shooters prioritize responsiveness and consistent high frame rates
over visual fidelity — professional and high-level players commonly run these
games at low or medium settings even on powerful hardware, specifically to
maximize frame rate and minimize input latency. Recommended approach: lowest or
low preset, disable motion blur and depth of field entirely (they reduce
clarity without helping competitively), disable ray tracing (not useful in fast
competitive play), and prioritize frame rate stability over visual quality.
VRAM demands are typically light for this genre.

## AAA FPS / Story-driven Shooters (Cyberpunk, Call of Duty campaign, Battlefield)
These titles are built around visual spectacle and benefit more from higher
settings, but are also the most GPU and VRAM demanding genre. On 4GB VRAM GPUs,
texture quality is the setting most likely to cause VRAM overflow — keep
textures at Medium-High rather than Ultra. Ray tracing can look impressive in
these titles but costs significant FPS; pair it with DLSS/FSR if enabled at
all. Shadow quality and ambient occlusion are good candidates to reduce for FPS
gains with minimal visual impact.

## Open World RPG (Elden Ring, Witcher 3, Red Dead Redemption 2 style games)
Open world games balance CPU load (streaming world data, NPC simulation, physics)
with GPU load (draw distance, foliage density, lighting). These games often
show mixed or fluctuating bottlenecks depending on location (dense cities vs
open plains). View distance and foliage density settings are good targets for
CPU-side improvements; texture and shadow quality are the main GPU-side
targets. VRAM pressure can be significant in these titles due to large open
world texture streaming.

## MOBA (Dota 2, League of Legends style games)
MOBAs are relatively lightweight on GPU demand compared to other genres, but can
be CPU-intensive due to many units, spells, and particle effects on screen
simultaneously, especially in late-game team fights. These games generally run
extremely well even on modest hardware; settings can typically stay high without
performance concern, though particle effect density is worth reducing if frame
drops occur specifically during large team fights.

## Battle Royale (Fortnite, PUBG, Warzone style games)
Battle royale games combine large open maps with many simultaneous players,
creating both CPU load (player/object simulation across a large map) and GPU
load (draw distance, view distance across open terrain). VRAM demands are
moderate to high due to large map textures. Reducing view distance and effects
quality tends to give the best FPS improvement per visual quality lost in this
genre, since seeing enemies clearly at range matters more competitively than
distant scenery detail.

## Racing Games (Forza, F1 style games)
Racing games are typically GPU-bound due to high-detail vehicle models,
reflections, and track environments at high speed. Motion blur is often used
stylistically in this genre — unlike competitive shooters, some motion blur can
be kept if desired since these games aren't typically played at a competitive
input-latency-critical level. Track detail and reflection quality are the
primary GPU cost centers to adjust if targeting a specific frame rate.

## Strategy Games (Total War, Civilization, RTS style games)
Strategy and RTS games are usually CPU-bound rather than GPU-bound, since they
simulate large numbers of units, AI decision-making, and complex game state each
frame — especially in late-game scenarios with many units or a large map.
Reducing unit/crowd density settings and simulation detail (where available)
tends to give larger FPS improvements than reducing graphics quality in this
genre. GPU settings can often stay relatively high without much performance
cost, since the CPU is typically the limiting factor first.