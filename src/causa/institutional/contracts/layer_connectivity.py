"""Аудит связности: почему вывод института доходит до слоя общих положений или нет.

## Зачем аудит

Прогон реальных дел через весь конвейер показал, что слой общих положений
получает входы от 13 институтов, а 75 в него не идут. Само по себе это ничего не
говорит: для большинства так и должно быть — модель складского хранения не решает
судьбу договора вообще. Но пока причина не записана по каждому институту,
«не идёт» неотличимо от «забыли провести».

Тот же дефект уже дважды находился в этом проекте: 45 объявленных типов
противоречий без единого потребителя и две объявленные сверки, неспособные
сработать. Лечение то же — по каждому институту либо связь, либо записанная
причина, и тест, не дающий оставить запись пустой.

## Категории

`SPECIAL_TYPE`
    Специальный договорный тип части второй ГК РФ. Его выводы относятся к
    правилам этого типа, а не к судьбе договора вообще. Слой называется «общие
    положения» не случайно: провести туда вывод модели хранения — значит размыть
    его смысл.

`DUPLICATED_UPSTREAM`
    Тот же правовой результат уже поступает в слой от другого института.
    Проводить его дважды — создать два источника одного факта и вернуть ровно ту
    проблему, ради которой строился слой сверки.

`REMEDY_SCOPE`
    Вывод о средствах защиты, размере ответственности или порядке их
    осуществления, а не о судьбе требования. Слой выводит правовые последствия,
    а не считает суммы.

`FORMATION_STAGE`
    Вывод относится к стадии до заключения договора либо к форме его
    заключения; в слой он попадает уже переработанным в заключённость.

`SHOULD_BE_WIRED`
    Обоснования нет. Вывод по праву меняет судьбу требования, но до слоя не
    доходит. Это открытый долг, а не решение.

Категория `SHOULD_BE_WIRED` — единственная, которая обязана уменьшаться. Тест
`test_open_wiring_debt_is_named` перечисляет её содержимое, чтобы долг был виден
в отчёте, а не только в этом файле.
"""

from enum import Enum

from pydantic import BaseModel, Field

LAYER_CONNECTIVITY_VERSION = "contracts-layer-connectivity-audit-v0"


class ConnectivityVerdict(str, Enum):
    SPECIAL_TYPE = "special_type"
    DUPLICATED_UPSTREAM = "duplicated_upstream"
    REMEDY_SCOPE = "remedy_scope"
    FORMATION_STAGE = "formation_stage"
    SHOULD_BE_WIRED = "should_be_wired"


VERDICT_LABELS_RU = {
    ConnectivityVerdict.SPECIAL_TYPE: "специальный договорный тип",
    ConnectivityVerdict.DUPLICATED_UPSTREAM: "результат уже поступает от другого института",
    ConnectivityVerdict.REMEDY_SCOPE: "средства защиты и размер, а не судьба требования",
    ConnectivityVerdict.FORMATION_STAGE: "стадия заключения, попадает в слой как заключённость",
    ConnectivityVerdict.SHOULD_BE_WIRED: "обоснования нет — открытый долг",
}

_SPECIAL = ConnectivityVerdict.SPECIAL_TYPE
_DUP = ConnectivityVerdict.DUPLICATED_UPSTREAM
_REMEDY = ConnectivityVerdict.REMEDY_SCOPE
_STAGE = ConnectivityVerdict.FORMATION_STAGE
_DEBT = ConnectivityVerdict.SHOULD_BE_WIRED

_SPECIAL_TYPE_REASON = (
    "специальный договорный тип части второй ГК РФ: выводы относятся к его "
    "собственным правилам, а не к судьбе договора вообще"
)

