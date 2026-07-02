import { Inter, JetBrains_Mono } from "next/font/google";
import localFont from "next/font/local";

export const fontSans = Inter({
  subsets: ["latin"],
  variable: "--font-sans",
});

export const fontMono = JetBrains_Mono({
  subsets: ["latin"],
  variable: "--font-mono",
});

// Since SF Pro Display is Apple proprietary, we use Inter as the main font 
// which is extremely similar, but we can setup the CSS to fall back to system fonts 
// like -apple-system, BlinkMacSystemFont, "SF Pro Display"
