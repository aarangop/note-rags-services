import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Note RAGs - AI Chat",
  description: "Chat with your notes using AI",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="antialiased">{children}</body>
    </html>
  );
}
