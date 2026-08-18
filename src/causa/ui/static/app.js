"use strict";

/* Резонанс — клиент стенда.
   Никаких внешних библиотек: интерфейс должен открываться там, где запущен
   сервер, без сборки и без сети. */

const state = {
  desktop: null,
  workspaceId: null,
  caseId: null,
  view: null,
  tab: "line",
};

const $ = (id) => document.getElementById(id);

function el(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
}

/* Снимок стенда: те же данные, вложенные в файл. Если он есть, страница
   работает без сервера, и это прямо сказано на экране. */
const SNAPSHOT = window.CAUSA_SNAPSHOT || null;

async function getJSON(url) {
  const response = await fetch(url);
  const payload = await response.json();
  if (!response.ok) throw new Error(payload.error_ru || "Запрос не выполнен");
  return payload;
}

async function loadDesktop() {
  if (SNAPSHOT) return SNAPSHOT.desktop;
  return getJSON("/api/desktop");
}

async function loadCase(workspaceId, caseId) {
  if (SNAPSHOT) {
    const view = SNAPSHOT.cases[`${workspaceId}/${caseId}`];
    if (!view) throw new Error("В снимке этого дела нет.");
    return JSON.parse(JSON.stringify(view));
  }
  return getJSON(
    `/api/case/${encodeURIComponent(workspaceId)}/${encodeURIComponent(caseId)}`
  );
}

/* ── Верхняя полоса и список пространств ─────────────────────────── */

function renderTopbar() {
  const { organisation, operator } = state.desktop;
  $("org-title").textContent = organisation.title_ru;
  $("operator-name").textContent = operator.display_name;
  $("operator-role").textContent = operator.role_ru;

  const panel = $("rights-panel");
  panel.replaceChildren();
  panel.append(el("strong", null, "Что эта роль вправе делать: "));
  panel.append(document.createTextNode(operator.rights_ru.join("; ") + "."));
  panel.append(el("br"));
  const others = organisation.operators
    .filter((person) => person.id !== operator.id)
    .map((person) => `${person.display_name} — ${person.role_ru}`)
    .join("; ");
  panel.append(
    el("span", "muted", "Другие роли в организации: " + others + ".")
  );
}

function renderRail() {
  const host = $("workspaces");
  host.replaceChildren();
  for (const workspace of state.desktop.workspaces) {
    const block = el("div", "ws");
    const head = el("div", "ws__head");
    head.append(el("span", "ws__name", workspace.title_ru));
    head.append(
      el("span", "ws__meta", `${workspace.sla_mode_ru} · ${workspace.risk_tier_ru}`)
    );
    block.append(head);

    for (const card of workspace.cases) {
      const button = el("button", "case-btn");
      button.type = "button";
      if (workspace.id === state.workspaceId && card.case_id === state.caseId) {
        button.classList.add("is-active");
      }
      button.append(el("span", null, card.title_ru));
      button.append(el("span", "case-btn__cluster", card.cluster_ru));

      const flags = el("div", "case-btn__flags");
      if (card.blocking_gaps > 0) {
        flags.append(el("span", "badge badge--warn", `пробелов: ${card.blocking_gaps}`));
      }
      if (card.needs_human) {
        flags.append(el("span", "badge badge--stop", "нужен человек"));
      }
      if (card.open_debt_ru.length > 0) {
        flags.append(el("span", "badge badge--stop", "разрыв до итога"));
      }
      if (flags.childElementCount > 0) button.append(flags);

      button.addEventListener("click", () => openCase(workspace.id, card.case_id));
      block.append(button);
    }
    host.append(block);
  }
}

/* ── Окно дела ───────────────────────────────────────────────────── */

async function openCase(workspaceId, caseId) {
  state.workspaceId = workspaceId;
  state.caseId = caseId;
  $("case-title").textContent = "Загрузка разбора…";
  try {
    state.view = await loadCase(workspaceId, caseId);
  } catch (error) {
    $("case-title").textContent = "Дело не открылось";
    $("case-id").textContent = error.message;
    return;
  }
  renderRail();
  renderCase();
}

