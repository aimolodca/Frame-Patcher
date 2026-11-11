# Close crops for text and repeated products

Use this route when packaging, lettering, or a logo stays inaccurate because each object occupies too little of a group crop. Prefer it as the adjusted second attempt, not as an unbounded retry loop.

1. Name the failed visible fact: for example, scrambled letters on one otherwise correct pack. Keep the reference and exact text authoritative.
2. Prepare a closer contextual crop around that object. Keep its full outline, perspective cues, support, and any foreground rail or occluder. Make the object larger within the input; do not simply expand the scene bbox, zoom the final image, or enlarge the edit mask.
3. Mask the full faulty text field, including every outgoing fragment and the new lettering footprint. For an interior lettering repair, preserve the pack outline, logo, corner graphics, rails, and neighbors. For a complete replacement, retain the existing full-object mask rule.
4. Set a working long edge appropriate for the editor, often 1024–1536 px. Inspect the reported `work_size`, not just the requested flag. `prepare` retains a default 4× enlargement ceiling; raise `--max-upscale` explicitly if it prevents the required working size. Upsampling helps allocate editor space but adds no original evidence: use a visual reference for reconstruction.
5. Send the clean `crop-work.png`, its mask, and the visual reference. Specify exact lines and natural occlusion by the central artwork; protect all other text and geometry. Keep neighboring accepted objects out of the editable region.
6. Run registration review before compositing if the editor returns another size. Reject moved landmarks or changed perspective. Cover all old and new letter pixels with the reviewed mask; do not hide a cut letter at the mask boundary with feathering.
7. Inspect lettering and seams at 100% and 200%, then inspect the source-resolution full image. Require pixel protection and visual acceptance independently. A sharper enlarged preview alone is not a pass.

Example for a 176×176 native context that should become a 1536×1536 working image:

```bash
python3 <skill-dir>/scripts/patch_tools.py prepare SOURCE DETAIL_PATCH \
  --polygon TEXT_FIELD.json --context-bbox x,y,176,176 \
  --mode repair --work-size 1536 --max-upscale 12 \
  --request "correct the repeated lettering from the supplied package reference" \
  --invariant "reference-matched words, line order and natural artwork occlusion" \
  --protected "pack outline, logo, rails, neighboring objects and final framing"
```

Without the explicit cap change, the same request produces 704×704. Preserve the existing attempt ceiling and any parent budget. A user instruction to continue with a closer crop authorizes that adjustment; do not interpret it as approval for overlays, a new design, or unlimited generations.
