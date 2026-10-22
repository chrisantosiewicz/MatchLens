# V4 review — October 22, 2026

Developer and second-AI review; independent human acceptance remains pending.

Four actual English outputs were reviewed against frozen contexts. 4103-0 and 4103-1 correctly describe team entry rates 5/10 to 3/5 (0.5 to 0.6) and player progressive-pass rates 3/10 to 1/5 (0.3 to 0.2). 4127-0 and 4127-1 correctly describe both rates changing from 0.5 to 0.2 across 10-minute windows. Subjects, stated intervals and association/no-causation caveats are supported. No unsupported factual clause was identified in these four outputs. Passing relevance is modest: comparison of recorded forward-pass frequencies, not tactical quality.

The second AI reviewer identified a presentation defect: the recorded viewer labeled the combined deterministic-source/model-ID union as model citations. The viewer now renders model_cited_event_ids in that section and retains deterministic aggregate sources separately. Backend already preserved both arrays.

12 paired questions, 24 policy rows, four actual model calls. Eight single-policy cases used deterministic boundaries, not model generation; they are not model successes/refusals. Source freeze: 6da84d6; manifest frozen-english-v4.json. Input tokens 23,942; output tokens 727. Model call times: 8,520.81 / 3,360.23 / 2,765.54 / 3,477.32 ms. These are observations, not a service guarantee or end-to-end timeout. Raw usage is not an invoice.

Independent human review remains required; this sample establishes no population reliability. Earlier failures remain available. Scopes/cases changed, so version-to-version acceptance rates would be misleading.
