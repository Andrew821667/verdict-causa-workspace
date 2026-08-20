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

/** Относится ли дело к тому, что система умеет разбирать. */
export type CaseScope = "in_scope" | "out_of_scope_suspected" | "undetermined";

export interface CaseQualification {
  candidates: ClusterCandidate[];
  primary: ClusterCandidate | null;
  competing: boolean;
  scope: CaseScope;
  /** Заявленные по делу статьи, не покрытые ни одним институтом. */
  uncovered_articles: string[];
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

export interface RegisterText {
  level: string;
  level_ru: string;
  text: string;
  faithfulness_passed: boolean;
  usability_passed: boolean;
}

export interface ReasoningView {
  line: ConclusionStep[];
  debate: {
    disclaimer_ru: string;
    supporting: DebateSide;
    opposing: DebateSide;
    critic: DebateSide;
  };
  /** Изложение для человека: коротко для решения и разбор для юриста. */
  registers: RegisterText[];
  /** Машинная трассировка. Служебный материал, а не текст в дело. */
  trace: RegisterText | null;
  all_assertions: ConclusionStep[];
  notes_ru: string[];
}

/** Фабула дела: что произошло, изложенное из проверенных фактов. */
export interface StoryFact {
  fact: string;
  text_ru: string;
  established: boolean;
  source_refs: string[];
}

export interface CaseStory {
  summary_ru: string;
  question_ru: string;
  sections: { title_ru: string; facts: StoryFact[] }[];
  notes_ru: string[];
}

/** Проект процессуального документа. */
export interface CourtFiling {
  kind: string;
  title_ru: string;
  sections: { title_ru: string; paragraphs_ru: string[] }[];
  checks: { code: string; title_ru: string; passed: boolean; detail_ru: string }[];
  ready_to_file: boolean;
  blocker_ru: string;
  text: string;
}

/** Схема правоотношения и цепочка до итога. */
export type LinkState = "performed" | "breached" | "established" | "absent";

export interface RelationScheme {
  parties: { id: string; title_ru: string; role_ru: string }[];
  links: {
    id: string;
    source: string;
    target: string;
    title_ru: string;
    state: LinkState;
    state_ru: string;
    detail_ru: string;
    articles_ru: string;
  }[];
  stages: { id: string; title_ru: string; reached: boolean; detail_ru: string }[];
  outcome_ru: string;
  outcome_detail_ru: string;
  notes_ru: string[];
}

/** Текст приложенного документа — или запись о том, почему его нет. */
export interface ExtractedText {
  document_id: string;
  filename: string;
  extracted: boolean;
  format_ru: string;
  text: string;
  characters: number;
  truncated: boolean;
  note_ru: string;
}

/** Места в документах, совпавшие со словами открытого вопроса. */
export interface GapEvidenceHints {
  gap_id: string;
  fragments: {
    document_id: string;
    filename: string;
    matched_ru: string;
    quote_ru: string;
    position: number;
  }[];
  dates: {
    document_id: string;
    filename: string;
    value: string;
    quote_ru: string;
    position: number;
  }[];
  note_ru: string;
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
  story: CaseStory;
  verdict: CaseVerdict;
  qualification: CaseQualification;
  reasoning: ReasoningView;
  gaps: { gaps: TypedGap[]; notes_ru: string[] };
  map: { nodes: MapNode[]; edges: MapEdge[]; notes_ru: string[] };
  scheme: RelationScheme;
  remarks: { outcomes: RemarkOutcome[] };
  sources: SourceLabel[];
  documents: { id: string; filename: string; size_bytes: number; sha256: string }[];
  closures: { gap_id: string; document_id: string; statement_ru: string }[];
  document_texts: ExtractedText[];
  hints: GapEvidenceHints[];
  filing: CourtFiling;
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
