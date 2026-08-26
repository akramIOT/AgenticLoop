# Cross-Reference Warning

rq_alpha and rq_beta both use the `user_queries_q1` dataset and mention
"caching" and "reduction." However:

- rq_alpha measures LATENCY (milliseconds).
- rq_beta measures CPU UTILIZATION (percent).

These are different metrics answering different RQs. Do NOT conflate them.
A claim like "caching improves performance" is ambiguous and unsupported
because it mixes latency and CPU metrics. Always specify which RQ and
which metric you are citing.
