"use client";

import { useState } from "react";
import type { Dataset, RemarkOutcome } from "@/lib/types";
import { Card, Chip, SectionTitle } from "./primitives";

const KINDS = [
  ["clarification", "уточнение по делу"],
  ["disagreement", "не согласен с выводом"],
  ["qualification", "квалификация определена неверно"],
  ["missing_rule", "не учтена норма или практика"],
  ["wording", "изложение непонятно"],
] as const;

const HINTS: Record<string, string> = {
  clarification:
    "Останется в этом деле. Сигналом системе быть не может: это о фактах, а не о том, как система рассуждает.",
  disagreement: "Как сигнал породит кандидата «разрешение конфликта норм» — самый строгий путь.",
  qualification: "Как сигнал породит кандидата «разрешение конфликта норм».",
  missing_rule: "Как сигнал породит кандидата «пробел в знании».",
  wording: "Как сигнал породит кандидата слоя перевода: вопрос изложения, а не права.",
};

/**
 * Замечание оператора — два разных действия с разной судьбой.
 *
 * «Внести в дело» остаётся в деле. «Отправить как сигнал» порождает кандидата
 * со статусом «предложен» и обязательные стадии governance. Исход берётся из
 * набора, вычисленного Python: правило здесь не повторяется.
 */
export function Remarks({
  dataset,
  initial,
}: {
  dataset: Dataset;
  initial: RemarkOutcome[];
}) {
  const [kind, setKind] = useState<string>("clarification");
  const [text, setText] = useState("");
  const [signal, setSignal] = useState(false);
  const [outcomes, setOutcomes] = useState<RemarkOutcome[]>(initial);

  const signalAllowed = kind !== "clarification";

  function submit(event: React.FormEvent) {
    event.preventDefault();
    const value = text.trim();
    if (!value) return;
    const key = `${kind}:${signalAllowed && signal ? 1 : 0}`;
    const outcome: RemarkOutcome = JSON.parse(
      JSON.stringify(dataset.remark_outcomes[key]),
    );
    if (outcome.candidate) outcome.candidate.statement = value;
    setOutcomes([...outcomes, { ...outcome, remark_id: `local-${outcomes.length + 1}` }]);
    setText("");
  }

  return (
    <Card className="p-5 sm:p-6">
      <SectionTitle hint="Замечание по делу и сигнал системе — разные действия с разной судьбой.">
        Замечание оператора
      </SectionTitle>

      <form onSubmit={submit} className="space-y-3">
        <label className="block">
          <span className="text-[12px] text-faint">Вид замечания</span>
          <select
            value={kind}
            onChange={(event) => {
              setKind(event.target.value);
              if (event.target.value === "clarification") setSignal(false);
            }}
            className="mt-1 w-full rounded-lg border border-line bg-surface px-3 py-2 text-[14px]"
          >
            {KINDS.map(([value, label]) => (
              <option key={value} value={value}>
                {label}
              </option>
            ))}
          </select>
        </label>

        <label className="block">
          <span className="text-[12px] text-faint">Текст</span>
          <textarea
            value={text}
            onChange={(event) => setText(event.target.value)}
            rows={3}
            placeholder="Например: срок продлён дополнительным соглашением от 12 марта."
            className="mt-1 w-full resize-y rounded-lg border border-line bg-surface px-3 py-2 text-[14px]"
          />
        </label>

        <label
          className={`flex items-start gap-2.5 text-[13px] ${
            signalAllowed ? "text-text" : "text-faint"
          }`}
        >
          <input
            type="checkbox"
            checked={signal && signalAllowed}
            disabled={!signalAllowed}
            onChange={(event) => setSignal(event.target.checked)}
            className="mt-0.5 h-4 w-4 accent-[var(--propose)]"
          />
          <span>отправить как сигнал системе, а не только в дело</span>
        </label>

        <p className="rounded-lg border-l-2 border-propose bg-surface-2 px-3 py-2 text-[13px] text-muted">
          {HINTS[kind]}
        </p>

        <button
          type="submit"
          className="rounded-lg bg-accent px-4 py-2 text-[14px] font-medium text-bg hover:opacity-90"
        >
          Внести
        </button>
      </form>

      <ul className="mt-4 space-y-3">
        {outcomes.map((outcome, index) => (
          <li
            key={`${outcome.remark_id}-${index}`}
            className={`rounded-lg border-l-2 border border-line bg-surface-2 p-3.5 ${
              outcome.candidate ? "border-l-propose" : "border-l-accent"
            }`}
          >
            <p className="text-[12px] font-semibold text-faint">{outcome.kind_ru}</p>
            <p className="mt-1 text-[13px] leading-relaxed text-muted">
              {outcome.case_effect_ru}
            </p>
            {outcome.system_effect_ru && (
              <p className="mt-2 text-[13px] leading-relaxed text-muted">
                {outcome.system_effect_ru}
              </p>
            )}
            {outcome.candidate && (
              <>
                <div className="mt-2.5 flex flex-wrap gap-1.5">
                  <Chip>кандидат: {outcome.candidate.status}</Chip>
                  <Chip>{outcome.candidate_type}</Chip>
                </div>
                <p className="mt-2 text-[12px] text-faint">
                  обязательные стадии: {outcome.required_stages_ru.join(" → ")}
                </p>
              </>
            )}
            {outcome.notes_ru.map((note) => (
              <p key={note} className="mt-2 text-[13px] text-muted">
                {note}
              </p>
            ))}
          </li>
        ))}
      </ul>
    </Card>
  );
}
