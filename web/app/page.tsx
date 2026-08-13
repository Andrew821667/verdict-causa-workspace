"use client";

import { useEffect, useMemo, useState } from "react";
import raw from "@/data/desktop.json";
import type { CaseView, Dataset } from "@/lib/types";
import { Chip } from "@/components/primitives";
import { VerdictHero } from "@/components/VerdictHero";
import { ReasoningLine } from "@/components/ReasoningLine";
import { GapQueue } from "@/components/GapQueue";
import { Qualification } from "@/components/Qualification";
import { Remarks } from "@/components/Remarks";
import { DebateView, Registers } from "@/components/DebateView";
import { CaseMap } from "@/components/CaseMap";
import { ChangePanel } from "@/components/ChangePanel";
import { detectApi } from "@/lib/api";

/**
 * Данные вложены в сборку намеренно: разбор пяти дел вычислен Python и
 * не пересчитывается в браузере. Фронтенд показывает результат, а не
 * повторяет правила.
 */
const dataset = raw as unknown as Dataset;

const TABS = [
  ["overview", "Обзор"],
  ["reasoning", "Разбор"],
  ["debate", "Спор"],
  ["registers", "Изложение"],
  ["map", "Карта"],
] as const;

type TabId = (typeof TABS)[number][0];

export default function Page() {
  const first = dataset.desktop.workspaces[0];
  const [selected, setSelected] = useState(`${first.id}/${first.cases[0].case_id}`);
  const [tab, setTab] = useState<TabId>("overview");
  const [railOpen, setRailOpen] = useState(false);
  const [live, setLive] = useState(false);
  const [override, setOverride] = useState<Record<string, CaseView>>({});
  const [change, setChange] = useState<Record<string, unknown> | null>(null);
  const [reconciliation, setReconciliation] = useState<Record<string, unknown> | null>(null);

  useEffect(() => {
    detectApi().then(setLive);
  }, []);

  const view = useMemo<CaseView>(
    () => override[selected] ?? dataset.cases[selected],
    [selected, override],
  );

  return (
    <div className="min-h-full">
      <Topbar onMenu={() => setRailOpen(!railOpen)} />

      <div className="mx-auto flex max-w-[1600px]">
        <Rail
          selected={selected}
          onSelect={(key) => {
            setSelected(key);
            setTab("overview");
            setChange(null);
            setRailOpen(false);
          }}
          open={railOpen}
        />

        <main className="min-w-0 flex-1 px-4 py-6 sm:px-6 lg:px-8">
          <header className="mb-5">
            <p className="text-[12px] text-faint">
              {view.case_id} · пространство {view.workspace_id}
            </p>
            <h1 className="mt-0.5 text-[19px] font-semibold text-balance">
              {view.title_ru}
            </h1>
          </header>

          {view.caveat_ru && (
            <p className="mb-5 rounded-lg border-l-2 border-warn bg-warn-soft px-4 py-3 text-[13.5px] leading-relaxed text-text">
              {view.caveat_ru}
            </p>
          )}

          <nav className="mb-5 flex flex-wrap gap-1 border-b border-line">
            {TABS.map(([id, label]) => (
              <button
                key={id}
                type="button"
                onClick={() => setTab(id)}
                className={`-mb-px border-b-2 px-3.5 py-2 text-[14px] transition-colors ${
                  tab === id
                    ? "border-accent font-semibold text-accent"
                    : "border-transparent text-muted hover:text-text"
                }`}
              >
                {label}
              </button>
            ))}
          </nav>

          {tab === "overview" && (
            <div className="space-y-5">
              <VerdictHero verdict={view.verdict} />
              {change && (
                <ChangePanel
                  change={change}
                  reconciliation={reconciliation}
                  onClose={() => setChange(null)}
                />
              )}
              <div className="grid gap-5 xl:grid-cols-[minmax(0,1fr)_minmax(0,380px)]">
                <GapQueue
                  gaps={view.gaps.gaps}
                  notes={view.gaps.notes_ru}
                  live={live}
                  caseKey={selected}
                  onChanged={(payload) => {
                    setChange(payload.change as Record<string, unknown>);
                    setReconciliation(
                      payload.reconciliation as Record<string, unknown>,
                    );
                    setOverride({
                      ...override,
                      [selected]: payload.case as unknown as CaseView,
                    });
                  }}
                />
                <div className="space-y-5">
                  <Qualification qualification={view.qualification} />
                  <Remarks dataset={dataset} initial={view.remarks.outcomes} />
                </div>
              </div>
            </div>
          )}

          {tab === "reasoning" && <ReasoningLine view={view} />}
          {tab === "debate" && <DebateView reasoning={view.reasoning} />}
          {tab === "registers" && <Registers reasoning={view.reasoning} />}
          {tab === "map" && <CaseMap view={view} />}

          <footer className="mt-10 max-w-[80ch] border-t border-line pt-4 text-[12px] leading-relaxed text-faint">
            Формальный результат не является судебным выводом или юридической
            консультацией. Данные вычислены конвейером Verdict Causa и вложены в
            сборку: интерфейс показывает результат, но новых дел не считает.
          </footer>
        </main>
      </div>
    </div>
  );
}

