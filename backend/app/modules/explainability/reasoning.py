def chain(
    *, dataset_id: object, probability_id: object, consensus_id: object, risk_id: object
) -> list[tuple[str, str, str]]:
    return [
        ("feature_values", "Feature values support the dataset snapshot.", str(dataset_id)),
        ("research_dataset", "Frozen dataset supplied probability inference.", str(dataset_id)),
        ("probability_output", "Probability output supplied consensus input.", str(probability_id)),
        ("consensus_output", "Consensus output supplied risk assessment.", str(consensus_id)),
        ("risk_assessment", "Risk assessment completes the explanation evidence.", str(risk_id)),
    ]
