"use client";

import { useState } from "react";
import type { CaseView, ConclusionStep, SourceLabel } from "@/lib/types";
import { Card, SectionTitle, YesNo, Note } from "./primitives";

/**
 * Линия вывода как раскрывающиеся шаги.
 *
 * В свёрнутом виде читается ответ: вопрос и «да»/«нет». Развёрнутый шаг несёт
 * формулировку модели и источники — уже подписанные по-русски, но с
 * идентификатором рядом, потому что подпись это украшение над данными, а не
 * их замена.
 */
export function ReasoningLine({ view }: { view: CaseView }) {
  const [open, setOpen] = useState<string | null>(view.reasoning.line[0]?.code ?? null);
  const labels = new Map<string, SourceLabel>(
    view.sources.map((source) => [source.id, source]),
  );

  return (
    <Card className="p-5 sm:p-6">
      <SectionTitle hint="Порядок, в котором решается спор о нарушении договора. Нажмите шаг, чтобы увидеть формулировку и источники.">
        Шаги разбора
      </SectionTitle>
      <ol className="divide-y divide-line">
        {view.reasoning.line.map((step, index) => (
          <Step
            key={step.code}
            step={step}
            index={index + 1}
            open={open === step.code}
            onToggle={() => setOpen(open === step.code ? null : step.code)}
            labels={labels}
          />
        ))}
      </ol>
      {view.reasoning.notes_ru.map((note) => (
        <div key={note} className="mt-4">
          <Note>{note}</Note>
        </div>
      ))}
    </Card>
  );
}

function Step({
  step,
  index,
  open,
  onToggle,
  labels,
}: {
  step: ConclusionStep;
  index: number;
  open: boolean;
  onToggle: () => void;
  labels: Map<string, SourceLabel>;
}) {
  return (
    <li>
      <button
        type="button"
        onClick={onToggle}
        aria-expanded={open}
        className="flex w-full items-center gap-3 py-3 text-left hover:bg-surface-2"
      >
        <span className="w-5 shrink-0 text-[12px] tabular-nums text-faint">{index}</span>
        <YesNo value={step.value === true} />
        <span className="flex-1 text-[15px] text-text">{step.question_ru}</span>
        <span
          aria-hidden
          className={`shrink-0 text-faint transition-transform ${open ? "rotate-90" : ""}`}
        >
          ›
        </span>
      </button>
      {open && (
        <div className="pb-4 pl-[4.5rem]">
          <p className="max-w-[70ch] text-[14px] leading-relaxed text-muted">
            {step.text_ru}
          </p>
          {step.source_refs.length > 0 && (
            <div className="mt-3 flex flex-wrap gap-1.5">
              {step.source_refs.map((ref) => {
                const label = labels.get(ref);
                return (
                  <span
                    key={ref}
                    title={ref}
                    className="rounded-md border border-line bg-surface-2 px-2 py-1 text-[12px] text-muted"
                  >
                    {label ? label.label_ru : ref}
                  </span>
                );
              })}
            </div>
          )}
        </div>
      )}
    </li>
  );
}
