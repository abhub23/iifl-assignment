import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "AI Content Assistant",
  description: "Summarize text and generate tags with an LLM",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-surface text-neutral-100 antialiased">
        {children}
      </body>
    </html>
  );
}
