from causa.core.models import CandidateHypothesis


def mark_candidate_reviewed(candidate: CandidateHypothesis) -> CandidateHypothesis:
    return candidate.model_copy(update={"status": "reviewed"})