#: Почему вывод института не доходит до слоя общих положений.
LAYER_CONNECTIVITY_AUDIT: dict[str, tuple[ConnectivityVerdict, str]] = {
    # --- Открытый долг: обоснования нет -------------------------------------
    "meeting_decisions": (
        _DEBT,
        "решение собрания обязательно для всех участников (статья 181.1), и его "
        "ничтожность по статье 181.5 подрывает договорное условие, которое на этом "
        "решении держится (дело 45-КГ23-2-К7). Связи между решением и конкретным "
        "условием договора в модели пока нет, поэтому долг открыт, а не закрыт",
    ),
    "obligation_dynamics": (
        _DEBT,
        "прекращение обязательства зачётом, новацией, прощением долга или "
        "невозможностью исполнения (глава 26) прекращает и требование. Слой получает "
        "от института расторжения только договорное расторжение, а прекращение "
        "обязательства до него не доходит",
    ),
    # --- Дублирование: тот же результат приходит от другого института --------
    "freedom": (
        _DUP,
        "соответствие договора императивным нормам слой получает через модель "
        "недействительности (статья 168), а не от модели свободы договора",
    ),
    "security": (
        _DUP,
        "обеспечение следует судьбе основного обязательства: его существование и "
        "недействительность слой уже получает от моделей заключения и "
        "недействительности",
    ),
    "temporal": (
        _DUP,
        "наступление срока исполнения слой получает через вывод о нарушении "
        "обязательства, а не отдельным входом",
    ),
    "temporal_effect": (
        _DUP,
        "момент заключения договора слой получает от модели заключения "
        "(статьи 432–443); отдельный вход дублировал бы тот же факт",
    ),
    "authority": (
        _DUP,
        "порок полномочий слой получает от модели представительства "
        "(статьи 182–189) как `unauthorized_representation_detected`",
    ),
    "unjust_enrichment": (
        _DUP,
        "возврат полученного по недействительной сделке слой выводит сам из "
        "реституции (статья 167); кондикция вне этого случая договорную судьбу не "
        "меняет",
    ),
    # --- Стадия заключения ---------------------------------------------------
    "precontractual": (
        _STAGE,
        "недобросовестность на переговорах порождает самостоятельное требование о "
        "возмещении, а не меняет судьбу заключённого договора (статья 434.1)",
    ),
    "preliminary": (
        _STAGE,
        "предварительный договор порождает обязанность заключить основной; для слоя "
        "значим уже основной договор и его заключённость (статья 429)",
    ),
    "option": (
        _STAGE,
        "опцион и опционный договор описывают порядок заключения основного договора; "
        "в слой попадает результат — заключённость (статьи 429.2–429.3)",
    ),
    "framework": (
        _STAGE,
        "рамочный и абонентский договор описывают способ определения условий; "
        "в слой попадает заключённость конкретного обязательства (статьи 429.1, 429.4)",
    ),
    "procedure": (
        _STAGE,
        "обязательное заключение и торги описывают порядок заключения; его результат "
        "слой получает как заключённость (статьи 445–449)",
    ),
    "public_contract": (
        _STAGE,
        "публичность договора ограничивает свободу отказа от заключения; заключённый "
        "договор попадает в слой на общих основаниях (статья 426)",
    ),
    "adhesion": (
        _STAGE,
        "присоединение к условиям даёт право требовать их изменения, а не порочит "
        "договор; в слой попадает заключённость (статья 428)",
    ),
    "third_party": (
        _STAGE,
        "договор в пользу третьего лица определяет, кто вправе требовать исполнения, "
        "а не судьбу самого договора (статья 430)",
    ),
    "interpretation": (
        _STAGE,
        "толкование определяет содержание условия, а не действительность договора; "
        "результат толкования приходит в слой уже в виде фактов (статья 431)",
    ),
    "representations": (
        _STAGE,
        "недостоверность заверений даёт убытки и право на отказ, а само по себе "
        "договор не порочит (статья 431.2)",
    ),
    "general_obligations": (
        _STAGE,
        "общие положения об обязательствах описывают их возникновение и стороны; "
        "в слой обязанность приходит через вывод о договорной обязанности "
        "(статьи 307–308.3)",
    ),
    # --- Средства защиты и размер --------------------------------------------
    "liability": (
        _REMEDY,
        "основания и размер ответственности, включая снижение неустойки, не меняют "
        "существование требования (статьи 333–401)",
    ),
    "performance_remedies": (
        _REMEDY,
        "выбор средства защиты при нарушении не меняет судьбу договора; факт "
        "нарушения слой получает отдельным входом (статьи 309–328, 393)",
    ),
    "moral_harm": (
        _REMEDY,
        "компенсация морального вреда — самостоятельное требование, договорную "
        "судьбу не затрагивает (статьи 1099–1101)",
    ),
    "settlements": (
        _REMEDY,
        "формы расчётов описывают порядок исполнения денежной обязанности, а не её "
        "существование (статьи 861–885)",
    ),
    "tort_general": (
        _REMEDY,
        "деликтное обязательство возникает вне договора и договорную судьбу не "
        "меняет (статьи 1064–1083)",
    ),
    "tort_life_health": (
        _REMEDY,
        "возмещение вреда жизни и здоровью — внедоговорное требование (статьи 1084–1094)",
    ),
    "product_liability": (
        _REMEDY,
        "ответственность за вред вследствие недостатков товара наступает независимо "
        "от договорной связи (статьи 1095–1098)",
    ),
}

