import type { ReasoningView } from "@/lib/types";
import { Card, SectionTitle, Note } from "./primitives";

const ACCENTS = ["border-t-accent", "border-t-stop", "border-t-propose"];

/**
 * Один путь рассуждения с трёх сторон.
 *
 * Это не состязательный разбор нескольких агентов из раздела 8.2 концепции —
 * его в ядре нет, и оговорка стоит первой, а не в примечании.
 */
export function DebateView({ reasoning }: { reasoning: ReasoningView }) {
  const sides = [
    reasoning.debate.supporting,
    reasoning.debate.opposing,
    reasoning.debate.critic,
  ];
  return (
    <div className="space-y-4">
      <Note>{reasoning.debate.disclaimer_ru}</Note>
      <div className="grid gap-4 lg:grid-cols-3">
        {sides.map((side, index) => (
          <Card
            key={side.title_ru}
            className={`border-t-2 p-5 ${ACCENTS[index]}`}
          >
            <h3 className="text-[16px] font-semibold">{side.title_ru}</h3>
            <p className="mt-1 text-[12px] leading-snug text-faint">{side.origin_ru}</p>
            <ul className="mt-3 space-y-2.5">
              {side.points_ru.map((point) => (
                <li key={point} className="flex gap-2 text-[13.5px] leading-relaxed text-muted">
                  <span aria-hidden className="mt-2 h-1 w-1 shrink-0 rounded-full bg-line-strong" />
                  <span>{point}</span>
                </li>
              ))}
            </ul>
          </Card>
        ))}
      </div>
    </div>
  );
}

/**
 * Изложение результата для человека: коротко для решения и разбор для юриста.
 *
 * Третий уровень слоя перевода сюда не попадает. Он называется
 * forensic-трассировкой, состоит из координат воспроизведения, constraint set и
 * governance-журнала и адресован тому, кто налаживает систему, а не тому, кто
 * решает юридический вопрос. Его место — вкладка «Наладка».
 */
export function Registers({ reasoning }: { reasoning: ReasoningView }) {
  if (reasoning.registers.length === 0) {
    return <Note>Изложение для этого дела не собрано.</Note>;
  }
  return (
    <div className="space-y-4">
      <SectionTitle hint="Один и тот же результат для разных читателей. Слой перевода — часть ядра, а не пересказ поверх него. Машинная трассировка вынесена во вкладку «Наладка»: она объясняет работу системы, а не право.">
        Изложение
      </SectionTitle>
      {reasoning.registers.map((register) => (
        <Card key={register.level}>
          <div className="flex flex-wrap items-center justify-between gap-2 border-b border-line px-5 py-3">
            <h3 className="text-[15px] font-semibold">{register.level_ru}</h3>
            <div className="flex gap-1.5">
              <span
                className={`rounded-full border px-2.5 py-0.5 text-xs ${
                  register.faithfulness_passed
                    ? "border-good/30 bg-good-soft text-good"
                    : "border-stop/30 bg-stop-soft text-stop"
                }`}
              >
                {register.faithfulness_passed
                  ? "проверка верности пройдена"
                  : "проверка верности не пройдена"}
              </span>
              <span
                className={`rounded-full border px-2.5 py-0.5 text-xs ${
                  register.usability_passed
                    ? "border-good/30 bg-good-soft text-good"
                    : "border-warn/30 bg-warn-soft text-warn"
                }`}
              >
                {register.usability_passed ? "структура в порядке" : "структура с замечаниями"}
              </span>
            </div>
          </div>
          <pre className="thin-scroll overflow-x-auto p-5 text-[13px] leading-relaxed whitespace-pre-wrap text-muted">
            {register.text}
          </pre>
        </Card>
      ))}
    </div>
  );
}
