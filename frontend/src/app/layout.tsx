import type { Metadata } from "next";
import { fontSans, fontMono } from "@/lib/fonts";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryProvider } from "@/components/providers/QueryProvider";
import "./globals.css";

export const metadata: Metadata = {
  title: "FRIDAY OS",
  description: "Advanced Agentic AI Operating System",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark">
      <head>
        <style>{`
          #friday-loader {
            position: fixed;
            inset: 0;
            background: #000;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            z-index: 9999;
            transition: opacity 0.5s ease;
          }
          #friday-loader.hide {
            opacity: 0;
            pointer-events: none;
          }
          .loader-title {
            font-family: monospace;
            font-size: 2.5rem;
            font-weight: bold;
            color: #00ff88;
            letter-spacing: 0.3em;
            text-shadow: 0 0 20px #00ff88, 0 0 40px #00ff88;
            animation: pulse 1.5s ease-in-out infinite;
          }
          .loader-sub {
            font-family: monospace;
            font-size: 0.8rem;
            color: #00ff8888;
            letter-spacing: 0.2em;
            margin-top: 0.5rem;
          }
          .loader-bar-wrap {
            width: 300px;
            height: 2px;
            background: #111;
            margin-top: 2rem;
            border-radius: 2px;
            overflow: hidden;
          }
          .loader-bar {
            height: 100%;
            background: linear-gradient(90deg, #00ff88, #00ccff);
            box-shadow: 0 0 10px #00ff88;
            animation: load 0.8s ease-out forwards;
          }
          .loader-dots {
            font-family: monospace;
            color: #00ff8866;
            font-size: 0.75rem;
            margin-top: 1rem;
            letter-spacing: 0.1em;
            animation: blink 1s step-end infinite;
          }
          @keyframes pulse {
            0%, 100% { text-shadow: 0 0 20px #00ff88, 0 0 40px #00ff88; }
            50% { text-shadow: 0 0 30px #00ff88, 0 0 60px #00ff88, 0 0 80px #00ccff; }
          }
          @keyframes load {
            from { width: 0% }
            to { width: 100% }
          }
          @keyframes blink {
            0%, 100% { opacity: 1 }
            50% { opacity: 0 }
          }
        `}</style>
        <script dangerouslySetInnerHTML={{__html: `
          window.addEventListener('load', function() {
            setTimeout(function() {
              var loader = document.getElementById('friday-loader');
              if (loader) {
                loader.classList.add('hide');
                setTimeout(function() { loader.remove(); }, 500);
              }
            }, 800);
          });
        `}} />
      </head>
      <body
        className={`${fontSans.variable} ${fontMono.variable} antialiased min-h-screen bg-background text-foreground font-sans`}
      >
        <div id="friday-loader">
          <div className="loader-title">FRIDAY OS</div>
          <div className="loader-sub">ADVANCED AGENTIC AI SYSTEM</div>
          <div className="loader-bar-wrap">
            <div className="loader-bar"></div>
          </div>
          <div className="loader-dots">INITIALIZING...</div>
        </div>
        <QueryProvider>
          <TooltipProvider>
            {children}
          </TooltipProvider>
        </QueryProvider>
      </body>
    </html>
  );
}