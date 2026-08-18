"use client";

import { useMemo, useState } from "react";
import type { CaseView, ExtractedText, TypedGap } from "@/lib/types";
import { Card, Chip, SectionTitle, Note } from "./primitives";
import { postJson, toBase64 } from "@/lib/api";

/**
 * Материалы дела: загрузка файлов, их текст и места под открытые вопросы.
 *
 * Что здесь появилось: стенд достаёт текст из файла и показывает его.
 * Чего не появилось: понимания. Найденные места — совпадения по словам, и
 * подписаны они именно так. Утверждение о факте по-прежнему делает оператор
 * во вкладке «Обзор», приложив документ к конкретному пробелу.
 *
 * Различие не косметическое: система, которая делает вид, что прочитала
 * договор, опаснее системы, которая честно говорит, что не читала.
 */
export function DocumentsView({
  view,
  live,
  caseKey,
  onUploaded,
}: {
  view: CaseView;
  live: boolean;
  caseKey: string;
  onUploaded: (payload: Record<string, unknown>) => void;
}) {
  const [file, setFile] = useState<File | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [selected, setSelected] = useState<string | null>(null);

  const texts = useMemo(
    () => new Map<string, ExtractedText>(view.document_texts.map((item) => [item.document_id, item])),
    [view.document_texts],
  );
  const gaps = useMemo(
    () => new Map<string, TypedGap>(view.gaps.gaps.map((gap) => [gap.id, gap])),
    [view.gaps.gaps],
  );
  const shown = selected ?? view.document_texts[0]?.document_id ?? null;
  const current = shown ? texts.get(shown) : undefined;

  async function upload(event: React.FormEvent) {
    event.preventDefault();
    if (!file) return;
    setBusy(true);
    setError("");
    try {
      const response = await postJson(`/api/case/${caseKey}/document`, {
        filename: file.name,
        media_type: file.type || "application/octet-stream",
        content_base64: await toBase64(file),
      });
      if (!response.ok) {
        setError(response.payload.error_ru || "Файл не принят");
        return;
      }
      onUploaded(response.payload);
      setSelected((response.payload.document as { id: string }).id);
      setFile(null);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="space-y-4">
      <Card className="p-5 sm:p-6">
        <SectionTitle hint="Файл приобщается к делу, и из него извлекается текст. Выводов из текста система не делает.">
          Приложить материалы
        </SectionTitle>

        {live ? (
          <form onSubmit={upload} className="space-y-3">
            <input
              type="file"
              accept=".txt,.md,.csv,.docx,.pdf"
              onChange={(event) => setFile(event.target.files?.[0] ?? null)}
              className="block w-full text-[13px] file:mr-3 file:rounded-md file:border file:border-line file:bg-surface-2 file:px-3 file:py-1.5 file:text-[13px] file:text-text"
            />
            <p className="text-[12px] leading-relaxed text-faint">
              Читаются TXT, MD, CSV, DOCX и PDF с текстовым слоем. Скан без
              текстового слоя не читается: распознавания в стенде нет, и об этом
              будет сказано прямо, а не показан пустой документ.
            </p>
            {error && <p className="text-[13px] text-stop">{error}</p>}
            <button
              type="submit"
              disabled={!file || busy}
              className="rounded-lg bg-accent px-4 py-2 text-[13px] font-medium text-bg disabled:opacity-50"
            >
              {busy ? "Загрузка и пересчёт…" : "Приложить к делу"}
            </button>
          </form>
        ) : (
          <Note>
            Загрузка доступна на живом стенде: приём файла и пересчёт дела
            выполняет Python, а эта страница — вложенный в сборку снимок разбора.
          </Note>
        )}
      </Card>

      {view.documents.length > 0 && (
        <Card className="p-5 sm:p-6">
          <SectionTitle hint="Приложенные файлы. Отпечаток показывает, что в деле именно этот файл.">
            В деле — {view.documents.length}
          </SectionTitle>
          <ul className="space-y-1.5">
            {view.documents.map((document) => {
              const text = texts.get(document.id);
              const active = document.id === shown;
              return (
                <li key={document.id}>
                  <button
                    type="button"
                    onClick={() => setSelected(document.id)}
                    className={`flex w-full flex-wrap items-center gap-2 rounded-lg border px-3 py-2 text-left ${
                      active ? "border-accent bg-accent-soft" : "border-line bg-surface-2"
                    }`}
                  >
                    <span className="flex-1 text-[13.5px] text-text">{document.filename}</span>
                    <span className="text-[11.5px] text-faint">
                      {Math.max(1, Math.round(document.size_bytes / 1024))} КиБ
                    </span>
                    {text ? (
                      <Chip tone={text.extracted ? "good" : "warn"}>
                        {text.extracted ? `текст: ${text.characters} зн.` : "текст не извлечён"}
                      </Chip>
                    ) : (
                      <Chip>текст не запрашивался</Chip>
                    )}
                  </button>
                </li>
              );
            })}
          </ul>
        </Card>
      )}

      {current && (
        <Card>
          <div className="flex flex-wrap items-center justify-between gap-2 border-b border-line px-5 py-3">
            <h3 className="text-[15px] font-semibold">{current.filename}</h3>
            <span className="text-[12px] text-faint">{current.format_ru}</span>
          </div>
          <div className="px-5 py-3">
            <Note>{current.note_ru}</Note>
          </div>
          {current.extracted && (
            <pre className="thin-scroll max-h-[520px] overflow-auto px-5 pb-5 text-[13px] leading-relaxed whitespace-pre-wrap text-muted">
              {current.text}
            </pre>
          )}
        </Card>
      )}

      {view.hints.length > 0 && (
        <Card className="p-5 sm:p-6">
          <SectionTitle hint="Совпадения по словам между открытым вопросом и текстом документа. Это подсказка, где смотреть, а не установленное обстоятельство.">
            Места под открытые вопросы
          </SectionTitle>
          <ul className="space-y-4">
            {view.hints.map((hint) => {
              const gap = gaps.get(hint.gap_id);
              return (
                <li key={hint.gap_id} className="rounded-lg border border-line bg-surface-2 p-4">
                  <p className="text-[14.5px] leading-snug text-text">
                    {gap ? gap.question_ru : hint.gap_id}
                  </p>
                  {hint.dates.length > 0 && (
                    <div className="mt-2.5 flex flex-wrap gap-1.5">
                      {hint.dates.map((candidate) => (
                        <span
                          key={`${candidate.document_id}:${candidate.position}`}
                          title={candidate.quote_ru}
                          className="rounded-md border border-accent/30 bg-accent-soft px-2 py-1 text-[12px] text-accent"
                        >
                          {candidate.value}
                        </span>
                      ))}
                    </div>
                  )}
                  <ul className="mt-2.5 space-y-2">
                    {hint.fragments.map((fragment) => (
                      <li
                        key={`${fragment.document_id}:${fragment.position}`}
                        className="rounded-md border border-line bg-surface px-3 py-2"
                      >
                        <p className="text-[11px] text-faint">
                          {fragment.filename} · совпало «{fragment.matched_ru}»
                        </p>
                        <p className="mt-1 text-[13px] leading-relaxed text-muted">
                          {fragment.quote_ru}
                        </p>
                      </li>
                    ))}
                  </ul>
                  <p className="mt-2.5 text-[12px] leading-relaxed text-faint">{hint.note_ru}</p>
                </li>
              );
            })}
          </ul>
        </Card>
      )}
    </div>
  );
}
