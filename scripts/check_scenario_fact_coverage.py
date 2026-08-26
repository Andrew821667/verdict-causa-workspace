"""Быстрая проверка: состав предикатов реальных дел против контракта данных.

Институт, получивший новый предикат, ломает все дела своего института разом —
их факты записаны явным словарём. Полный прогон тестов покажет это через
одиннадцать минут и (до появления этого аудита) по одному делу за раз.

Запускать сразу после правки института:

    .venv/bin/python scripts/check_scenario_fact_coverage.py

Код возврата 1, если расхождение есть, — годится для хука и для CI.
"""

import sys

from causa.institutional.contracts.real_case_scenarios import (
    audit_scenario_fact_coverage,
    render_scenario_fact_coverage_ru,
)


def main() -> int:
    report = audit_scenario_fact_coverage()
    print(render_scenario_fact_coverage_ru(report))
    return 0 if report.complete else 1


if __name__ == "__main__":
    sys.exit(main())
