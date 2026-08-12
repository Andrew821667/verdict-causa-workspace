/**
 * Живой API стенда.
 *
 * Данные разбора вложены в сборку, но загрузка документа требует пересчёта, а
 * пересчёт умеет только Python. Поэтому интерфейс проверяет, отвечает ли API на
 * том же адресе: если да — загрузка работает, если нет — она честно выключена,
 * а не притворяется работающей.
 */

export async function detectApi(): Promise<boolean> {
  if (typeof window === "undefined") return false;
  try {
    const response = await fetch("/api/desktop", { method: "GET" });
    return response.ok;
  } catch {
    return false;
  }
}

export async function postJson(path: string, body: unknown) {
  const response = await fetch(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  const payload = await response.json();
  return { ok: response.ok, status: response.status, payload };
}

export function toBase64(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => {
      const result = String(reader.result);
      resolve(result.slice(result.indexOf(",") + 1));
    };
    reader.onerror = () => reject(reader.error);
    reader.readAsDataURL(file);
  });
}
