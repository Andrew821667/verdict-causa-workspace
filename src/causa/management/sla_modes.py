from enum import Enum


class SLAMode(str, Enum):
    DRAFT = "draft"
    STANDARD = "standard"
    DEEP = "deep"
    RESEARCH = "research"
