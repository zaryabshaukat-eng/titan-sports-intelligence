from app.modules.explainability.engines import DeterministicFeatureExplainer


class ExplainabilityRegistry:
    def __init__(self) -> None:
        self._engines = (DeterministicFeatureExplainer(),)

    def engines(self):
        return self._engines
