# AgenticLoop

AgenticLoop is an evidence-gated control plane for AI-assisted computational research. It treats research questions, task contracts, evidence objects, claim ledgers, closeouts, and manuscript bindings as durable project state.

This repository contains the public research artifact for the AgenticLoop technical report:

- `experiments/agenticloop/`: experiment workspace skeleton, audit scripts, and protocol-facing runners.
- `tests/agenticloop/`: regression tests for the experiment and audit contracts.
- `docs/research/`: research state, version records, evidence notes, and supporting documentation.
- `src/agenticloop/`: claim admission, metric provenance, and research-spine loaders.
- `ui/`: Evidence Console — local UI for gate admission, provenance, and protocol comparison.


High Level system architectural view of this AgenticLoop engineering project.

<img width="6706" height="4771" alt="diagram (13)" src="https://github.com/user-attachments/assets/48bad189-f382-47dd-9e76-e8ff2938f35a" />


The public artifact is venue-neutral. It preserves the research process and reproducibility materials without encoding a specific submission venue or outcome.

## Evidence Console

```bash
python ui/server.py
# open http://127.0.0.1:8765
```

See `ui/README.md`. The console reads durable V6 artifacts only and rejects mock/dry-run text as paper-eligible evidence.

## Notes

Generated LaTeX files and historical research records are kept to make the artifact inspectable. Claims in the manuscript should be interpreted through the paper claim ledger, evidence gates, and closeout records.
