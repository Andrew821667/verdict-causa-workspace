"use client";

import { useState } from "react";
import type { CaseView } from "@/lib/types";
import { Card, Chip, SectionTitle, Note, YesNo } from "./primitives";

/**
 * Наладка: машинная трассировка и полный список утверждений.
 *
 * Этот материал раньше стоял во вкладке «Изложение» под подписью «для суда, с
 * координатами». Подпись вводила в заблуждение: судья такой текст не читает.
 * Достаточно посмотреть, из чего он состоит — координаты воспроизведения,
 * constraint set, provenance, governance-журнал. Правила проверки конвейера
 * это подтверждают: именно для этого уровня снижен порог кириллицы и снята
 * проверка на утечку машинной детали.
 *
 * Материал не выброшен: воспроизводимость вывода — свойство системы, за
 * которое отвечает тот, кто её проверяет. Он просто перестал занимать место
 * в юридической работе.
 */
export function Diagnostics({ view }: { view: CaseView }) {
  const [showAll, setShowAll] = useState(false);
  const trace = view.reasoning.trace;
  const assertions = view.reasoning.all_assertions;
  const shown = showAll ? assertions : assertions.slice(0, 12);

  return (
    <div className="space-y-4">
      <Note>
        Это служебный раздел. Он нужен при наладке системы и проверке
        воспроизводимости вывода, а не при решении юридического вопроса. Для
        работы по делу — вкладки «Обзор», «Разбор» и «Изложение».
      </Note>

      <Card className="p-5 sm:p-6">
        <SectionTitle hint="Версии моделей, на которых собрано это окно. По ним разбор воспроизводится.">
          Версии
        </SectionTitle>
        <div className="flex flex-wrap gap-1.5">
          <Chip>дело {view.case_id}</Chip>
          <Chip>пространство {view.workspace_id}</Chip>
          <Chip>звеньев: {view.reasoning.line.length}</Chip>
          <Chip>утверждений: {assertions.length}</Chip>
          <Chip>источников: {view.sources.length}</Chip>
        </div>
      </Card>

      {trace ? (
        <Card>
          <div className="flex flex-wrap items-center justify-between gap-2 border-b border-line px-5 py-3">
            <div>
              <h3 className="text-[15px] font-semibold">Машинная трассировка</h3>
              <p className="mt-0.5 text-[12px] text-faint">{trace.level_ru}</p>
            </div>
            <div className="flex gap-1.5">
              <Chip tone={trace.faithfulness_passed ? "good" : "stop"}>
                {trace.faithfulness_passed
                  ? "проверка верности пройдена"
                  : "проверка верности не пройдена"}
              </Chip>
              <Chip tone={trace.usability_passed ? "good" : "warn"}>
                {trace.usability_passed ? "структура в порядке" : "структура с замечаниями"}
              </Chip>
            </div>
          </div>
          <pre className="thin-scroll max-h-[600px] overflow-auto p-5 text-[12.5px] leading-relaxed whitespace-pre-wrap text-muted">
            {trace.text}
          </pre>
        </Card>
      ) : (
        <Note>Машинная трассировка для этого дела не собрана.</Note>
      )}

      <Card className="p-5 sm:p-6">
        <SectionTitle hint="Все утверждения формальной проверки. Линия вывода — двенадцать из них, отобранных по юридическому порядку решения спора.">
          Полная проверка — {assertions.length}
        </SectionTitle>
        <ul className="divide-y divide-line">
          {shown.map((assertion) => (
            <li key={assertion.code} className="flex items-start gap-3 py-2">
              <YesNo value={assertion.value === true} />
              <div className="min-w-0 flex-1">
                <p className="text-[13.5px] leading-relaxed text-text">{assertion.text_ru}</p>
                <p className="mt-0.5 truncate text-[11px] text-faint" title={assertion.code}>
                  {assertion.code} · источников: {assertion.source_refs.length}
                </p>
              </div>
            </li>
          ))}
        </ul>
        {assertions.length > 12 && (
          <button
            type="button"
            onClick={() => setShowAll(!showAll)}
            className="mt-3 rounded-lg border border-line px-3 py-1.5 text-[13px] text-muted hover:border-accent hover:text-accent"
          >
            {showAll ? "Свернуть" : `Показать все ${assertions.length}`}
          </button>
        )}
      </Card>
    </div>
  );
}
