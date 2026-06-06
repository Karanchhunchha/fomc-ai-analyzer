import type { Metadata } from "next";
import { Inter, Playfair_Display } from "next/font/google";
import "./globals.css";

const inter = Inter({
  variable: "--font-inter",
  subsets: ["latin"],
  display: "swap",
});

const playfair = Playfair_Display({
  variable: "--font-playfair",
  subsets: ["latin"],
  display: "swap",
});

export const metadata: Metadata = {
  title: "CK Workspace",
  description: "AI-native intelligence workspace for document analysis and grounded research.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      className={`${inter.variable} ${playfair.variable} h-full antialiased`}
    >
      <body className="min-h-full flex flex-row">
        {/* Global Navigation Rail */}
        <nav className="w-16 flex-shrink-0 bg-white/5 border-r border-white/5 flex flex-col items-center py-6 gap-6 z-50">
          <div className="w-8 h-8 rounded-full bg-amber-500/20 border border-amber-500/30 flex items-center justify-center mb-4">
            <span className="text-amber-500 text-xs font-bold tracking-tighter">CK</span>
          </div>
          <a href="/workspace" className="text-white/40 hover:text-white transition-colors" title="Workspace">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"></path><polyline points="9 22 9 12 15 12 15 22"></polyline></svg>
          </a>
          <a href="/documents" className="text-white/40 hover:text-white transition-colors" title="Documents">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline><line x1="16" y1="13" x2="8" y2="13"></line><line x1="16" y1="17" x2="8" y2="17"></line><polyline points="10 9 9 9 8 9"></polyline></svg>
          </a>
          <a href="/compare" className="text-white/40 hover:text-white transition-colors" title="Compare">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M16 3h5v5"></path><path d="M8 3H3v5"></path><path d="M12 22v-8.3a4 4 0 0 0-1.172-2.872L3 3"></path><path d="M15 9l6-6"></path></svg>
          </a>
          <a href="/insights" className="text-white/40 hover:text-white transition-colors" title="Insights">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"></polyline></svg>
          </a>
          <a href="/sessions" className="text-white/40 hover:text-white transition-colors" title="History">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="10"></circle><polyline points="12 6 12 12 16 14"></polyline><path d="M12 2a10 10 0 0 0-7.38 3.4L3 7"></path><polyline points="3 3 3 7 7 7"></polyline></svg>
          </a>
        </nav>
        
        {/* Main Content Area */}
        <main className="flex-1 min-w-0 h-full relative">
          {children}
        </main>
      </body>
    </html>
  );
}