function Topbar({ onMenu }: { onMenu: () => void }) {
  const { organisation, operator } = dataset.desktop;
  const [rights, setRights] = useState(false);
  return (
    <header className="sticky top-0 z-20 border-b border-line bg-surface/90 backdrop-blur">
      <div className="mx-auto flex max-w-[1600px] items-center gap-3 px-4 py-2.5 sm:px-6">
        <button
          type="button"
          onClick={onMenu}
          aria-label="Список дел"
          className="rounded-lg border border-line px-2 py-1 text-muted lg:hidden"
        >
          ☰
        </button>
        <span
          aria-hidden
          className="h-6 w-2.5 rounded-sm bg-gradient-to-b from-accent to-propose"
        />
        <div className="min-w-0 flex-1">
          <p className="truncate text-[14px] font-semibold">{organisation.title_ru}</p>
          <p className="truncate text-[11.5px] text-faint">Резонанс · стенд оператора</p>
        </div>
        <Chip>{operator.role_ru}</Chip>
        <span className="hidden text-[13px] text-muted sm:inline">
          {operator.display_name}
        </span>
        <button
          type="button"
          onClick={() => setRights(!rights)}
          className="rounded-full border border-line px-2.5 py-1 text-[12px] text-muted hover:border-accent hover:text-accent"
        >
          права роли
        </button>
      </div>
      {rights && (
        <div className="border-t border-line bg-accent-soft px-4 py-2.5 text-[13px] text-text sm:px-6">
          <strong>Эта роль вправе: </strong>
          {operator.rights_ru.join("; ")}.{" "}
          <span className="text-muted">
            Другие роли:{" "}
            {organisation.operators
              .filter((person) => person.id !== operator.id)
              .map((person) => `${person.display_name} — ${person.role_ru}`)
              .join("; ")}
            .
          </span>
        </div>
      )}
    </header>
  );
}

function Rail({
  selected,
  onSelect,
  open,
}: {
  selected: string;
  onSelect: (key: string) => void;
  open: boolean;
}) {
  return (
    <aside
      className={`${
        open ? "block" : "hidden"
      } w-full shrink-0 border-r border-line px-4 py-5 lg:block lg:w-[280px]`}
    >
      <p className="mb-3 text-[11px] font-semibold tracking-[0.08em] text-faint uppercase">
        Рабочие пространства
      </p>
      <div className="space-y-5">
        {dataset.desktop.workspaces.map((workspace) => (
          <div key={workspace.id}>
            <p className="text-[13.5px] font-semibold">{workspace.title_ru}</p>
            <p className="mb-2 text-[11px] text-faint">
              {workspace.sla_mode_ru} · {workspace.risk_tier_ru}
            </p>
            <ul className="space-y-1.5">
              {workspace.cases.map((card) => {
                const key = `${workspace.id}/${card.case_id}`;
                const active = key === selected;
                return (
                  <li key={key}>
                    <button
                      type="button"
                      onClick={() => onSelect(key)}
                      className={`w-full rounded-lg border px-3 py-2.5 text-left transition-colors ${
                        active
                          ? "border-accent bg-accent-soft"
                          : "border-line bg-surface hover:border-line-strong"
                      }`}
                    >
                      <p className="text-[13.5px] leading-snug">{card.title_ru}</p>
                      <p className="mt-0.5 text-[11.5px] text-faint">{card.cluster_ru}</p>
                      <div className="mt-2 flex flex-wrap gap-1">
                        {card.blocking_gaps > 0 && (
                          <Chip tone="warn">пробелов: {card.blocking_gaps}</Chip>
                        )}
                        {card.needs_human && <Chip tone="stop">нужен человек</Chip>}
                      </div>
                    </button>
                  </li>
                );
              })}
            </ul>
          </div>
        ))}
      </div>
      <p className="mt-6 text-[11.5px] leading-relaxed text-faint">
        Материалы одного пространства не видны из другого. Это инвариант модели,
        а не настройка интерфейса.
      </p>
    </aside>
  );
}
