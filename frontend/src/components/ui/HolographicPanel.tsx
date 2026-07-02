import { ReactNode } from "react";
import { motion, HTMLMotionProps } from "framer-motion";
import { cn } from "@/lib/utils";

interface HolographicPanelProps extends HTMLMotionProps<"div"> {
  children: ReactNode;
  className?: string;
  intensity?: "low" | "medium" | "high";
}

export function HolographicPanel({ 
  children, 
  className, 
  intensity = "medium",
  ...props 
}: HolographicPanelProps) {
  
  const intensityMap = {
    low: "bg-blue-950/10 border-blue-500/20 shadow-[0_0_15px_rgba(0,100,255,0.05)]",
    medium: "bg-blue-950/20 border-blue-400/30 shadow-[0_0_20px_rgba(0,150,255,0.1)]",
    high: "bg-blue-900/30 border-blue-300/40 shadow-[0_0_30px_rgba(0,200,255,0.2)]",
  };

  return (
    <motion.div
      whileHover={{ scale: 1.01, transition: { duration: 0.2 } }}
      className={cn(
        "relative overflow-hidden rounded-2xl border backdrop-blur-xl",
        "transition-colors duration-500",
        intensityMap[intensity],
        className
      )}
      {...props}
    >
      {/* Glossy top highlight */}
      <div className="absolute top-0 left-0 right-0 h-[1px] bg-gradient-to-r from-transparent via-white/20 to-transparent" />
      
      {/* Content wrapper */}
      <div className="relative z-10 p-5 h-full w-full">
        {children}
      </div>
      
      {/* Animated scanline effect overlay */}
      <div className="absolute inset-0 z-0 pointer-events-none opacity-10 mix-blend-overlay bg-[linear-gradient(rgba(255,255,255,0)_50%,rgba(0,150,255,0.1)_50%)] bg-[length:100%_4px]" />
    </motion.div>
  );
}
