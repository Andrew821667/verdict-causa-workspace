from enum import Enum


class AuthorityLevel(str, Enum):
    CONSTITUTIONAL = "constitutional"
    STATUTORY = "statutory"
    REGULATORY = "regulatory"
    JUDICIAL = "judicial"
    CONTRACTUAL = "contractual"
    FACTUAL = "factual"
