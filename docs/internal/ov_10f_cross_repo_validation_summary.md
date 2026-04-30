# OV-10F — Cross-Repo Validation Summary (Final)

## Branch Verification

- Community branch: `feature/rearchitecture-runtime-overlay-contract`
- Supported branch: `feature/rearchitecture-runtime-overlay-contract`
- Result: matched in both repositories

## Overlay Coverage

| overlay | community_dev | community_installed | supported_dev | supported_installed | parity |
| --- | --- | --- | --- | --- | --- |
| `overlay_hello_world` | pass | pass | pass | pass | full parity |
| `overlay_heartbeat_v2` | pass | pass | pass | pass | full parity |
| `overlay_asx200_ohlcv_v2` | n/a | n/a | pass | pass | Supported-only overlay |
| `overlay_asx_historic_csv` | pass | pass | pass | pass | full parity |
| `overlay_kaggle_ingestion` | pass | pass | pass | pass | full parity |
| `overlay_file_only_demo` | pass | pass | pass | pass | full parity |

## Corrected Findings

### Dev-Mode Behaviour

- Final conclusion: yes. Dev-mode parity is achieved for all five shared overlays.
- Community dev mode passed all five Community overlays in OV-05.
- Supported dev mode passed all six Supported overlays after the OV-07C and OV-07D remediations completed the earlier OV-07B false negatives and dev-surface gaps.
- `overlay_asx200_ohlcv_v2` remains Supported-only, so it is outside cross-repo parity scope but passes within the Supported repo.

### Installed-Mode Behaviour

- Final conclusion: yes. Installed-mode parity is achieved for all five shared overlays on the current branch.
- The OV-09 Community installed failures for `overlay_heartbeat_v2` and `overlay_kaggle_ingestion` were not real persistent parity gaps.
- OV-10A reproduced Community and Supported heartbeat installed mode from clean `/tmp` roots and showed both repos healthy after a 90-second warm-up.
- OV-10C reproduced Community and Supported Kaggle installed mode from clean `/tmp` roots and showed both repos install cleanly, expose the expected config file, and reach healthy scheduler state after warm-up.
- Supported installed-mode reproducibility for `overlay_asx200_ohlcv_v2` was documentation-blocked in OV-08 and then closed by OV-08A; the final Supported installed conclusion is pass for all six overlays.

### Documentation Reproducibility

- Final conclusion: yes. All validated overlays are reproducible from documentation in their current state.
- Community reproducibility is now complete for its five overlays. The remaining ambiguity identified in OV-09 was the Kaggle installed archive/install documentation, and OV-10C corrected that documentation.
- Supported reproducibility is complete for all six overlays after OV-08A added the missing `overlay_asx200_ohlcv_v2` archive/install steps and resolved the Kaggle and file-only-demo installed command conflicts.

## Correction of OV-09 Conclusions

- OV-09 incorrectly concluded that Community installed mode failed for `overlay_heartbeat_v2`.
- Why incorrect:
  - the OV-06 failure record sampled Airflow `/health` too early, after roughly 40 seconds total wait, during a transient scheduler-heartbeat startup window
- Correcting evidence:
  - OV-10A reran the same scenario from clean installed roots on 2026-04-30 and both Community and Supported returned `scheduler.status = healthy` after a 90-second warm-up

- OV-09 incorrectly concluded that Community installed mode failed for `overlay_kaggle_ingestion`.
- Why incorrect:
  - the recorded `cp config/kaggle_jobs.example.json config/kaggle_jobs.json` failure was not reproducible from a clean install context on the current branch
  - the recorded unhealthy scheduler state was also a transient startup artefact rather than a persistent runtime defect
- Correcting evidence:
  - OV-10C showed `config/kaggle_jobs.example.json` present immediately after unzip in both repos, the documented copy step succeeding, the DAG present, PHP reachable, and scheduler health reaching `healthy` after normal warm-up

- OV-09 therefore incorrectly treated two Community installed-mode observations as enduring parity failures.
- The corrected final state is that those failures were validation artefacts, not current branch contract violations.

## Root Cause of False Negatives

- Timing issues (`overlay_heartbeat_v2`):
  - Airflow webserver `/health` became reachable before the scheduler had emitted its later steady-state heartbeat
  - an early probe could therefore report `scheduler.status = unhealthy` even though the scheduler process was running and later became healthy without changes

- Non-clean install/test context (`overlay_kaggle_ingestion`):
  - the earlier failing copy step was not reproducible from a clean temp-root install on the current branch
  - the corrective rerun showed the expected archive contents and successful config copy in both repos

- Documentation ambiguity:
  - Supported had real installed-doc gaps in OV-08 for `overlay_asx200_ohlcv_v2`, plus conflicting Kaggle and file-only-demo command paths
  - Community Kaggle docs also needed the installed archive-root expectation stated explicitly
  - these documentation issues affected reproducibility claims, but not the final installed runtime parity after correction

## Final Assessment

- Overall status: PASS
- Justification:
  - both repos satisfy the overlay contract on the required root surfaces and explicit Airflow service model
  - dev-mode parity is achieved across all five shared overlays
  - installed-mode parity is achieved across all five shared overlays after correcting the OV-09 false negatives with OV-10A and OV-10C evidence
  - all overlays are reproducible from current documentation, including the Supported-only `overlay_asx200_ohlcv_v2` after OV-08A
  - the previous Community installed failures were artefacts of timing and validation context, not persistent branch-level defects

## Recommendations

- Validation discipline improvements:
  - require clean `/tmp` install roots for installed-mode validation and record the exact archive contents being tested
  - treat historical failed observations as provisional until reproduced from a clean root with the same command set

- Test timing guidance:
  - use the task-standard 60 to 120 second warm-up before treating Airflow scheduler health as failed
  - distinguish container reachability from steady-state scheduler heartbeat readiness in validation conclusions

- Documentation clarity rules:
  - every overlay should declare one authoritative archive, install, and start command set per mode
  - installed-mode docs must state expected archive-root paths for any required post-unzip copy steps
  - when dev and installed commands differ, both paths should be stated explicitly to avoid command drift
