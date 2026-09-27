import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Korean Vocab | Word Library",
  description: "A personal wordbook for the Korean words you want to remember.",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
