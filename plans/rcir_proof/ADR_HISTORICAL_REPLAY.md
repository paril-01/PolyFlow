# Historical replay and release eligibility

The owner's repeated complete-implementation instruction authorizes continuing development. CI checks two different properties separately:

1. Frozen historical receipts are internally consistent with the recorded source-byte policy. Historical dirty flags remain intact. This is an artifact-replay check, not a current benchmark or approval of an architecture.
2. Release eligibility requires fresh clean source, qualified independent evaluation, current provenance and the preregistered success criteria. The existing strict gate continues to reject the dirty historical run.

Historical replay runs in temporary output directories and explicitly reports `release_eligible: false` for a recorded dirty source. Its passing CI exit means only that the frozen replay is consistent. No paid calls, public release, main write or fabricated benchmark result is authorized. The original manifest and all historical raw receipts remain unchanged.
