from enum import Enum


LOCALE_RU = "ru-RU"

GOVERNANCE_STAGE_LABELS_RU = {
    "proposed": "Предложено",
    "type_classification": "Классификация типа",
    "formal_check": "Формальная проверка",
    "source_check": "Проверка источников",
    "benchmark_check": "Проверка на контрольных задачах",
    "red_team_check": "Проверка Red Team",
    "expert_review": "Экспертная проверка",
    "cross_review": "Перекрестная экспертная проверка",
    "sandbox": "Предактивационная песочница",
    "active": "Активно",
    "revalidation": "Повторная валидация",
    "rejected": "Отклонено",
    "rolled_back": "Откачено",
}

CANDIDATE_TYPE_LABELS_RU = {
    "meta_principle": "Мета-принцип",
    "calibration_rule": "Правило калибровки",
    "gap_heuristic": "Эвристика пробела",
    "conflict_resolution_pattern": "Паттерн разрешения противоречий",
    "counterfactual_sensitivity_pattern": "Паттерн контрфактической чувствительности",
    "argument_template": "Аргументационный шаблон",
    "translation_pattern": "Паттерн юридического объяснения",
}

FAILURE_TYPE_LABELS_RU = {
    "hallucinated_source_grounding": "Ложная привязка к источнику",
    "bad_formalization": "Ошибочная формализация",
    "wrong_temporal_applicability": "Неверная временная применимость",
    "wrong_authority_ranking": "Неверное ранжирование юридической силы",
    "overbroad_candidate_principle": "Чрезмерно широкий принцип-кандидат",
    "translation_distortion": "Искажение при юридическом объяснении",
    "escalation_failure": "Ошибка эскалации на проверку",
    "false_confidence_inflation": "Необоснованное завышение уверенности",
    "privacy_leakage_risk": "Риск утечки конфиденциальных данных",
    "benchmark_overfitting": "Переобучение на контрольных задачах",
}

SLA_MODE_LABELS_RU = {
    "draft": "Черновой",
    "standard": "Стандартный",
    "deep": "Углубленный",
    "research": "Исследовательский",
}

RISK_TIER_LABELS_RU = {
    "t1_reference": "T1: справочная ориентация",
    "t2_internal_memo": "T2: внутренняя записка",
    "t3_draft_letter": "T3: проект письма или правовой позиции",
    "t4_procedural_draft": "T4: проект процессуального документа",
    "t5_high_stakes_recommendation": "T5: рекомендация с высокими рисками",
    "t6_ready_to_file_document": "T6: готовый к подаче документ",
}

AUTHORITY_LEVEL_LABELS_RU = {
    "constitutional": "конституционный уровень",
    "statutory": "уровень закона",
    "regulatory": "уровень подзаконного регулирования",
    "judicial": "уровень судебного толкования",
    "contractual": "уровень договорного условия",
    "factual": "уровень фактического материала",
}

AUTHORITY_RULE_LABELS_RU = {
    "temporal_applicability": "временная применимость",
    "higher_authority": "приоритет источника большей юридической силы",
    "lex_specialis": "приоритет специальной нормы",
    "unresolved_equal_authority": "неразрешенное равенство юридической силы",
}


def label_ru(value: str | Enum, labels: dict[str, str]) -> str:
    machine_value = value.value if isinstance(value, Enum) else value
    try:
        return labels[machine_value]
    except KeyError as error:
        raise ValueError(f"Для значения {machine_value!r} отсутствует русская метка.") from error
