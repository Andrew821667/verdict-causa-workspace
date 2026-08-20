"use client";

import { useState } from "react";
import type { CaseView } from "@/lib/types";
import { Card, Chip, SectionTitle, Note } from "./primitives";
import { postJson } from "@/lib/api";

/**
 * Спор двух миров и то, что выводится при неустановленных фактах.
 *
 * Прежний «Критик пути» был константой: пять его строк из шести совпадали
 * дословно для любого дела. Здесь спора никто не сочиняет — он уже есть в деле
 * как расхождение двух допустимых толкований спорных фактов, и вычисляется
 * целиком.
 *
 * Спорный факт — тот, за которым не стоит документа. Пока факт держится на
 * одном утверждении, противная сторона вправе прочитать его иначе.
 */
export function DisputeView({
  view,
  live,
  caseKey,
  onChanged,
}: {
  view: CaseView;
  live: boolean;
  caseKey: string;
  onChanged: (payload: Record<string, unknown>) => void;
}) {
  const stable = view.worlds.conclusions.filter(
    (item) => item.in_claimant_world === item.in_respondent_world,
  );
  const split = view.worlds.conclusions.filter(
    (item) => item.in_claimant_world !== item.in_respondent_world,
  );
  const deciding = view.worlds.contested.filter((item) => item.switches.length > 0);

  return (
    <div className="space-y-4">
      <div className="grid gap-4 lg:grid-cols-2">
        <Card className="border-t-2 border-t-accent p-5">
          <h3 className="text-[16px] font-semibold">Устояло в обоих мирах</h3>
          <p className="mt-1 text-[12px] leading-snug text-faint">
            эти выводы не поколеблет ни одно толкование спорного
          </p>
          <ul className="mt-3 space-y-2">
            {stable.map((item) => (
              <li key={item.outcome} className="text-[13.5px] leading-relaxed text-muted">
                {item.label_ru}: «{item.in_claimant_world ? "да" : "нет"}»
              </li>
            ))}
            {stable.length === 0 && (
              <li className="text-[13.5px] text-faint">
                Ни один вывод не устоял: спорно всё, от чего зависит исход.
              </li>
            )}
          </ul>
        </Card>

        <Card className="border-t-2 border-t-stop p-5">
          <h3 className="text-[16px] font-semibold">Расходится между сторонами</h3>
          <p className="mt-1 text-[12px] leading-snug text-faint">
            вот чем позиция уязвима — и это вычислено, а не сочинено
          </p>
          <ul className="mt-3 space-y-2">
            {split.map((item) => (
              <li key={item.outcome} className="text-[13.5px] leading-relaxed text-muted">
                {item.label_ru}: у истца «{item.in_claimant_world ? "да" : "нет"}», у
                ответчика «{item.in_respondent_world ? "да" : "нет"}»
              </li>
            ))}
            {split.length === 0 && (
              <li className="text-[13.5px] text-faint">
                Стороны не расходятся ни по одному выводу.
              </li>
            )}
          </ul>
        </Card>
      </div>

      <Card className="p-5 sm:p-6">
        <SectionTitle hint="Спорные факты в порядке того, сколько выводов каждый решает. Факт, не меняющий ничего, здесь не назван: требовать его доказывания — задавать работу, из которой ничего не следует.">
          От чего зависит расхождение — {deciding.length}
        </SectionTitle>
        <ul className="space-y-1.5">
          {deciding.map((item) => (
            <li
              key={item.fact}
              className="flex flex-wrap items-center gap-2 rounded-md border border-line bg-surface-2 px-3 py-2"
            >
              <span className="flex-1 text-[13.5px] text-text">{item.label_ru}</span>
              <Chip>выводов: {item.switches.length}</Chip>
            </li>
          ))}
          {deciding.length === 0 && (
            <li className="text-[13.5px] text-faint">Спорных фактов, решающих исход, нет.</li>
          )}
        </ul>
        {view.worlds.notes_ru.map((note) => (
          <div key={note} className="mt-3">
            <Note>{note}</Note>
          </div>
        ))}
      </Card>

      <Uncertainty view={view} live={live} caseKey={caseKey} onChanged={onChanged} />
    </div>
  );
}

/**
 * Неустановленные факты и бремя доказывания.
 *
 * «Не установлено» и «установлено обратное» — разные утверждения, и до этого
 * блока система их не различала: неутверждённый факт шёл в правило как факт в
 * пользу истца. Здесь неизвестное остаётся неизвестным, а вывод, который от
 * него зависит, разрешается против той стороны, которая обязана была доказать.
 */
function Uncertainty({
  view,
  live,
  caseKey,
  onChanged,
}: {
  view: CaseView;
  live: boolean;
  caseKey: string;
  onChanged: (payload: Record<string, unknown>) => void;
}) {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const unknown = new Set(view.uncertainty.unknown_facts);
  const depends = view.uncertainty.outcomes.filter((item) => item.status === "depends");

  async function toggle(fact: string) {
    setBusy(true);
    setError("");
    try {
      const next = new Set(unknown);
      if (next.has(fact)) next.delete(fact);
      else next.add(fact);
      const response = await postJson(`/api/case/${caseKey}/unknown-facts`, {
        facts: [...next],
      });
      if (!response.ok) {
        setError(response.payload.error_ru || "Не принято");
        return;
      }
      onChanged(response.payload);
    } finally {
      setBusy(false);
    }
  }

  return (
    <Card className="p-5 sm:p-6">
      <SectionTitle hint="«Не установлено» — не то же самое, что «установлено обратное». Вывод, зависящий от неустановленного, разрешается против того, кто обязан был доказать.">
        Неустановленные факты — {view.uncertainty.unknown_facts.length}
      </SectionTitle>

      {depends.length > 0 && (
        <ul className="mb-4 space-y-2">
          {depends.map((item) => (
            <li
              key={item.outcome}
              className="rounded-lg border border-warn/40 bg-warn-soft px-3.5 py-3"
            >
              <p className="text-[14px] text-text">
                {item.label_ru}: {item.status_ru} — принято «{item.resolved ? "да" : "нет"}»
              </p>
              <p className="mt-1 text-[12.5px] leading-relaxed text-muted">
                {item.resolution_ru}
              </p>
            </li>
          ))}
        </ul>
      )}

      {live ? (
        <div className="flex flex-wrap gap-1.5">
          {view.worlds.contested.map((item) => (
            <button
              key={item.fact}
              type="button"
              disabled={busy}
              onClick={() => toggle(item.fact)}
              className={`rounded-full border px-3 py-1 text-[12.5px] transition-colors disabled:opacity-50 ${
                unknown.has(item.fact)
                  ? "border-warn/50 bg-warn-soft text-warn"
                  : "border-line bg-surface-2 text-muted hover:border-accent hover:text-accent"
              }`}
            >
              {item.label_ru}
            </button>
          ))}
        </div>
      ) : (
        <Note>
          Объявить факт неустановленным можно на живом стенде: пересчёт дела
          выполняет Python, а эта страница — вложенный в сборку снимок разбора.
        </Note>
      )}

      {error && <p className="mt-2 text-[13px] text-stop">{error}</p>}

      {view.uncertainty.notes_ru.map((note) => (
        <div key={note} className="mt-3">
          <Note>{note}</Note>
        </div>
      ))}
    </Card>
  );
}