function renderCase() {
  const view = state.view;
  $("case-title").textContent = view.title_ru;
  $("case-id").textContent = `${view.case_id} · пространство ${view.workspace_id}`;

  const caveat = $("case-caveat");
  caveat.textContent = view.caveat_ru;
  caveat.hidden = !view.caveat_ru;

  const badges = $("case-badges");
  badges.replaceChildren();
  const blocking = view.gaps.gaps.filter((gap) => gap.blocking).length;
  badges.append(
    el(
      "span",
      blocking ? "badge badge--warn" : "badge badge--ok",
      blocking ? `пробелов, меняющих вывод: ${blocking}` : "пробелов, меняющих вывод, нет"
    )
  );
  const debts = view.map.edges.filter((edge) => edge.open_debt).length;
  if (debts > 0) {
    badges.append(el("span", "badge badge--stop", `разрывов без обоснования: ${debts}`));
  }
  if (view.reasoning.registers.length > 0) {
    badges.append(el("span", "badge", `изложение: ${view.reasoning.registers.length} уровня`));
  }

  renderStory();
  renderMaterials();
  renderQualification();
  renderGaps();
  renderOutcomes();
  renderTabs();
}

function renderMaterials() {
  const view = state.view;
  const host = $("materials");
  host.replaceChildren();
  for (const node of view.map.nodes.filter((n) => n.kind === "source")) {
    host.append(el("li", null, node.title_ru));
  }
  if (host.childElementCount === 0) {
    host.append(el("li", null, "линия вывода не ссылается на источники"));
  }

  const breaks = $("breaks");
  breaks.replaceChildren();
  const byTarget = new Map(view.map.nodes.map((node) => [node.id, node]));
  for (const edge of view.map.edges.filter((e) => !e.connected)) {
    const item = el("li", edge.open_debt ? "is-debt" : null);
    const node = byTarget.get(edge.source);
    item.append(el("span", "kicker", node ? node.title_ru : edge.source));
    item.append(document.createTextNode(edge.reason_ru));
    breaks.append(item);
  }
  if (breaks.childElementCount === 0) {
    breaks.append(el("li", null, "все сработавшие институты доходят до итога"));
  }
}

function renderQualification() {
  const host = $("qualification");
  host.replaceChildren();
  const qualification = state.view.qualification;
  const primaryId = qualification.primary ? qualification.primary.institute : null;

  for (const candidate of qualification.candidates) {
    const classes = ["cluster"];
    if (candidate.institute === primaryId) classes.push("cluster--primary");
    if (candidate.displaced_by_special_rule) classes.push("cluster--displaced");
    const box = el("div", classes.join(" "));
    box.append(el("div", "cluster__title", candidate.title_ru));
    box.append(
      el("div", "cluster__meta", `${candidate.group_ru} · ${candidate.articles_ru}`)
    );
    const flags = el("div", "case-btn__flags");
    if (candidate.institute === primaryId) {
      flags.append(el("span", "badge badge--ok", "основная квалификация"));
    }
    if (candidate.displaced_by_special_rule) {
      flags.append(el("span", "badge", "вытеснена специальными правилами"));
    }
    if (candidate.certainty !== "single") {
      flags.append(el("span", "badge badge--warn", candidate.certainty_ru));
    }
    box.append(flags);
    box.append(el("div", "cluster__basis", candidate.basis_ru));
    host.append(box);
  }
  if (qualification.candidates.length === 0) {
    host.append(el("p", "muted", "Ни один предикат квалификации не сработал."));
  }
  if (qualification.notes_ru.length > 0) {
    const notes = el("ul", "notes");
    for (const note of qualification.notes_ru) notes.append(el("li", null, note));
    host.append(notes);
  }
}

