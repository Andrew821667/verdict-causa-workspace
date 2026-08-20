"use client";

import { useState } from "react";
import type { CaseQualification } from "@/lib/types";
import { Card, Chip, SectionTitle, Note } from "./primitives";

/**
 * Квалификация: кластер определяет система.
 *
 * Техническое основание (имя предиката) убрано под «почему так»: в основном
 * виде юрист читает тип договора и статьи, а не поле модели. Убрано, а не
 * скрыто — оно раскрывается в один клик и не меняется по дороге.
 */
export function Qualification({ qualification }: { qualification: CaseQualification }) {
  const [shown, setShown] = useState<string | null>(null);
  const primary = qualification.primary?.institute ?? null;

  return (
    <Card className="p-5 sm:p-6">
      <SectionTitle hint="Кластер система определяет сама. Процента уверенности нет: предикат — вывод решателя, а не оценка правдоподобия.">
        Квалификация
      </SectionTitle>

      {qualification.scope !== "in_scope" && (
        <div className="mb-3 rounded-lg border-l-2 border-stop bg-stop-soft px-4 py-3">
          <p className="text-[13.5px] leading-relaxed text-text">
            {qualification.scope === "out_of_scope_suspected"
              ? "Дело, похоже, вне смоделированной области: статьи, на которые оно ссылается, не покрыты ни одним институтом."
              : "Область дела не определена: ни один предикат не сработал, статьи по делу не заявлены."}
          </p>
          {qualification.uncovered_articles.length > 0 && (
            <p className="mt-1 text-[12.5px] text-muted">
              Не покрыты: {qualification.uncovered_articles.join(", ")}.
            </p>
          )}
        </div>
      )}

      <ul className="space-y-2.5">
        {qualification.candidates.map((candidate) => (
          <li
            key={candidate.institute}
            className={`rounded-lg border p-3.5 ${
              candidate.institute === primary
                ? "border-accent/40 bg-accent-soft/40"
                : "border-line bg-surface-2"
            } ${candidate.displaced_by_special_rule ? "opacity-75" : ""}`}
          >
            <div className="flex flex-wrap items-baseline justify-between gap-2">
              <p className="text-[15px] font-semibold">{candidate.title_ru}</p>
              <p className="text-[12px] text-faint">{candidate.articles_ru}</p>
            </div>
            <div className="mt-2 flex flex-wrap gap-1.5">
              {candidate.institute === primary && <Chip tone="good">основная</Chip>}
              {candidate.displaced_by_special_rule && (
                <Chip>вытеснена специальными правилами</Chip>
              )}
              {candidate.certainty !== "single" && (
                <Chip tone="warn">{candidate.certainty_ru}</Chip>
              )}
              <button
                type="button"
                onClick={() =>
                  setShown(shown === candidate.institute ? null : candidate.institute)
                }
                className="rounded-full border border-line px-2.5 py-0.5 text-xs text-muted hover:border-accent hover:text-accent"
              >
                {shown === candidate.institute ? "скрыть основание" : "почему так"}
              </button>
            </div>
            {shown === candidate.institute && (
              <p className="mt-2.5 border-l-2 border-line pl-3 text-[13px] leading-relaxed text-muted">
                {candidate.basis_ru}
              </p>
            )}
          </li>
        ))}
      </ul>

      {qualification.candidates.length === 0 && (
        <Note>Ни один предикат квалификации не сработал.</Note>
      )}

      {qualification.notes_ru.map((note) => (
        <div key={note} className="mt-3">
          <Note>{note}</Note>
        </div>
      ))}
    </Card>
  );
}
