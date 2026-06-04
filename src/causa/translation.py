from enum import Enum

from pydantic import BaseModel


class TranslationLevel(str, Enum):
    EXECUTIVE = "executive"
    PROFESSIONAL = "professional"
    FORENSIC = "forensic"


class TranslationArtifact(BaseModel):
    id: str
    trace_id: str
    level: TranslationLevel
    template_version: str
    text: str
    faithfulness_checked: bool = False
    usability_checked: bool = False
