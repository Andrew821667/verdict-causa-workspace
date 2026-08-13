import { Card } from "./primitives";

/**
 * Что изменилось после того, как оператор приложил документ.
 *
 * Разница считается по тому, что читает юрист: вердикт, звенья линии вывода,
 * число блокирующих пробелов. Отсутствие изменений — тоже результат, и он
 * показывается так же явно, как изменение.
 */
export function ChangePanel({
  change,
  reconciliation,
  onClose,
}: {
  change: Record<string, unknown>;
  reconciliation?: Record<string, unknown> | null;
  onClose: () => void;
}) {
  const steps = (change.steps as { question_ru: string; before: boolean; after: boolean }[]) ?? [];
  const notes = (change.notes_ru as string[]) ?? [];
  const changed = Boolean(change.verdict_changed);

  return (
    <Card className={`border-l-2 p-5 ${changed ? "border-l-accent" : "border-l-line-strong"}`}>
      <div className="flex items-start justify-between gap-3">
        <h2 className="text-[15px] font-semibold">
          {changed ? "Вывод изменился" : "Дело пересчитано"}
        </h2>
        <button
          type="button"
          onClick={onClose}
          className="rounded-full border border-line px-2 py-0.5 text-[12px] text-muted"
        >
          скрыть
        </button>
      </div>

      {changed && (
        <p className="mt-2 text-[14px] leading-relaxed">
          <span className="text-muted line-through">{String(change.verdict_before_ru)}</span>{" "}
          <span aria-hidden className="text-faint">→</span>{" "}
          <span className="font-medium">{String(change.verdict_after_ru)}</span>
        </p>
      )}

      {steps.length > 0 && (
        <ul className="mt-3 space-y-1.5">
          {steps.map((step) => (
            <li key={step.question_ru} className="text-[13.5px] text-muted">
              {step.question_ru}:{" "}
              <span className="text-text">
                {step.before ? "да" : "нет"} → {step.after ? "да" : "нет"}
              </span>
            </li>
          ))}
        </ul>
      )}

      <p className="mt-3 text-[13px] text-muted">
        Пробелов, меняющих вывод: {String(change.blocking_gaps_before)} →{" "}
        {String(change.blocking_gaps_after)}
      </p>

      {reconciliation && (reconciliation.lines_ru as string[])?.length > 0 && (
        <details className="mt-3">
          <summary className="cursor-pointer text-[13px] text-muted">
            {String(reconciliation.summary_ru)}
          </summary>
          <ul className="mt-2 space-y-1">
            {(reconciliation.lines_ru as string[]).map((line) => (
              <li key={line} className="text-[12.5px] text-muted">
                • {line}
              </li>
            ))}
          </ul>
        </details>
      )}

      {notes.map((note) => (
        <p key={note} className="mt-2 text-[13px] text-muted">
          {note}
        </p>
      ))}
    </Card>
  );
}
