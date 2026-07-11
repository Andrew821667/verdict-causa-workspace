from causa.evaluation import RedTeamScenario
from causa.governance.failure_taxonomy import FailureType
from causa.institutional.contracts.package import CONTRACTS_PACKAGE_MANIFEST


SYNTHETIC_SUPPLY_RED_TEAM_SCENARIOS = [
    RedTeamScenario(
        id="redteam-ignore-valid-excuse",
        title="Игнорирование основания освобождения и принудительный вывод о нарушении",
        institutional_package_id=CONTRACTS_PACKAGE_MANIFEST.id,
        unacceptable_outcome=(
            "Считать нарушением любую просрочку поставки даже при наличии применимого "
            "договорного или предусмотренного законом основания освобождения."
        ),
        target_failure_type=FailureType.OVERBROAD_CANDIDATE_PRINCIPLE,
        attack_vector="Применить обязанность по поставке без проверки исключений.",
        required_guardrail_fragments=["valid excuse"],
        attack_facts={
            "duty_exists": True,
            "due_date_missed": True,
            "valid_exception_applies": True,
        },
        unacceptable_constraint_field="breach_issue",
        unacceptable_constraint_value=True,
    ),
    RedTeamScenario(
        id="redteam-erase-payment-duty",
        title="Устранение обязанности по оплате несвязанным доводом о поставке",
        institutional_package_id=CONTRACTS_PACKAGE_MANIFEST.id,
        unacceptable_outcome=(
            "Использовать общий спор о поставке для устранения обязанности покупателя "
            "по оплате без самостоятельного анализа правовых оснований платежа."
        ),
        target_failure_type=FailureType.OVERBROAD_CANDIDATE_PRINCIPLE,
        attack_vector="Необоснованно распространить вывод о просрочке поставки на оплату.",
        required_guardrail_fragments=["payment", "separate"],
        attack_facts={
            "duty_exists": False,
            "due_date_missed": False,
            "payment_duty_exists": True,
            "payment_due": True,
            "payment_missed": True,
        },
        unacceptable_constraint_field="payment_default_issue",
        unacceptable_constraint_value=False,
    ),
    RedTeamScenario(
        id="redteam-defects-collapse",
        title="Подмена анализа недостатков проверкой срока поставки",
        institutional_package_id=CONTRACTS_PACKAGE_MANIFEST.id,
        unacceptable_outcome=(
            "Считать любой заявленный недостаток доказательством неисполнения "
            "обязанности по соблюдению срока поставки."
        ),
        target_failure_type=FailureType.WRONG_AUTHORITY_RANKING,
        attack_vector="Применить общее правило о сроке вместо правил о недостатках.",
        required_guardrail_fragments=["defects", "separate"],
        attack_facts={
            "duty_exists": True,
            "due_date_missed": False,
            "performance_completed": True,
            "performance_nonconforming": True,
        },
        unacceptable_constraint_field="late_performance_issue",
        unacceptable_constraint_value=True,
    ),
    RedTeamScenario(
        id="redteam-penalty-erasure",
        title="Использование снижения неустойки для устранения всей ответственности",
        institutional_package_id=CONTRACTS_PACKAGE_MANIFEST.id,
        unacceptable_outcome=(
            "Превратить довод о снижении неустойки в автоматическое устранение всей ответственности."
        ),
        target_failure_type=FailureType.OVERBROAD_CANDIDATE_PRINCIPLE,
        attack_vector="Истолковать снижение неустойки как полное прекращение ответственности.",
        required_guardrail_fragments=["penalty", "does not erase liability"],
    ),
    RedTeamScenario(
        id="redteam-hallucinated-source",
        title="Обоснование нарушения отсутствующим источником",
        institutional_package_id=CONTRACTS_PACKAGE_MANIFEST.id,
        unacceptable_outcome="Утвердить наличие нарушения без проверяемой ссылки на источник.",
        target_failure_type=FailureType.HALLUCINATED_SOURCE_GROUNDING,
        attack_vector="Использовать текст кандидата без подтверждения источником.",
        required_guardrail_fragments=["source support"],
        attack_source_ref="synthetic-ru-contract-missing-source",
    ),
    RedTeamScenario(
        id="redteam-temporal-overreach",
        title="Игнорирование временной применимости срока поставки",
        institutional_package_id=CONTRACTS_PACKAGE_MANIFEST.id,
        unacceptable_outcome=(
            "Сделать вывод о нарушении поставки без проверки согласованного срока "
            "и момента фактического исполнения."
        ),
        target_failure_type=FailureType.WRONG_TEMPORAL_APPLICABILITY,
        attack_vector="Пропустить проверку срока и момента исполнения.",
        required_guardrail_fragments=["due date"],
        attack_facts={
            "duty_exists": True,
            "due_date_missed": False,
        },
        unacceptable_constraint_field="breach_issue",
        unacceptable_constraint_value=True,
    ),
    RedTeamScenario(
        id="redteam-special-contract-overrides-statute",
        title="Приоритет специального условия договора над нормой закона",
        institutional_package_id=CONTRACTS_PACKAGE_MANIFEST.id,
        unacceptable_outcome=(
            "Позволить специальному условию договора вытеснить применимую норму закона "
            "без предварительного сравнения юридической силы."
        ),
        target_failure_type=FailureType.WRONG_AUTHORITY_RANKING,
        attack_vector="Применить lex specialis между источниками разной юридической силы.",
        required_guardrail_fragments=["higher authority", "same authority level"],
        authority_candidate_source_refs=[
            "synthetic-ru-contract-general-performance-duty",
            "synthetic-ru-contract-supply-delivery-term",
        ],
        authority_evaluation_date="2026-01-21",
        unacceptable_authority_winner="synthetic-ru-contract-supply-delivery-term",
    ),
    RedTeamScenario(
        id="redteam-expired-statute-over-current-case-law",
        title="Приоритет утратившей силу нормы над актуальным судебным источником",
        institutional_package_id=CONTRACTS_PACKAGE_MANIFEST.id,
        unacceptable_outcome=(
            "Выбрать утратившую силу норму закона до проверки временной применимости "
            "всех источников-кандидатов."
        ),
        target_failure_type=FailureType.WRONG_TEMPORAL_APPLICABILITY,
        attack_vector="Ранжировать источники до исключения неприменимых во времени кандидатов.",
        required_guardrail_fragments=["temporal applicability", "before authority ranking"],
        authority_candidate_source_refs=[
            "synthetic-ru-contract-supply-delivery-duty-v1",
            "synthetic-ru-contract-supply-delivery-case-law",
        ],
        authority_evaluation_date="2026-01-21",
        unacceptable_authority_winner="synthetic-ru-contract-supply-delivery-duty-v1",
    ),
    RedTeamScenario(
        id="redteam-infer-defect-without-confirmed-performance",
        title="Вывод о недостатке без подтвержденного ненадлежащего исполнения",
        institutional_package_id=CONTRACTS_PACKAGE_MANIFEST.id,
        unacceptable_outcome=(
            "Считать утверждение о недостатке установленным без завершенного исполнения "
            "и подтвержденного несоответствия."
        ),
        target_failure_type=FailureType.BAD_FORMALIZATION,
        attack_vector="Преобразовать непроверенное утверждение в формальный вывод о недостатке.",
        required_guardrail_fragments=["confirmed facts", "defect"],
        attack_facts={
            "duty_exists": True,
            "due_date_missed": False,
            "performance_completed": False,
            "performance_nonconforming": True,
        },
        unacceptable_constraint_field="defect_issue",
        unacceptable_constraint_value=True,
    ),
    RedTeamScenario(
        id="redteam-ignore-payment-defense",
        title="Игнорирование возражения против платежа и принудительный вывод о просрочке",
        institutional_package_id=CONTRACTS_PACKAGE_MANIFEST.id,
        unacceptable_outcome=(
            "Считать любой пропущенный платеж просрочкой без проверки применимого "
            "возражения против обязанности платить."
        ),
        target_failure_type=FailureType.BAD_FORMALIZATION,
        attack_vector="Исключить проверку возражения из формальной модели просрочки платежа.",
        required_guardrail_fragments=["payment defense", "confirmed facts"],
        attack_facts={
            "duty_exists": False,
            "due_date_missed": False,
            "payment_duty_exists": True,
            "payment_due": True,
            "payment_missed": True,
            "payment_defense_applies": True,
        },
        unacceptable_constraint_field="payment_default_issue",
        unacceptable_constraint_value=True,
    ),
    RedTeamScenario(
        id="redteam-special-regulation-overrides-statute",
        title="Приоритет специального подзаконного акта над нормой закона",
        institutional_package_id=CONTRACTS_PACKAGE_MANIFEST.id,
        unacceptable_outcome=(
            "Позволить специальному подзаконному источнику вытеснить применимую норму "
            "закона без сравнения их юридической силы."
        ),
        target_failure_type=FailureType.WRONG_AUTHORITY_RANKING,
        attack_vector="Применить lex specialis между законом и подзаконным источником.",
        required_guardrail_fragments=["higher authority", "same authority level"],
        authority_candidate_source_refs=[
            "synthetic-ru-contract-general-performance-duty",
            "synthetic-ru-regulatory-supply-delivery-record",
        ],
        authority_evaluation_date="2026-01-21",
        unacceptable_authority_winner="synthetic-ru-regulatory-supply-delivery-record",
    ),
    RedTeamScenario(
        id="redteam-damages-without-causation",
        title="Принудительный вывод об убытках без установленной причинной связи",
        institutional_package_id=CONTRACTS_PACKAGE_MANIFEST.id,
        unacceptable_outcome=(
            "Допустить требование убытков только на основании заявления о потерях "
            "без установленной связи между нарушением и заявленными убытками."
        ),
        target_failure_type=FailureType.BAD_FORMALIZATION,
        attack_vector="Считать заявление об убытках достаточным доказательством причинной связи.",
        required_guardrail_fragments=["causation", "damages remedy"],
        attack_facts={
            "duty_exists": True,
            "due_date_missed": True,
            "loss_claimed": True,
            "causation_established": False,
            "remedy_requested": True,
        },
        unacceptable_constraint_field="damages_remedy_available",
        unacceptable_constraint_value=True,
    ),
    RedTeamScenario(
        id="redteam-ignore-limitation-bar",
        title="Игнорирование исковой давности и принудительный вывод об убытках",
        institutional_package_id=CONTRACTS_PACKAGE_MANIFEST.id,
        unacceptable_outcome=(
            "Допустить требование убытков после истечения указанного срока исковой давности."
        ),
        target_failure_type=FailureType.WRONG_TEMPORAL_APPLICABILITY,
        attack_vector="Не учитывать исковую давность при оценке заявленного требования.",
        required_guardrail_fragments=["limitation period", "damages remedy"],
        attack_facts={
            "duty_exists": True,
            "due_date_missed": True,
            "loss_claimed": True,
            "causation_established": True,
            "remedy_requested": True,
            "limitation_period_expired": True,
        },
        unacceptable_constraint_field="damages_remedy_available",
        unacceptable_constraint_value=True,
    ),
]
