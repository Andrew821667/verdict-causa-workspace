import type { LinkState, RelationScheme } from "@/lib/types";
import { Card, SectionTitle, Note } from "./primitives";

/**
 * Схема правоотношения: кто кому что должен и чем это кончилось.
 *
 * Карта разбора отвечает на вопрос об устройстве системы — какой институт
 * сработал и доходит ли его вывод до итога. Схема отвечает на вопрос юриста:
 * какое отношение связывает стороны и что с ним произошло. Одно другое не
 * заменяет.
 *
 * Рисуется инлайновым SVG без библиотек: диаграмма из двух сторон и трёх
 * связей не стоит зависимости, а зависимость в сборке стоит дорого.
 */

const LINK_COLOR: Record<LinkState, string> = {
  breached: "var(--color-stop)",
  performed: "var(--color-good)",
  established: "var(--color-accent)",
  absent: "var(--color-line-strong)",
};

export function RelationSchemeView({ scheme }: { scheme: RelationScheme }) {
  const broke = scheme.stages.find((stage) => !stage.reached);
  return (
    <div className="space-y-4">
      <Card className="p-5 sm:p-6">
        <SectionTitle hint="Стороны названы ролями: имён сторон во входах модели нет, и подставлять их неоткуда.">
          Правоотношение
        </SectionTitle>
        <div className="thin-scroll overflow-x-auto">
          <PartiesDiagram scheme={scheme} />
        </div>
        <ul className="mt-4 space-y-2">
          {scheme.links.map((link) => (
            <li key={link.id} className="flex flex-wrap items-baseline gap-x-2 gap-y-1">
              <span
                aria-hidden
                className="mt-[6px] h-2 w-2 shrink-0 rounded-full"
                style={{ background: LINK_COLOR[link.state] }}
              />
              <span className="text-[14px] text-text">{link.title_ru}</span>
              <span className="text-[12.5px] text-faint">
                {link.state_ru} · {link.detail_ru}
                {link.articles_ru ? ` · ${link.articles_ru}` : ""}
              </span>
            </li>
          ))}
        </ul>
      </Card>

      <Card className="p-5 sm:p-6">
        <SectionTitle hint="Итог показан цепочкой условий: обрыв виден там, где он произошёл, а не сводится к ярлыку в конце.">
          От факта к результату
        </SectionTitle>
        <ol className="space-y-0">
          {scheme.stages.map((stage, index) => (
            <li key={stage.id} className="flex gap-3">
              <div className="flex flex-col items-center">
                <span
                  aria-hidden
                  className={`flex h-6 w-6 shrink-0 items-center justify-center rounded-full border text-[11px] font-bold ${
                    stage.reached
                      ? "border-accent/40 bg-accent-soft text-accent"
                      : "border-stop/40 bg-stop-soft text-stop"
                  }`}
                >
                  {stage.reached ? "✓" : "✕"}
                </span>
                {index < scheme.stages.length - 1 && (
                  <span
                    aria-hidden
                    className={`w-px flex-1 ${stage.reached ? "bg-accent/30" : "bg-stop/30"}`}
                  />
                )}
              </div>
              <div className="pb-4">
                <p
                  className={`text-[14.5px] leading-snug ${
                    stage.reached ? "text-text" : "text-stop"
                  }`}
                >
                  {stage.title_ru}
                </p>
                <p className="mt-0.5 text-[12.5px] leading-relaxed text-faint">
                  {stage.detail_ru}
                </p>
              </div>
            </li>
          ))}
        </ol>

        <div className="mt-1 rounded-lg border-l-2 border-accent bg-accent-soft px-4 py-3">
          <p className="text-[11px] font-semibold tracking-[0.08em] text-faint uppercase">
            Итог
          </p>
          <p className="mt-1 text-[15.5px] font-semibold text-text">{scheme.outcome_ru}</p>
          <p className="mt-1 max-w-[75ch] text-[13.5px] leading-relaxed text-muted">
            {scheme.outcome_detail_ru}
          </p>
          {broke && (
            <p className="mt-2 text-[13px] text-muted">
              Цепочка обрывается здесь: «{broke.title_ru}».
            </p>
          )}
        </div>
      </Card>

      {scheme.notes_ru.map((note) => (
        <Note key={note}>{note}</Note>
      ))}
    </div>
  );
}

/** Две стороны и связи между ними. Направление стрелки — направление долга. */
function PartiesDiagram({ scheme }: { scheme: RelationScheme }) {
  const [debtor, creditor] = scheme.parties;
  const rowHeight = 58;
  const height = 96 + scheme.links.length * rowHeight;
  const left = 24;
  const right = 476;

  return (
    <svg
      viewBox={`0 0 500 ${height}`}
      role="img"
      aria-label="Схема правоотношения между должником и кредитором"
      className="h-auto w-full min-w-[460px]"
    >
      <defs>
        {(["breached", "performed", "established", "absent"] as LinkState[]).map((state) => (
          <marker
            key={state}
            id={`arrow-${state}`}
            viewBox="0 0 10 10"
            refX="9"
            refY="5"
            markerWidth="7"
            markerHeight="7"
            orient="auto-start-reverse"
          >
            <path d="M 0 0 L 10 5 L 0 10 z" fill={LINK_COLOR[state]} />
          </marker>
        ))}
      </defs>

      <PartyBox x={left} label={debtor?.title_ru ?? "Должник"} anchor="start" />
      <PartyBox x={right} label={creditor?.title_ru ?? "Кредитор"} anchor="end" />

      <line
        x1={left + 34}
        y1={44}
        x2={left + 34}
        y2={height - 12}
        stroke="var(--color-line)"
        strokeDasharray="3 4"
      />
      <line
        x1={right - 34}
        y1={44}
        x2={right - 34}
        y2={height - 12}
        stroke="var(--color-line)"
        strokeDasharray="3 4"
      />

      {scheme.links.map((link, index) => {
        const y = 80 + index * rowHeight;
        const fromDebtor = link.source === debtor?.id;
        const x1 = fromDebtor ? left + 34 : right - 34;
        const x2 = fromDebtor ? right - 34 : left + 34;
        const dashed = link.state === "absent";
        return (
          <g key={link.id}>
            <line
              x1={x1}
              y1={y}
              x2={x2}
              y2={y}
              stroke={LINK_COLOR[link.state]}
              strokeWidth={link.state === "breached" ? 2.2 : 1.4}
              strokeDasharray={dashed ? "5 5" : undefined}
              markerEnd={`url(#arrow-${link.state})`}
            />
            <text
              x={250}
              y={y - 10}
              textAnchor="middle"
              className="fill-[var(--color-text)]"
              style={{ fontSize: 12.5 }}
            >
              {link.title_ru}
            </text>
            <text
              x={250}
              y={y + 16}
              textAnchor="middle"
              className="fill-[var(--color-faint)]"
              style={{ fontSize: 11 }}
            >
              {link.state_ru}
            </text>
          </g>
        );
      })}
    </svg>
  );
}

function PartyBox({
  x,
  label,
  anchor,
}: {
  x: number;
  label: string;
  anchor: "start" | "end";
}) {
  return (
    <text
      x={x}
      y={30}
      textAnchor={anchor}
      className="fill-[var(--color-text)]"
      style={{ fontSize: 14, fontWeight: 600 }}
    >
      {label}
    </text>
  );
}