function renderGaps() {
  const host = $("gaps");
  host.replaceChildren();
  for (const gap of state.view.gaps.gaps) {
    const item = el("li", gap.blocking ? "gap gap--blocking" : "gap");
    item.append(el("div", "gap__kind", gap.kind_ru));
    item.append(el("div", "gap__q", gap.question_ru));
    if (gap.consequence_ru.length > 0) {
      item.append(el("div", "gap__label", "если закрыть, изменится:"));
      const list = el("ul");
      for (const line of gap.consequence_ru) list.append(el("li", null, line));
      item.append(list);
    }
    if (gap.closes_with_ru.length > 0) {
      item.append(el("div", "gap__label", "закрывается:"));
      const list = el("ul");
      for (const line of gap.closes_with_ru) list.append(el("li", null, line));
      item.append(list);
    }
    host.append(item);
  }
  if (state.view.gaps.gaps.length === 0) {
    host.append(el("li", "muted", "Очередь пуста."));
  }
}

/* ── Вкладки ─────────────────────────────────────────────────────── */

function renderTabs() {
  for (const tab of document.querySelectorAll(".tab")) {
    const active = tab.dataset.view === state.tab;
    tab.classList.toggle("is-active", active);
    tab.setAttribute("aria-selected", String(active));
    $(`panel-${tab.dataset.view}`).hidden = !active;
  }
  ({
    line: renderLine,
    debate: renderDebate,
    registers: renderRegisters,
    map: renderMap,
    diagnostics: renderDiagnostics,
  })[state.tab]();
}

/* Фабула: три предложения сверху, подробности под раскрытием.
   Все формулировки приходят из Python; здесь они только размещаются. */
function renderStory() {
  const story = state.view.story;
  const section = $("case-story");
  if (!story) {
    section.hidden = true;
    return;
  }
  section.hidden = false;
  $("story-summary").textContent = story.summary_ru;

  const body = $("story-body");
  body.replaceChildren();
  let established = 0;
  let total = 0;
  for (const part of story.sections) {
    body.append(el("h3", "story__section", part.title_ru));
    const list = el("ul", "story__facts");
    for (const fact of part.facts) {
      total += 1;
      if (fact.established) established += 1;
      list.append(
        el("li", fact.established ? "story__fact" : "story__fact story__fact--missing", fact.text_ru)
      );
    }
    body.append(list);
  }
  appendNotes(body, story.notes_ru);
  $("story-toggle").textContent =
    `Подробное описание обстоятельств — подтверждено ${established} из ${total}`;
}

function renderLine() {
  const panel = $("panel-line");
  panel.replaceChildren();
  const list = el("ul", "line");
  for (const step of state.view.reasoning.line) {
    const item = el("li", "step");
    const yes = step.value === true;
    item.append(
      el("span", `step__mark ${yes ? "step__mark--yes" : "step__mark--no"}`, yes ? "да" : "нет")
    );
    const body = el("div");
    body.append(el("div", "step__q", step.question_ru));
    body.append(el("p", "step__text", step.text_ru));
    if (step.source_refs.length > 0) {
      body.append(el("div", "step__src", "источники: " + step.source_refs.join(", ")));
    }
    item.append(body);
    list.append(item);
  }
  panel.append(list);
  appendNotes(panel, state.view.reasoning.notes_ru);
}

function renderDebate() {
  const panel = $("panel-debate");
  panel.replaceChildren();
  const debate = state.view.reasoning.debate;
  panel.append(el("p", "disclaimer", debate.disclaimer_ru));

  const grid = el("div", "debate");
  const sides = [
    [debate.supporting, "side side--for"],
    [debate.opposing, "side side--against"],
    [debate.critic, "side side--critic"],
  ];
  for (const [side, className] of sides) {
    const box = el("div", className);
    box.append(el("h3", null, side.title_ru));
    box.append(el("div", "side__origin", side.origin_ru));
    const list = el("ul");
    for (const point of side.points_ru) list.append(el("li", null, point));
    box.append(list);
    grid.append(box);
  }
  panel.append(grid);
}