_SPECIAL_TYPE_INSTITUTES = (
    "agency",
    "annuity",
    "bank_account",
    "bank_deposit",
    "barter",
    "building_lease",
    "carriage",
    "commercial_credit",
    "commission",
    "construction_contract",
    "consumer_work",
    "contractation",
    "credit",
    "design_work",
    "energy_supply",
    "enterprise_lease",
    "enterprise_sale",
    "factoring",
    "forwarding",
    "franchise",
    "games",
    "gift",
    "gratuitous_use",
    "insurance",
    "insurance_settlement",
    "lease",
    "leasing",
    "loan",
    "mandate",
    "negotiorum_gestio",
    "paid_services",
    "partnership",
    "public_promise",
    "real_estate_sale",
    "rental",
    "research_work",
    "residential_lease",
    "retail_sale",
    "sale",
    "special_storage",
    "state_supply",
    "state_work",
    "storage",
    "supply",
    "trust_management",
    "vehicle_lease",
    "warehouse_storage",
    "work_contract",
)

for _name in _SPECIAL_TYPE_INSTITUTES:
    LAYER_CONNECTIVITY_AUDIT[_name] = (_SPECIAL, _SPECIAL_TYPE_REASON)


class ConnectivityEntry(BaseModel):
    institute: str
    verdict: ConnectivityVerdict
    verdict_ru: str
    reason_ru: str


class LayerConnectivityReport(BaseModel):
    version: str = LAYER_CONNECTIVITY_VERSION
    feeding_the_layer: int = 0
    audited: int = 0
    by_verdict: dict[str, int] = Field(default_factory=dict)
    open_wiring_debt: list[ConnectivityEntry] = Field(default_factory=list)
    entries: list[ConnectivityEntry] = Field(default_factory=list)
    unaudited: list[str] = Field(default_factory=list)
    notes_ru: list[str] = Field(default_factory=list)


def audit_layer_connectivity() -> LayerConnectivityReport:
    """Свести аудит связности в отчёт и назвать открытый долг."""
    from causa.institutional.contracts.real_case_pipeline import LAYER_FED_BY
    from causa.institutional.contracts.reviewed_analysis import ReviewedContractAnalysisResult

    layers = {"general_effects", "general_consistency"}
    institutes = sorted(
        name[: -len("_evaluation")]
        for name in ReviewedContractAnalysisResult.model_fields
        if name.endswith("_evaluation")
    )
    not_feeding = [name for name in institutes if name not in LAYER_FED_BY and name not in layers]
    entries = [
        ConnectivityEntry(
            institute=name,
            verdict=LAYER_CONNECTIVITY_AUDIT[name][0],
            verdict_ru=VERDICT_LABELS_RU[LAYER_CONNECTIVITY_AUDIT[name][0]],
            reason_ru=LAYER_CONNECTIVITY_AUDIT[name][1],
        )
        for name in not_feeding
        if name in LAYER_CONNECTIVITY_AUDIT
    ]
    unaudited = [name for name in not_feeding if name not in LAYER_CONNECTIVITY_AUDIT]
    by_verdict: dict[str, int] = {}
    for entry in entries:
        by_verdict[entry.verdict.value] = by_verdict.get(entry.verdict.value, 0) + 1
    debt = [entry for entry in entries if entry.verdict is ConnectivityVerdict.SHOULD_BE_WIRED]

    notes = [
        f"Слой общих положений питают {len(LAYER_FED_BY)} институтов из "
        f"{len(institutes) - len(layers)}; остальные {len(not_feeding)} разобраны здесь.",
        "«Не доходит» без записанной причины неотличимо от «забыли провести», поэтому "
        "причина обязательна для каждого института.",
    ]
    if debt:
        notes.append(
            "Открытый долг связности: "
            + ", ".join(entry.institute for entry in debt)
            + ". Это единственная категория, которая обязана уменьшаться."
        )
    if unaudited:
        notes.append("Институты без записи в аудите: " + ", ".join(unaudited) + ".")
    return LayerConnectivityReport(
        feeding_the_layer=len(LAYER_FED_BY),
        audited=len(entries),
        by_verdict=dict(sorted(by_verdict.items())),
        open_wiring_debt=debt,
        entries=entries,
        unaudited=unaudited,
        notes_ru=notes,
    )
