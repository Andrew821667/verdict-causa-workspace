"use client";

import { useState } from "react";
import type { TypedGap } from "@/lib/types";
import { postJson, toBase64 } from "@/lib/api";

/**
 * Закрытие пробела документом.
 *
 * Система документ не читает — это сказано на экране, а не спрятано в
 * документации. Оператор прикладывает файл и **сам утверждает**, что документ
 * подтверждает факт; идентификатор файла становится источником этого
 * утверждения, и дело пересчитывается целиком.
 */
export function GapCloser({
  gap,
  live,
  caseKey,
  onChanged,
}: {
  gap: TypedGap;
  live: boolean;
  caseKey: string;
  onChanged: (payload: Record<string, unknown>) => void;
}) {
  const [open, setOpen] = useState(false);
  const [file, setFile] = useState<File | null>(null);
  const [statement, setStatement] = useState("");
  const [due, setDue] = useState("");
  const [actual, setActual] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [conflicts, setConflicts] = useState<string[]>([]);
  const [explanation, setExplanation] = useState("");

  if (!gap.closure_kind) return null;
  const byDate = gap.closure_kind === "supplied_date";

  if (!live) {
    return (
      <p className="mt-3 rounded-lg border border-dashed border-line px-3 py-2 text-[12px] text-faint">
        Загрузка документа доступна на живом стенде: пересчёт дела выполняет
        Python, а эта страница — вложенный в сборку снимок разбора.
      </p>
    );
  }

  async function submit(event: React.FormEvent) {
    event.preventDefault();
    if (!file) return;
    setBusy(true);
    setError("");
    setConflicts([]);
    try {
      const upload = await postJson(`/api/case/${caseKey}/document`, {
        filename: file.name,
        media_type: file.type || "application/octet-stream",
        content_base64: await toBase64(file),
      });
      if (!upload.ok) {
        setError(upload.payload.error_ru || "Файл не принят");
        return;
      }
      const closed = await postJson(`/api/case/${caseKey}/close-gap`, {
        gap_id: gap.id,
        document_id: upload.payload.document.id,
        kind: gap.closure_kind,
        fact_updates: gap.fact_updates,
        agreed_due_date: byDate && due ? due : null,
        actual_performance_date: byDate && actual ? actual : null,
        statement_ru: statement,
      });
      if (closed.status === 409) {
        setConflicts(closed.payload.conflicts_ru || []);
        setExplanation(closed.payload.explanation_ru || "");
        return;
      }
      if (!closed.ok) {
        setError(closed.payload.error_ru || "Пересчёт не выполнен");
        return;
      }
      onChanged(closed.payload);
      setOpen(false);
      setFile(null);
    } finally {
      setBusy(false);
    }
  }

  if (!open) {
    return (
      <button
        type="button"
        onClick={() => setOpen(true)}
        className="mt-3 rounded-lg border border-accent/40 bg-accent-soft px-3 py-1.5 text-[13px] font-medium text-accent hover:opacity-90"
      >
        Закрыть документом
      </button>
    );
  }

  return (
    <form onSubmit={submit} className="mt-3 space-y-3 rounded-lg border border-line bg-surface p-3.5">
      <p className="text-[12px] leading-relaxed text-muted">
        Система документ <strong>не читает</strong>. Приложив файл, вы
        утверждаете, что он подтверждает факт; файл останется в деле как
        основание этого утверждения, а дело будет пересчитано.
      </p>

      <label className="block">
        <span className="text-[12px] text-faint">Файл</span>
        <input
          type="file"
          onChange={(event) => setFile(event.target.files?.[0] ?? null)}
          className="mt-1 block w-full text-[13px] file:mr-3 file:rounded-md file:border file:border-line file:bg-surface-2 file:px-3 file:py-1.5 file:text-[13px] file:text-text"
        />
      </label>

      {byDate ? (
        <div className="grid gap-3 sm:grid-cols-2">
          <label className="block">
            <span className="text-[12px] text-faint">Согласованный срок</span>
            <input
              type="date"
              value={due}
              onChange={(event) => setDue(event.target.value)}
              className="mt-1 w-full rounded-lg border border-line bg-surface px-3 py-1.5 text-[13px]"
            />
          </label>
          <label className="block">
            <span className="text-[12px] text-faint">Фактическое исполнение</span>
            <input
              type="date"
              value={actual}
              onChange={(event) => setActual(event.target.value)}
              className="mt-1 w-full rounded-lg border border-line bg-surface px-3 py-1.5 text-[13px]"
            />
          </label>
        </div>
      ) : (
        <p className="rounded-md bg-surface-2 px-3 py-2 text-[12px] text-muted">
          Вы утверждаете:{" "}
          {Object.entries(gap.fact_updates)
            .map(([field, value]) => `${field} — ${value ? "да" : "нет"}`)
            .join(", ")}
        </p>
      )}

      <label className="block">
        <span className="text-[12px] text-faint">Что именно подтверждает документ</span>
        <textarea
          rows={2}
          value={statement}
          onChange={(event) => setStatement(event.target.value)}
          className="mt-1 w-full resize-y rounded-lg border border-line bg-surface px-3 py-2 text-[13px]"
        />
      </label>

      {error && <p className="text-[13px] text-stop">{error}</p>}

      {conflicts.length > 0 && (
        <div className="rounded-lg border border-stop/40 bg-stop-soft p-3">
          <p className="text-[13px] leading-relaxed text-text">{explanation}</p>
          <ul className="mt-2 space-y-1">
            {conflicts.map((line) => (
              <li key={line} className="text-[12.5px] text-muted">
                • {line}
              </li>
            ))}
          </ul>
        </div>
      )}

      <div className="flex gap-2">
        <button
          type="submit"
          disabled={!file || busy}
          className="rounded-lg bg-accent px-4 py-2 text-[13px] font-medium text-bg disabled:opacity-50"
        >
          {busy ? "Пересчёт…" : "Приложить и пересчитать"}
        </button>
        <button
          type="button"
          onClick={() => setOpen(false)}
          className="rounded-lg border border-line px-3 py-2 text-[13px] text-muted"
        >
          Отмена
        </button>
      </div>
    </form>
  );
}
