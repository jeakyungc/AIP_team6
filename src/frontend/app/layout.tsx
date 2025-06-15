import { Geist, Geist_Mono} from "next/font/google";
import './globals.css'
import Link from 'next/link'

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata = {
  title: 'CHUNK-IT',
  description: 'PDF 기반 질문-응답 시각화',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="ko">
      <head>
        <link
          href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined"
          rel="stylesheet"
        />
      </head>
      <body className="bg-gray-100 text-gray-900 min-h-screen">
        <nav className="bg-white shadow-md px-4 py-3 flex gap-6">
          <Link href="/"><h1
          className="text-2xl text-neutral-800"
          style={{ fontFamily: 'var(--font-climate-crisis)' }}
        >
          CHUNK-IT
        </h1></Link>
        </nav>
        <main className={`${geistSans.variable} ${geistMono.variable} antialiased`}>{children}</main>
      </body>
    </html>
  )
}

