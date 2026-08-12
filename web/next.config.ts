import type { NextConfig } from "next";

/**
 * Статический экспорт: интерфейс должен открываться и без сервера Node —
 * из папки, из артефакта, из чего угодно. Данные вложены в сборку, поэтому
 * серверная часть на этапе просмотра не нужна.
 */
const nextConfig: NextConfig = {
  output: "export",
  images: { unoptimized: true },
};

export default nextConfig;
