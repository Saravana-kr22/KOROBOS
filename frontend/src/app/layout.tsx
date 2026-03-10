/*
CortexOS — Second Brain Operating System

Copyright (c) 2026 Saravana Perumal K

Licensed under the GNU Affero General Public License v3.
*/
import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "CortexOS Frontend",
  description: "CortexOS Next.js frontend",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
