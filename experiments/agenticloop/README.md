# AgenticLoop Experiment Workspace

This directory contains the experiment workspace skeleton for the AgenticLoop public artifact. It defines task, prompt, baseline, trial configuration, and audit-script interfaces. Smoke or mock outputs must remain explicitly marked and must not be promoted into manuscript claims.

## Subdirectories

- `tasks/`: controlled research task suite drafts.
- `prompts/`: ad-hoc, linear, full-protocol, and ablation prompts.
- `baselines/`: baseline adapters and dossiers.
- `trial_configs/`: locked condition/seed/budget/tool-permission configs.
- `scripts/`: audit and trial runner scripts.
- `results/`: real run outputs only; mock output must be marked `is_mock: true`.