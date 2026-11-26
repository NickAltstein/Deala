# Silent Shift v0.3 — Public evaluation methodology

## SS-01 / INTELLIGENCE
Frozen 72-hour accelerated event replay; no user prompts. Measure recommendation precision, recall, evidence grounding, correct silence and missed opportunities.

## SS-02A / MODEL & PAYLOAD
Exercise actual parsing and recovery with controlled malformed output, truncated JSON, interrupted SSE, timeouts and bounded retries.

## SS-02B / PROTOCOL & TRANSPORT
Use actual connector code and real protocol I/O against authorized test endpoints. Inject TCP faults and controlled HTTP failures. Response replay alone is not integration proof.

## SS-03 / ENDURANCE
Run for 72 elapsed hours unattended. Track scheduling, queues, restarts, resources, missed and duplicate work, and authorization failures. Accelerated replay is not endurance.

## SS-04 / ECONOMICS
Compare equivalent held-out workloads, quality and recommendation budgets at one, four and eight isolated tenants. Measure actual cost, latency, routing, utilization and retries; label modeled costs separately.

## Disposition and scoring contract
Measurement and integrity

Freeze candidate versions, scenarios, answer keys and scoring before evaluation. Keep held-out labels outside the candidate runtime. Independent commercial labels are needed for real-world claims.

Precision: qualified recommendations / recommendations. Recall: detected valid opportunities / all independently labeled valid opportunities. Correct silence: validated correct non-interventions / all cases labeled for silence. Completion: completed expected unique events / expected unique events. Report failure, timeout, unresolved deferral, dropped event and authorization violation counts independently. Undefined ratios are N/A.

Authorization violations are hard-gate failures, not a penalty offset by intelligence scores. Report SS-02A and SS-02B separately. Cost per qualified recommendation is N/A when none qualifies.

RECOMMEND, ABSTAIN, FILTERED, ESCALATE, DENIED, DEFERRED, FAILED, TIMEOUT. Every accepted unique event must have a traceable disposition; deferrals reconcile to retry or terminal outcome. Failures never count as correct silence.

## Evidence status
Methodology only. No completed benchmark, endurance result, certification or deployment claim. Synthetic fixtures do not establish commercial advantage.
