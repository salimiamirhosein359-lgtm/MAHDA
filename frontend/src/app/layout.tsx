import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "AI Sentinel — رصد هوش مصنوعی",
  description: "رصد فناوری و اخبار هوش مصنوعی + دستیار پژوهشی",
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="fa" dir="rtl">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
      </head>
      <body className="min-h-screen antialiased bg-white text-ink font-vazirmatn">
        {children}
      </body>
    </html>
  );
}
