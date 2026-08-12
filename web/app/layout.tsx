import type { Metadata } from "next";
import "./globals.css";

/* Шрифты берутся из системы намеренно: страница должна открываться там, где
   внешние запросы запрещены, и не подменять начертание молча. */

export const metadata: Metadata = {
  title: "Резонанс",
  description:
    "Интерфейс оператора Verdict Causa: вердикт по делу, разбор, пробелы и сигналы обучения.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="ru" className="h-full antialiased">
      <body className="min-h-full">{children}</body>
    </html>
  );
}
