import type { CaseView, MapEdge } from "@/lib/types";
import { Card, Chip, SectionTitle, Note } from "./primitives";

/**
 * Карта разбора: что дошло до итога, а что нет.
 *
 * Разрыв не прячется. Вывод института, который никуда не идёт, не влияет на
 * то, что прочитает юрист, и это должно быть видно на деле, а не в
 * спецификации аудита.
 */
export function CaseMap({ view }: { view: CaseView }) {
  const toLayer = new Map<string, MapEdge>();
  for (const edge of view.map.edges) {
    if (edge.target.startsWith("layer:")) toLayer.set(edge.source, edge);
  }
  const institutes = view.map.nodes.filter((node) => node.kind === "institute");
  const reaching = institutes.filter((node) => toLayer.get(node.id)?.connected);
  const broken = institutes.filter((node) => toLayer.get(node.id)?.connected === false);

  return (
    <div className="space-y-4">
      <Card className="p-5 sm:p-6">
        <SectionTitle hint="Институты, чей вывод дошёл до итоговых выводов по делу.">
          Доходит до итога — {reaching.length}
        </SectionTitle>
        <div className="flex flex-wrap gap-2">
          {reaching.map((node) => (
            <span
              key={node.id}
              className="rounded-lg border border-accent/30 bg-accent-soft px-3 py-1.5 text-[13px] text-accent"
            >
              {node.title_ru}
            </span>
          ))}
        </div>
      </Card>

      <Card className="p-5 sm:p-6">
        <SectionTitle hint="Вывод института остался в его собственных правилах. У каждого разрыва записана причина — либо это решение, либо открытый долг.">
          Не доходит — {broken.length}
        </SectionTitle>
        <ul className="space-y-2.5">
          {broken.map((node) => {
            const edge = toLayer.get(node.id)!;
            return (
              <li
                key={node.id}
                className={`rounded-lg border border-dashed p-3.5 ${
                  edge.open_debt ? "border-stop/50 bg-stop-soft" : "border-line bg-surface-2"
                }`}
              >
                <div className="flex flex-wrap items-center gap-2">
                  <p className="text-[14px] font-semibold">{node.title_ru}</p>
                  {edge.open_debt && <Chip tone="stop">открытый долг связности</Chip>}
                </div>
                <p className="mt-1.5 text-[13px] leading-relaxed text-muted">
                  {edge.reason_ru}
                </p>
              </li>
            );
          })}
        </ul>
      </Card>

      <Card className="p-5 sm:p-6">
        <SectionTitle hint="Источники, на которых держится линия вывода. Идентификатор остаётся рядом с подписью.">
          Материалы — {view.sources.length}
        </SectionTitle>
        <ul className="grid gap-1.5 sm:grid-cols-2">
          {view.sources.map((source) => (
            <li
              key={source.id}
              title={source.id}
              className="rounded-md border border-line bg-surface-2 px-3 py-2"
            >
              <p className="text-[13px] text-text">{source.label_ru}</p>
              <p className="text-[11px] text-faint">{source.kind_ru}</p>
            </li>
          ))}
        </ul>
      </Card>

      {view.map.notes_ru.map((note) => (
        <Note key={note}>{note}</Note>
      ))}
    </div>
  );
}
