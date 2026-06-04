from causa.core.models import CandidateHypothesis


def propose_hypothesis(identifier: str, statement: str) -> CandidateHypothesis:
    return CandidateHypothesis(id=identifier, statement=statement)
