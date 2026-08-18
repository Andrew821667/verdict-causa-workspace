import type { CourtFiling } from "@/lib/types";
import { Card, Chip, SectionTitle, Note } from "./primitives";

/**
 * Проект процессуального документа.
 *
 * Это не четвёртый регистр перевода, а другой жанр. Регистр объясняет вывод;
 * документ его заявляет — обстоятельства, правовое обоснование, требование,
 * доказательства. Ни имён предикатов, ни отпечатков, ни идентификаторов: всё
 * это осталось в машинной трассировке, где ему и место.
 *
 * Пока открыт хотя бы один вопрос, меняющий вывод, документ помечен
 * непригодным к подаче — и это написано в самом тексте, а не только здесь.
 */
export function CourtFilingView({ filing }: { filing: CourtFiling }) {
  const failed = filing.checks.filter((check) => !check.passed);
  return (
    <Card>
      <div className="flex flex-wrap items-center justify-between gap-2 border-b border-line px-5 py-3">
        <div>
          <h3 className="text-[15px] font-semibold">{filing.title_ru}</h3>
          <p className="mt-0.5 text-[12px] text-faint">
            проект документа в дело — жанр выбран по выводу системы
          </p>
        </div>
        <Chip tone={filing.ready_to_file ? "good" : "warn"}>
          {filing.ready_to_file ? "проверки пройдены" : "не готов к подаче"}
        </Chip>
      </div>

      <div className="space-y-5 p-5 sm:p-6">
        {filing.sections.map((section) => (
          <section key={section.title_ru}>
            <h4 className="text-[11px] font-semibold tracking-[0.08em] text-faint uppercase">
              {section.title_ru}
            </h4>
            <div className="mt-1.5 space-y-1.5">
              {section.paragraphs_ru.map((paragraph) => (
                <p
                  key={paragraph}
                  className="max-w-[80ch] text-[14px] leading-relaxed text-text"
                >
                  {paragraph}
                </p>
              ))}
            </div>
          </section>
        ))}
      </div>

      <div className="border-t border-line px-5 py-4">
        <SectionTitle hint="Чем этот текст отличается от машинного вывода. Проверки идут по собранному документу, а не по замыслу.">
          Проверки жанра
        </SectionTitle>
        <ul className="space-y-1.5">
          {filing.checks.map((check) => (
            <li key={check.code} className="flex items-start gap-2.5 text-[13.5px]">
              <span
                aria-hidden
                className={`mt-[3px] inline-flex h-4 w-4 shrink-0 items-center justify-center rounded-full text-[10px] font-bold ${
                  check.passed
                    ? "bg-good-soft text-good"
                    : "bg-warn-soft text-warn"
                }`}
              >
                {check.passed ? "✓" : "!"}
              </span>
              <span className={check.passed ? "text-muted" : "text-text"}>
                {check.title_ru}
                {check.detail_ru && (
                  <span className="text-faint"> — {check.detail_ru}</span>
                )}
              </span>
            </li>
          ))}
        </ul>
        {failed.length > 0 && (
          <div className="mt-3">
            <Note>
              Документ можно прочитать и править, но подавать в этом виде нельзя:
              проверки не пройдены. Причина указана рядом с каждой.
            </Note>
          </div>
        )}
      </div>
    </Card>
  );
}
