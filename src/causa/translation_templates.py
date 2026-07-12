import hashlib
import json

from pydantic import BaseModel, ConfigDict, Field, model_validator

from causa.translation import TranslationLevel


class TranslationTemplateDefinition(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    level: TranslationLevel
    title_ru: str
    template_text_ru: str
    required_headings_ru: tuple[str, ...] = Field(min_length=1)
    min_characters: int = Field(ge=1)
    max_characters: int = Field(ge=1)

    @model_validator(mode="after")
    def validate_length_bounds(self) -> "TranslationTemplateDefinition":
        if self.max_characters <= self.min_characters:
            raise ValueError("Максимальная длина шаблона должна превышать минимальную.")
        if not all(heading in self.template_text_ru for heading in self.required_headings_ru):
            raise ValueError("Не все обязательные заголовки присутствуют в шаблоне.")
        return self


class TranslationTemplateSet(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    version: str
    locale: str = "ru-RU"
    templates: tuple[TranslationTemplateDefinition, ...]
    content_hash: str

    @model_validator(mode="after")
    def validate_set(self) -> "TranslationTemplateSet":
        levels = [template.level for template in self.templates]
        if set(levels) != set(TranslationLevel) or len(levels) != len(set(levels)):
            raise ValueError("Набор должен содержать ровно по одному шаблону каждого уровня.")
        if self.content_hash != compute_translation_template_hash(
            self.version,
            self.locale,
            self.templates,
        ):
            raise ValueError("Hash набора шаблонов не соответствует содержимому.")
        return self

    def template_for(self, level: TranslationLevel) -> TranslationTemplateDefinition:
        return next(template for template in self.templates if template.level == level)


def compute_translation_template_hash(
    version: str,
    locale: str,
    templates: tuple[TranslationTemplateDefinition, ...],
) -> str:
    canonical = json.dumps(
        {
            "version": version,
            "locale": locale,
            "templates": [
                template.model_dump(mode="json")
                for template in sorted(templates, key=lambda item: item.level.value)
            ],
        },
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return f"sha256:{hashlib.sha256(canonical.encode('utf-8')).hexdigest()}"


def build_russian_translation_template_set() -> TranslationTemplateSet:
    version = "translation-template-ru-v8"
    templates = (
        TranslationTemplateDefinition(
            level=TranslationLevel.EXECUTIVE,
            title_ru="Краткое правовое резюме",
            template_text_ru=(
                "КРАТКОЕ ПРАВОВОЕ РЕЗЮМЕ\n\n"
                "Вывод\n{conclusion_ru}\n\n"
                "Ключевое основание\n{key_basis_ru}\n\n"
                "Риск и следующий шаг\n{risk_and_next_step_ru}\n\n"
                "{disclaimer_ru}"
            ),
            required_headings_ru=(
                "КРАТКОЕ ПРАВОВОЕ РЕЗЮМЕ",
                "Вывод",
                "Ключевое основание",
                "Риск и следующий шаг",
            ),
            min_characters=300,
            max_characters=1_200,
        ),
        TranslationTemplateDefinition(
            level=TranslationLevel.PROFESSIONAL,
            title_ru="Профессиональное юридическое объяснение",
            template_text_ru=(
                "ПРОФЕССИОНАЛЬНОЕ ЮРИДИЧЕСКОЕ ОБЪЯСНЕНИЕ\n\n"
                "Правовой вывод\n{conclusion_ru}\n\n"
                "Установленные обстоятельства\n{facts_ru}\n\n"
                "Применимая норма и юридическая сила\n{rule_and_authority_ru}\n\n"
                "Формальная проверка\n{formal_result_ru}\n\n"
                "Заключение договора\n{formation_professional_ru}\n\n"
                "Действительность сделки\n{invalidity_professional_ru}\n\n"
                "Обеспечение исполнения обязательств\n{security_professional_ru}\n\n"
                "Перемена лиц и прекращение обязательств\n{dynamics_professional_ru}\n\n"
                "Изменение и расторжение договора\n{termination_professional_ru}\n\n"
                "Контрфактическая чувствительность\n{counterfactual_professional_ru}\n\n"
                "Ответственность и неустойка\n{liability_professional_ru}\n\n"
                "Ограничения и действия эксперта\n{limitations_ru}\n\n"
                "{disclaimer_ru}"
            ),
            required_headings_ru=(
                "ПРОФЕССИОНАЛЬНОЕ ЮРИДИЧЕСКОЕ ОБЪЯСНЕНИЕ",
                "Правовой вывод",
                "Установленные обстоятельства",
                "Применимая норма и юридическая сила",
                "Формальная проверка",
                "Заключение договора",
                "Действительность сделки",
                "Обеспечение исполнения обязательств",
                "Перемена лиц и прекращение обязательств",
                "Изменение и расторжение договора",
                "Контрфактическая чувствительность",
                "Ответственность и неустойка",
                "Ограничения и действия эксперта",
            ),
            min_characters=800,
            max_characters=9_000,
        ),
        TranslationTemplateDefinition(
            level=TranslationLevel.FORENSIC,
            title_ru="Forensic-трассировка юридического вывода",
            template_text_ru=(
                "FORENSIC-ТРАССИРОВКА ЮРИДИЧЕСКОГО ВЫВОДА\n\n"
                "Координаты воспроизведения\n{coordinates_ru}\n\n"
                "Проверенные факты и provenance\n{provenance_ru}\n\n"
                "Формальная норма и constraint set\n{formal_rule_ru}\n\n"
                "Разрешение юридической силы\n{authority_trace_ru}\n\n"
                "Модель заключения договора (статьи 432, 435, 438 и 443 ГК РФ)\n{formation_forensic_ru}\n\n"
                "Модель недействительности сделки (статьи 166–181 ГК РФ)\n{invalidity_forensic_ru}\n\n"
                "Модель обеспечения исполнения (статьи 329–381.2 ГК РФ)\n{security_forensic_ru}\n\n"
                "Модель перемены лиц и прекращения обязательств (статьи 382–419 ГК РФ)\n{dynamics_forensic_ru}\n\n"
                "Модель изменения и расторжения договора (статьи 450–453 ГК РФ)\n{termination_forensic_ru}\n\n"
                "Результаты формальной проверки\n{all_assertions_ru}\n\n"
                "Governance-журнал кандидата\n{governance_ru}\n\n"
                "Сравнение путей рассуждения\n{path_comparison_ru}\n\n"
                "Bounded counterfactual-анализ\n{counterfactual_forensic_ru}\n\n"
                "Модель ответственности (статьи 333 и 401 ГК РФ)\n{liability_forensic_ru}\n\n"
                "Ограничения\n{limitations_ru}\n\n"
                "{disclaimer_ru}"
            ),
            required_headings_ru=(
                "FORENSIC-ТРАССИРОВКА ЮРИДИЧЕСКОГО ВЫВОДА",
                "Координаты воспроизведения",
                "Проверенные факты и provenance",
                "Формальная норма и constraint set",
                "Разрешение юридической силы",
                "Модель заключения договора (статьи 432, 435, 438 и 443 ГК РФ)",
                "Модель недействительности сделки (статьи 166–181 ГК РФ)",
                "Модель обеспечения исполнения (статьи 329–381.2 ГК РФ)",
                "Модель перемены лиц и прекращения обязательств (статьи 382–419 ГК РФ)",
                "Модель изменения и расторжения договора (статьи 450–453 ГК РФ)",
                "Результаты формальной проверки",
                "Governance-журнал кандидата",
                "Сравнение путей рассуждения",
                "Bounded counterfactual-анализ",
                "Модель ответственности (статьи 333 и 401 ГК РФ)",
                "Ограничения",
            ),
            min_characters=1_600,
            max_characters=115_000,
        ),
    )
    return TranslationTemplateSet(
        id=f"translation-template-set:{version}",
        version=version,
        templates=templates,
        content_hash=compute_translation_template_hash(version, "ru-RU", templates),
    )
