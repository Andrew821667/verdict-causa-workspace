import type { ReactNode } from "react";
import type { Tone } from "@/lib/types";

/** Оценка серьёзности приходит из Python; здесь она только раскрашивается. */
export const TONE_CLASSES: Record<Tone, string> = {
  neutral: "bg-surface-2 text-muted border-line",
  good: "bg-good-soft text-good border-good/30",
  warn: "bg-warn-soft text-warn border-warn/30",
  stop: "bg-stop-soft text-stop border-stop/30",
};

export function Chip({
  children,
  tone = "neutral",
  title,
}: {
  children: ReactNode;
  tone?: Tone;
  title?: string;
}) {
  return (
    <span
      title={title}
      className={`inline-flex items-center gap-1.5 rounded-full border px-2.5 py-0.5 text-xs font-medium whitespace-nowrap ${TONE_CLASSES[tone]}`}
    >
      {children}
    </span>
  );
}

export function Card({
  children,
  className = "",
}: {
  children: ReactNode;
  className?: string;
}) {
  return (
    <section
      className={`rounded-xl border border-line bg-surface ${className}`}
    >
      {children}
    </section>
  );
}

export function SectionTitle({
  children,
  hint,
}: {
  children: ReactNode;
  hint?: string;
}) {
  return (
    <div className="mb-3">
      <h2 className="text-[13px] font-semibold tracking-[0.08em] text-faint uppercase">
        {children}
      </h2>
      {hint ? <p className="mt-1 text-[13px] text-muted">{hint}</p> : null}
    </div>
  );
}

/** Ответ «да»/«нет» звена разбора. Форма несёт то же, что и цвет. */
export function YesNo({ value }: { value: boolean }) {
  return value ? (
    <span className="inline-flex h-6 w-9 shrink-0 items-center justify-center rounded-md border border-accent/40 bg-accent-soft text-[11px] font-bold text-accent">
      да
    </span>
  ) : (
    <span className="inline-flex h-6 w-9 shrink-0 items-center justify-center rounded-md border border-line bg-surface-2 text-[11px] font-bold text-faint">
      нет
    </span>
  );
}

export function Note({ children }: { children: ReactNode }) {
  return (
    <p className="rounded-lg border border-dashed border-line bg-surface-2 px-3 py-2 text-[13px] leading-relaxed text-muted">
      {children}
    </p>
  );
}
