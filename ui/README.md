# AgenticLoop Evidence Console

Local UI for the research control plane in this repository.

## Features

1. **Research spine** — live epoch / gate / paper-binding status from `docs/research/`
2. **Claim admission gate** — admit / hold / reject draft claims with evidence-trace heuristics (mock language rejected)
3. **Metric provenance** — browse T05 vs T06 vs ablation sources so headline numbers are not mixed
4. **Protocol comparator** — claim-weighted B01 / B02 / Full bars from durable T05 metrics
5. **Falsification board** — surfaces the V6 null-effect status explicitly
6. **Extended research points** — claim volume, gate-redundancy index, classifier drift, task heterogeneity (`/api/research-points`)

## Run

From the repo root (Flask required):

```bash
python ui/server.py
```

Open [http://127.0.0.1:8765](http://127.0.0.1:8765).

CLI (same gate, no browser):

```bash
python ui/admit_claim.py "Full rate is 6.87% per runs/V6_RQ01_T05_metrics.json"
python ui/verify_provenance.py --write
```

## API

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/api/spine` | Epoch pipeline + falsification board |
| GET | `/api/metrics` | Provenance map + available metric payloads |
| GET | `/api/metrics/<id>` | Single metric source resolution |
| POST | `/api/admit` | JSON `{claim, require_artifact_path?, allow_mock?}` |

## Design notes

- Reads only local artifacts; does not call models or invent results.
- Ablation deltas are labeled separately from T05 claim-weighted rates.
- Library code lives in `src/agenticloop/` and is covered by `tests/agenticloop/test_claim_gate.py` and `test_provenance.py`.