function renderRegisters() {
  const panel = $("panel-registers");
  panel.replaceChildren();
  const registers = state.view.reasoning.registers;
  if (registers.length === 0) {
    panel.append(el("p", "disclaimer", "Изложение для этого дела не собрано."));
  }
  for (const register of registers) {
    const box = el("div", "register");
    const head = el("div", "register__head");
    head.append(el("strong", null, register.level_ru));
    const flags = el("div", "case-btn__flags");
    flags.append(
      el(
        "span",
        register.faithfulness_passed ? "badge badge--ok" : "badge badge--stop",
        register.faithfulness_passed ? "проверка верности пройдена" : "проверка верности не пройдена"
      )
    );
    flags.append(
      el(
        "span",
        register.usability_passed ? "badge badge--ok" : "badge badge--warn",
        register.usability_passed ? "структура в порядке" : "структура с замечаниями"
      )
    );
    head.append(flags);
    box.append(head);
    box.append(el("pre", null, register.text));
    panel.append(box);
  }
  renderFiling(panel);
}

/* Проект процессуального документа — другой жанр, а не четвёртый регистр:
   обстоятельства, правовое обоснование, требование, доказательства. */
function renderFiling(panel) {
  const filing = state.view.filing;
  if (!filing) return;
  const box = el("div", "register");
  const head = el("div", "register__head");
  head.append(el("strong", null, filing.title_ru));
  head.append(
    el(
      "span",
      filing.ready_to_file ? "badge badge--ok" : "badge badge--warn",
      filing.ready_to_file ? "проверки пройдены" : "не готов к подаче"
    )
  );
  box.append(head);
  for (const section of filing.sections) {
    box.append(el("h3", "story__section", section.title_ru));
    for (const paragraph of section.paragraphs_ru) {
      box.append(el("p", "step__text", paragraph));
    }
  }
  const checks = el("ul", "story__facts");
  for (const check of filing.checks) {
    checks.append(
      el(
        "li",
        check.passed ? "story__fact" : "story__fact story__fact--missing",
        check.detail_ru ? `${check.title_ru} — ${check.detail_ru}` : check.title_ru
      )
    );
  }
  box.append(el("h3", "story__section", "Проверки жанра"));
  box.append(checks);
  panel.append(box);
}

/* Наладка: машинная трассировка и полный список утверждений.
   Раньше этот материал стоял в «Изложении» под подписью «для суда»; подпись
   вводила в заблуждение — в суд такой текст не идёт. */
function renderDiagnostics() {
  const panel = $("panel-diagnostics");
  panel.replaceChildren();
  panel.append(
    el(
      "p",
      "disclaimer",
      "Служебный раздел: нужен при наладке системы и проверке воспроизводимости " +
        "вывода, а не при решении юридического вопроса."
    )
  );

  const trace = state.view.reasoning.trace;
  if (trace) {
    const box = el("div", "register");
    const head = el("div", "register__head");
    head.append(el("strong", null, "Машинная трассировка"));
    head.append(el("span", "badge", trace.level_ru));
    box.append(head);
    box.append(el("pre", null, trace.text));
    panel.append(box);
  } else {
    panel.append(el("p", "disclaimer", "Машинная трассировка для этого дела не собрана."));
  }

  const assertions = state.view.reasoning.all_assertions || [];
  panel.append(el("h3", "story__section", `Полная проверка — ${assertions.length}`));
  const list = el("ul", "story__facts");
  for (const assertion of assertions) {
    list.append(
      el(
        "li",
        assertion.value === true ? "story__fact" : "story__fact story__fact--missing",
        `${assertion.text_ru} · ${assertion.code}`
      )
    );
  }
  panel.append(list);
}

/* Схема правоотношения: кто кому что должен и чем это кончилось.
   Карта отвечает на вопрос об устройстве системы, схема — на вопрос юриста. */
