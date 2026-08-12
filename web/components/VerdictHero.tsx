import type { CaseVerdict, Tone } from "@/lib/types";
import { Card, Chip } from "./primitives";

const BAR: Record<Tone, string> = {
  neutral: "bg-line-strong",
  good: "bg-good",
  warn: "bg-warn",
  stop: "bg-stop",
};

/**
 * Главный ответ по делу.
 *
 * Он стоит первым намеренно: разбор без вердикта — это протокол вычисления,
 * а не результат. Ограничители («требование убытков недоступно») стоят рядом,
 * а не вместо: они меняют то, что с выводом делать, но не отменяют его.
 */
export function VerdictHero({ verdict }: { verdict: CaseVerdict }) {
  return (
    <Card className="overflow-hidden">
      <div className={`h-1 w-full ${BAR[verdict.tone]}`} />
      <div className="p-5 sm:p-6">
        <p className="text-[12px] font-semibold tracking-[0.08em] text-faint uppercase">
          Вердикт по проверенным фактам
        </p>
        <h1 className="mt-1.5 text-2xl leading-snug font-semibold text-balance sm:text-[28px]">
          {verdict.headline_ru}
        </h1>
        <p className="mt-2 max-w-[68ch] text-[15px] leading-relaxed text-muted">
          {verdict.detail_ru}
        </p>

        {verdict.qualifiers_ru.length > 0 && (
          <ul className="mt-4 space-y-1.5">
            {verdict.qualifiers_ru.map((line) => (
              <li
                key={line}
                className="flex gap-2 text-[14px] leading-relaxed text-text"
              >
                <span aria-hidden className="mt-2 h-1 w-1 shrink-0 rounded-full bg-warn" />
                <span>{line}</span>
              </li>
            ))}
          </ul>
        )}

        {verdict.next_step_ru && (
          <p className="mt-5 rounded-lg border border-accent/25 bg-accent-soft px-3.5 py-2.5 text-[14px] text-accent">
            <span className="font-semibold">Что дальше. </span>
            {verdict.next_step_ru}
          </p>
        )}

        <div className="mt-5 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          {verdict.metrics.map((metric) => (
            <div
              key={metric.label_ru}
              className="rounded-lg border border-line bg-surface-2 px-3.5 py-3"
            >
              <p className="text-[11px] font-medium tracking-wide text-faint uppercase">
                {metric.label_ru}
              </p>
              <div className="mt-1.5">
                <Chip tone={metric.tone}>{metric.value_ru}</Chip>
              </div>
              <p className="mt-2 text-[12px] leading-snug text-muted">
                {metric.hint_ru}
              </p>
            </div>
          ))}
        </div>
      </div>
    </Card>
  );
}
