from enum import Enum

from pydantic import BaseModel, Field


class ContractRelationType(str, Enum):
    SALE = "sale"
    SUPPLY = "supply"
    SERVICES = "services"
    WORKS = "works"
    OTHER = "other"


class ObligationStatus(str, Enum):
    PERFORMED = "performed"
    BREACHED = "breached"
    DISPUTED = "disputed"
    UNKNOWN = "unknown"


class ContractParty(BaseModel):
    id: str
    name: str
    role: str


class ContractObligation(BaseModel):
    id: str
    debtor_party_id: str
    creditor_party_id: str
    description: str
    due_date: str | None = None
    status: ObligationStatus = ObligationStatus.UNKNOWN


class ContractCase(BaseModel):
    id: str
    relation_type: ContractRelationType
    parties: list[ContractParty] = Field(default_factory=list)
    obligations: list[ContractObligation] = Field(default_factory=list)
    facts: list[str] = Field(default_factory=list)
    legal_sources: list[str] = Field(default_factory=list)
