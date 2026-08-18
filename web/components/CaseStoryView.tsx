"use client";

import { useState } from "react";
import type { CaseStory } from "@/lib/types";
import { Card, Note } from "./primitives";

/**
 * Фабула дела: коротко сверху, подробно под раскрытием.
 *
 * Раньше окно дела открывалось вердиктом — ответом без вопроса. Юрист видел
 * «вопрос о нарушении возникает» и не знал, о каком обязательстве речь.
 * Фабула отвечает на это раньше вердикта, потому что вопрос читается раньше
 * ответа.
 *
 * Все предложения приходят из Python и собраны из тринадцати фактов
 * обязательства и трёх дат. Фронтенд не досочиняет ни слова: сочинённая
 * фабула, выглядящая как материалы дела, — самый дорогой вид ошибки здесь.
 */
export function CaseStoryView({ story }: { story: CaseStory }) {
  const [open, setOpen] = useState(false);
  const established = story.sections.flatMap((section) =>
    section.facts.filter((fact) => fact.established),
  ).length;
  const total = story.sections.flatMap((section) => section.facts).length;

  return (
    <Card className="p-5 sm:p-6">
      <h2 className="text-[13px] font-semibold tracking-[0.08em] text-faint uppercase">
        Фабула дела
      </h2>
      <p className="mt-2.5 max-w-[75ch] text-[15.5px] leading-relaxed text-text">
        {story.summary_ru}
      </p>

      <button
        type="button"
        onClick={() => setOpen(!open)}
        aria-expanded={open}
        className="mt-3.5 flex items-center gap-2 text-[13.5px] font-medium text-accent hover:opacity-80"
      >
        <span
          aria-hidden
          className={`inline-block transition-transform ${open ? "rotate-90" : ""}`}
        >
          ›
        </span>
        {open ? "Свернуть подробное описание" : "Подробное описание обстоятельств"}
        <span className="text-[12px] font-normal text-faint">
          подтверждено {established} из {total}
        </span>
      </button>

      {open && (
        <div className="mt-4 space-y-4 border-t border-line pt-4">
          {story.sections.map((section) => (
            <div key={section.title_ru}>
              <p className="text-[11px] font-semibold tracking-[0.08em] text-faint uppercase">
                {section.title_ru}
              </p>
              <ul className="mt-1.5 space-y-1.5">
                {section.facts.map((fact) => (
                  <li key={fact.fact} className="flex gap-2.5">
                    <span
                      aria-hidden
                      className={`mt-[7px] h-1.5 w-1.5 shrink-0 rounded-full ${
                        fact.established ? "bg-accent" : "bg-line-strong"
                      }`}
                    />
                    <span
                      className={`text-[14px] leading-relaxed ${
                        fact.established ? "text-text" : "text-faint"
                      }`}
                    >
                      {fact.text_ru}
                    </span>
                  </li>
                ))}
              </ul>
            </div>
          ))}
          {story.notes_ru.map((note) => (
            <Note key={note}>{note}</Note>
          ))}
        </div>
      )}
    </Card>
  );
}