function renderScheme(panel) {
  const scheme = state.view.scheme;
  if (!scheme) return;
  const group = el("div", "map-group");
  group.append(el("h3", null, "Правоотношение"));
  for (const link of scheme.links) {
    const from = scheme.parties.find((party) => party.id === link.source);
    const to = scheme.parties.find((party) => party.id === link.target);
    const row = el("div", link.state === "absent" ? "map-node map-node--break" : "map-node");
    row.append(
      el("strong", null, `${from ? from.title_ru : link.source} → ${to ? to.title_ru : link.target}: ${link.title_ru}`)
    );
    row.append(
      el(
        "span",
        "map-node__why",
        `${link.state_ru} · ${link.detail_ru}${link.articles_ru ? " · " + link.articles_ru : ""}`
      )
    );
    group.append(row);
  }
  panel.append(group);

  const chain = el("div", "map-group");
  chain.append(el("h3", null, "От факта к результату"));
  const list = el("ul", "story__facts");
  for (const stage of scheme.stages) {
    list.append(
      el(
        "li",
        stage.reached ? "story__fact" : "story__fact story__fact--missing",
        `${stage.title_ru} — ${stage.detail_ru}`
      )
    );
  }
  chain.append(list);
  chain.append(el("h3", null, "Итог"));
  chain.append(el("p", "story__summary", scheme.outcome_ru));
  chain.append(el("p", "step__text", scheme.outcome_detail_ru));
  panel.append(chain);
  appendNotes(panel, scheme.notes_ru);
}

function renderMap() {
  const panel = $("panel-map");
  panel.replaceChildren();
  renderScheme(panel);
  const map = state.view.map;
  const byId = new Map(map.nodes.map((node) => [node.id, node]));

  const groups = [
    ["evidence", "Проверенные факты"],
    ["institute", "Институты, сказавшие что-либо по делу"],
    ["layer", "Итоговые выводы"],
  ];
  const outgoing = new Map();
  for (const edge of map.edges) {
    if (!outgoing.has(edge.source)) outgoing.set(edge.source, []);
    outgoing.get(edge.source).push(edge);
  }

  for (const [kind, title] of groups) {
    const group = el("div", "map-group");
    group.append(el("h3", null, title));
    for (const node of map.nodes.filter((n) => n.kind === kind)) {
      const toLayer = (outgoing.get(node.id) || []).find((edge) =>
        edge.target.startsWith("layer:")
      );
      const classes = ["map-node"];
      if (toLayer && !toLayer.connected) classes.push("map-node--break");
      if (toLayer && toLayer.open_debt) classes.push("map-node--debt");
      const row = el("div", classes.join(" "));
      row.append(el("strong", null, node.title_ru));
      if (toLayer) {
        row.append(
          el(
            "span",
            "map-node__why",
            toLayer.connected
              ? "→ доходит до итога"
              : `✕ не доходит: ${toLayer.reason_ru}`
          )
        );
      } else if (node.detail_ru) {
        row.append(el("span", "map-node__why", node.detail_ru));
      }
      if (node.needs_human) {
        row.append(el("span", "badge badge--stop", "нужен человек"));
      }
      group.append(row);
    }
    panel.append(group);
  }
  appendNotes(panel, map.notes_ru);
}

function appendNotes(panel, notes) {
  if (!notes || notes.length === 0) return;
  const list = el("ul", "notes");
  for (const note of notes) list.append(el("li", null, note));
  panel.append(list);
}

/* ── Замечания ───────────────────────────────────────────────────── */

const REMARK_HINTS = {
  clarification:
    "Уточнение остаётся в этом деле. Сигналом системе оно быть не может: оно о фактах, а не о том, как система рассуждает.",
  disagreement:
    "Как сигнал породит кандидата типа «разрешение конфликта норм» — самый строгий путь governance.",
  qualification:
    "Как сигнал породит кандидата типа «разрешение конфликта норм»: спор о том, каким институтом описано дело.",
  missing_rule: "Как сигнал породит кандидата типа «пробел в знании».",
  wording: "Как сигнал породит кандидата слоя перевода: вопрос изложения, а не права.",
};

function renderRemarkHint() {
  const kind = $("remark-kind").value;
  const signal = $("remark-signal");
  if (kind === "clarification") {
    signal.checked = false;
    signal.disabled = true;
  } else {
    signal.disabled = false;
  }
  $("remark-hint").textContent = REMARK_HINTS[kind];
}

