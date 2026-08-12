/**
 * Типы данных стенда.
 *
 * Это описание того, что присылает Python, а не самостоятельная модель.
 * Ни одного правила фронтенд не повторяет: тексты, оценки и подписи
 * вычислены конвейером и приходят готовыми.
 */

export type Tone = "neutral" | "good" | "warn" | "stop";

export interface VerdictMetric {
  label_ru: string;
  value_ru: string;
  tone: Tone;
  hint_ru: string;
}

export interface CaseVerdict {
  state: string;
  tone: Tone;
  headline_ru: string;
  detail_ru: string;
  qualifiers_ru: string[];
  next_step_ru: string;
  metrics: VerdictMetric[];
}

export interface ClusterCandidate {
  institute: string;
  title_ru: string;
  predicate: string;
  group_ru: string;
  articles_ru: string;
  certainty: "single" | "competing" | "needs_human";
  certainty_ru: string;
  basis_ru: string;
  specialises: string | null;
  displaced_by_special_rule: boolean;
}

export interface CaseQualification {
  candidates: ClusterCandidate[];
  primary: ClusterCandidate | null;
  competing: boolean;
  notes_ru: string[];
}

export interface ConclusionStep {
  code: string;
  question_ru: string;
  value: boolean | string;
  text_ru: string;
  source_refs: string[];
}

export interface DebateSide {
  title_ru: string;
  origin_ru: string;
  points_ru: string[];
}

export interface ReasoningView {
  line: ConclusionStep[];
  debate: {
    disclaimer_ru: string;
    supporting: DebateSide;
    opposing: DebateSide;
    critic: DebateSide;
  };
  registers: {
    level: string;
    level_ru: string;
    text: string;
    faithfulness_passed: boolean;
    usability_passed: boolean;
  }[];
  all_assertions: ConclusionStep[];
  notes_ru: string[];
}

export interface TypedGap {
  id: string;
  kind: "decisive_fact" | "human_review" | "not_explored";
  kind_ru: string;
  question_ru: string;
  consequence_ru: string[];
  closes_with_ru: string[];
  institute: string | null;
  institute_ru: string | null;
  blocking: boolean;
  /** Как пробел закрывается: утверждением о факте, датой или никак. */
  closure_kind: "asserted_fact" | "supplied_date" | null;
  /** Какие факты станут какими, если оператор подтвердит их документом. */
  fact_updates: Record<string, boolean>;
}

export interface MapNode {
  id: string;
  kind: "source" | "evidence" | "institute" | "layer";
  kind_ru: string;
  title_ru: string;
  detail_ru: string;
  needs_human: boolean;
}

export interface MapEdge {
  source: string;
  target: string;
  connected: boolean;
  reason_ru: string;
  open_debt: boolean;
}

export interface SourceLabel {
  id: string;
  label_ru: string;
  kind_ru: string;
  recognised: boolean;
}

export interface RemarkOutcome {
  remark_id: string;
  kind_ru: string;
  case_effect_ru: string;
  system_effect_ru: string;
  candidate: { id: string; statement: string; status: string } | null;
  candidate_type: string | null;
  required_stages_ru: string[];
  notes_ru: string[];
}

export interface CaseView {
  case_id: string;
  title_ru: string;
  workspace_id: string;
  caveat_ru: string;
  verdict: CaseVerdict;
  qualification: CaseQualification;
  reasoning: ReasoningView;
  gaps: { gaps: TypedGap[]; notes_ru: string[] };
  map: { nodes: MapNode[]; edges: MapEdge[]; notes_ru: string[] };
  remarks: { outcomes: RemarkOutcome[] };
  sources: SourceLabel[];
  documents: { id: string; filename: string; size_bytes: number; sha256: string }[];
  closures: { gap_id: string; document_id: string; statement_ru: string }[];
}

export interface CaseCard {
  case_id: string;
  title_ru: string;
  workspace_id: string;
  cluster_ru: string;
  blocking_gaps: number;
  open_debt_ru: string[];
  needs_human: boolean;
}

export interface Workspace {
  id: string;
  title_ru: string;
  sla_mode_ru: string;
  risk_tier_ru: string;
  cases: CaseCard[];
}

export interface Desktop {
  organisation: {
    id: string;
    title_ru: string;
    operators: { id: string; display_name: string; role_ru: string; rights_ru: string[] }[];
  };
  operator: { id: string; display_name: string; role_ru: string; rights_ru: string[] };
  workspaces: Workspace[];
}

export interface Dataset {
  version: string;
  desktop: Desktop;
  cases: Record<string, CaseView>;
  remark_outcomes: Record<string, RemarkOutcome>;
  placeholder: string;
}
