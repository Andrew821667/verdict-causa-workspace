"""Таксономия противоречий в договорных делах.

Здесь остались только те имена противоречий, которые действительно проверяются.

Прежде рядом лежал `CONTRACT_CONTRADICTION_TYPES` — 45 имён «для разметки
противоречий внутри одного института». Ни одно из них не импортировалось никуда,
кроме перечня файлов пакета: список описывал предметную область и не влиял ни на
что. Он удалён по тому же правилу, по которому в выпуске `0.97.0` были удалены
две объявленные, но неспособные сработать сверки: объявленное и не проверяемое
читается как покрытие, которого нет. Когда для внутриинститутских противоречий
появится проверяющий их слой, имена вернутся вместе с ним и с тестом.

`CROSS_INSTITUTE_CONTRADICTION_TYPES` устроен иначе: каждое имя из этого набора
обязано проверяться слоем сверки `general_consistency` и соответствовать полю
его оценки. Соответствие закреплено тестом
`test_every_declared_cross_institute_type_is_checked`, а достижимость каждого
типа в полном конвейере — тестом
`test_every_declared_conflict_fires_end_to_end`. Поэтому набор не может ни
снова стать перечнем без потребителей, ни содержать сверку, которая объявлена,
но сработать не способна.
"""

CROSS_INSTITUTE_CONTRADICTION_TYPES = (
    "capacity_invalidity_conflict",
    "entity_capacity_invalidity_conflict",
    "limited_capacity_invalidity_conflict",
    "minor_capacity_invalidity_conflict",
    "consent_invalidity_conflict",
    "circulation_lawfulness_conflict",
    "formation_form_observance_conflict",
    "circulation_public_interest_conflict",
)