function renderOutcomes() {
  const host = $("outcomes");
  host.replaceChildren();
  for (const outcome of state.view.remarks.outcomes) {
    host.append(outcomeNode(outcome));
  }
}

function outcomeNode(outcome) {
  const item = el("li", outcome.candidate ? "outcome outcome--signal" : "outcome");
  item.append(el("div", "outcome__label", outcome.kind_ru));
  item.append(el("p", null, outcome.case_effect_ru));
  if (outcome.system_effect_ru) {
    item.append(el("p", null, outcome.system_effect_ru));
  }
  if (outcome.candidate) {
    const flags = el("div", "case-btn__flags");
    flags.append(el("span", "badge badge--propose", `кандидат: ${outcome.candidate.status}`));
    flags.append(el("span", "badge", outcome.candidate_type));
    item.append(flags);
    item.append(
      el("div", "outcome__stages", "обязательные стадии: " + outcome.required_stages_ru.join(" → "))
    );
  }
  for (const note of outcome.notes_ru) {
    item.append(el("p", "muted", note));
  }
  return item;
}

async function submitRemark(event) {
  event.preventDefault();
  const text = $("remark-text").value.trim();
  if (!text) return;
  const kind = $("remark-kind").value;
  const signal = $("remark-signal").checked;

  if (SNAPSHOT) {
    // Снимок не пересчитывает дело: исход берётся из заранее вычисленного
    // сервером набора, а не собирается здесь заново.
    const outcome = JSON.parse(
      JSON.stringify(SNAPSHOT.remark_outcomes[`${kind}:${signal ? 1 : 0}`])
    );
    if (outcome.candidate) {
      outcome.candidate.statement = text;
    }
    $("outcomes").append(outcomeNode(outcome));
    $("remark-text").value = "";
    return;
  }

  const body = {
    kind: kind,
    text_ru: text,
    as_learning_signal: signal,
  };
  const response = await fetch(
    `/api/case/${encodeURIComponent(state.workspaceId)}/${encodeURIComponent(state.caseId)}/remark`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    }
  );
  const outcome = await response.json();
  if (!response.ok) {
    $("remark-hint").textContent = outcome.error_ru || "Замечание не принято";
    return;
  }
  $("outcomes").append(outcomeNode(outcome));
  $("remark-text").value = "";
}

/* ── Снимок ──────────────────────────────────────────────────────── */

function markAsSnapshot() {
  $("org-sub").textContent =
    "статический снимок стенда · данные вычислены конвейером, пересчёт недоступен";
  const foot = document.querySelector(".foot");
  foot.prepend(
    el(
      "p",
      null,
      "Это снимок, а не живой стенд. Разборы всех дел вычислены тем же кодом, " +
        "что и на сервере, и вложены в файл; новых дел снимок посчитать не может, " +
        "а исходы замечаний в нём заранее вычислены, а не собраны в браузере."
    )
  );
}

/* ── Запуск ──────────────────────────────────────────────────────── */

async function start() {
  state.desktop = await loadDesktop();
  renderTopbar();
  if (SNAPSHOT) markAsSnapshot();
  renderRail();
  renderRemarkHint();

  $("rights-toggle").addEventListener("click", (event) => {
    const panel = $("rights-panel");
    panel.hidden = !panel.hidden;
    event.currentTarget.setAttribute("aria-expanded", String(!panel.hidden));
  });
  const known = new Set(["line", "debate", "registers", "map", "diagnostics"]);
  const fromHash = location.hash.replace("#", "");
  if (known.has(fromHash)) state.tab = fromHash;
  for (const tab of document.querySelectorAll(".tab")) {
    tab.addEventListener("click", () => {
      state.tab = tab.dataset.view;
      location.hash = state.tab;
      renderTabs();
    });
  }
  $("remark-kind").addEventListener("change", renderRemarkHint);
  $("remark-form").addEventListener("submit", submitRemark);

  const first = state.desktop.workspaces[0];
  if (first && first.cases.length > 0) {
    await openCase(first.id, first.cases[0].case_id);
  }
}

start();
