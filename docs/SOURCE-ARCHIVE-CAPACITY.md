# Bounded source-archive capacity repair — 17 November 2026

The normal FastNews run44036531696 failed while building LabourNet DE's source archive: the flat source JSON package exceeded4194304 UTF-8 bytes. The previous public file is4155003bytes (97articles,43complete bodies), only39301bytes below that cap. Saved public inputs replay at4154894bytes and do not themselves reproduce the failed runner. Its unpublished exact inputs were not retained. A clearly synthetic64KiB admitted addition produces4221385bytes, reproduces the old refusal, and passes the new bounded capacity.

## Compatible behavior

Maximum serialized source package size is8MiB=8388608bytes, still counted after compact UTF-8 JSON serialization plus newline. A single byte over the limit still aborts before main writes chunks, manifest or quick-feed. No text cut, article removal, contentComplete promotion, rights-policy change, cap bypass or automatic unlimited growth is introduced. Existing30-day eligibility is unchanged.

Manifest schema1, one source entry and one flat news-archive/<source-id>.json array per source, stable source IDs and quick detailPath bindings remain identical. Readers need no migration. The existing full-body admission and prior-body retention comparisons are unchanged. All43 previously complete LabourNet raw bodies remain byte-identical in replay. This candidate does not repair unrelated historical truncated articles.

## Validation and limits

17 targeted existing/new pytest cases PASS, covering actual8MiB-1/exact8MiB/+1 boundaries using multibyte UTF-8, per-source rather than global capacity, full-body equality, unchanged legacy paths, detail binding and no-output-writes on overcapacity. Existing rights/incomplete/mismatched identity/rollover/30-day guards pass.

Actual unmodified function slices and core from signed Code41 AAB91771a06... were read-only extracted. Three fresh-VM loopback HTTP probes load the real LabourNet replay, synthetic growth, and exact8MiB package. Raw transport/cache content hashes and complete bodies are preserved. The existing signed core's whitespace/HTML normalization is compared separately against that exact core; normalized render text is not misrepresented as byte-identical raw text. Loading/parse/normalization at approximately2MiB/s source pacing took3.2/3.2/5.6seconds, below the actual25second source timeout. This is a controlled compatibility probe, not public/mobile throughput or native storage proof.

Independent exact candidate review and PR CI are still required. No production news refresh or public delivery PASS is claimed by this private package. Any later over8MiB package must fail closed and prompt a separate versioned-sharding design coordinated with App/Website readers. PR59 and all App/Website target files remain untouched.
