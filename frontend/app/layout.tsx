import "./globals.css";
import Link from "next/link";
import type { Metadata } from "next";
import { ReactNode } from "react";

export const metadata: Metadata = {
  title: "CreatorTrack",
  description: "Face-tracked video processing SaaS for creators.",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body>
        <div className="shell">
          <header className="topbar">
            <Link href="/" className="brand">
              CreatorTrack
            </Link>
            <nav className="nav">
              <Link href="/">Home</Link>
              <Link href="/try-now">Try now</Link>
              <Link href="/sign-in" className="primary-button">
                Sign in
              </Link>
            </nav>
          </header>
        </div>
        {children}
      </body>
    </html>
  );
}

