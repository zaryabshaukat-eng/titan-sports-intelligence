def scores(*, evidence_count: int, contribution_count: int) -> tuple[float, float, float, float]:
    evidence = min(1.0, evidence_count / 5)
    traceability = 1.0 if evidence_count >= 5 else evidence
    coverage = min(1.0, contribution_count / 5)
    return (evidence + traceability + coverage) / 3, evidence, traceability, coverage
