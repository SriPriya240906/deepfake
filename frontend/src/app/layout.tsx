import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-inter",
});

export const metadata: Metadata = {
  title: "Forensic Analysis Suite - Deepfake Detection",
  description: "Professional deepfake detection and forensic analysis platform for video authenticity verification",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" className={`${inter.variable} h-full`}>
      <body className="min-h-full bg-slate-50 font-sans antialiased">
        <div className="min-h-full">
          {children}
        </div>
      </body>
    </html>
  );
}
