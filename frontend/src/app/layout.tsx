/*
KOROBOS — Second Brain Operating System

Copyright (c) 2026 Saravana Perumal K

Licensed under the GNU Affero General Public License v3.
*/
import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "KOROBOS Frontend",
  description: "KOROBOS Next.js frontend",
  icons: {
    icon: [
      { url: "/favicon.ico", sizes: "any" },
      { url: "/favicon-32x32.png", type: "image/png", sizes: "32x32" },
      { url: "/favicon-16x16.png", type: "image/png", sizes: "16x16" },
      { url: "/korobos-icon-192.png", type: "image/png", sizes: "192x192" },
      { url: "/KOROBOS-logo.svg", type: "image/svg+xml" },
      { url: "/KOROBOS-logo.png", type: "image/png", sizes: "500x500" },
    ],
    apple: [
      { url: "/apple-touch-icon.png", sizes: "180x180", type: "image/png" },
    ],
    shortcut: "/favicon.ico",
  },
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
