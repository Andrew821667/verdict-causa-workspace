import type { TypedGap } from "@/lib/types";
import { Card, Chip, SectionTitle, Note } from "./primitives";

const KIND_TONE = {
  decisive_fact: "warn",
  human_review: "stop",
  not_explored: "neutral",
} as const;

/**
 * Пробелы как задачи, а не как список недостающих данных.
 *
 * У каждого записана цена ответа — какие выводы перевернутся, если факт
 * установить, — и способ закрыть. Пробел без последствия был бы просьбой
 * донести документ «на всякий случай».
 */
export function GapQueue({
  gaps,
  notes,
}: {
  gaps: TypedGap[];
  notes: string[];
}) {
  return (
    <Card className="p-5 sm:p-6">
      <SectionTitle hint="Чего системе не хватает и что изменится, если это получить.">
        Что закрыть
      </SectionTitle>

      {gaps.length === 0 && (
        <Note>Очередь пуста: ни один известный вопрос не переворачивает вывод.</Note>
      )}

      <ul className="space-y-3">
        {gaps.map((gap) => (
          <li
            key={gap.id}
            className={`rounded-lg border bg-surface-2 p-4 ${
              gap.blocking ? "border-warn/40" : "border-line"
            }`}
          >
            <div className="flex flex-wrap items-center gap-2">
              <Chip tone={KIND_TONE[gap.kind]}>{gap.kind_ru}</Chip>
              {gap.blocking && <Chip tone="warn">блокирует вывод</Chip>}
            </div>
            <p className="mt-2.5 text-[15px] leading-snug text-text">{gap.question_ru}</p>

            {gap.consequence_ru.length > 0 && (
              <div className="mt-3">
                <p className="text-[11px] font-medium tracking-wide text-faint uppercase">
                  Если закрыть, изменится
                </p>
                <ul className="mt-1 space-y-1">
                  {gap.consequence_ru.map((line) => (
                    <li key={line} className="flex gap-2 text-[13px] text-muted">
                      <span aria-hidden className="text-accent">→</span>
                      <span>{line}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {gap.closes_with_ru.length > 0 && (
              <div className="mt-3">
                <p className="text-[11px] font-medium tracking-wide text-faint uppercase">
                  Закрывается
                </p>
                <div className="mt-1.5 flex flex-wrap gap-1.5">
                  {gap.closes_with_ru.map((line) => (
                    <span
                      key={line}
                      className="rounded-md border border-line bg-surface px-2 py-1 text-[12px] text-muted"
                    >
                      {line}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </li>
        ))}
      </ul>

      {notes.map((note) => (
        <div key={note} className="mt-4">
          <Note>{note}</Note>
        </div>
      ))}
    </Card>
  );
}
