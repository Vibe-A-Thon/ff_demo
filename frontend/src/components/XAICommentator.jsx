
import React, { useEffect, useState, useRef } from "react";
import { xaiAPI } from "../lib/api";
import { MiraCharacter } from "./MiraCharacter";
import { X, RefreshCw, MessageSquare, Mic } from "lucide-react";
import { AnimatePresence, motion } from "framer-motion";

const XAICommentator = ({ screen, role, summary, highlights = [] }) => {
  const [isOpen, setIsOpen] = useState(false);
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(false);
  const [miraState, setMiraState] = useState("idle"); // idle, thinking, speaking
  const prevScreenRef = useRef(screen);

  // Fetch commentary when screen context changes
  useEffect(() => {
    if (screen !== prevScreenRef.current) {
        // Auto-open on screen change? Maybe briefly options?
        // For now, let's just refresh content if open, or prepare it.
        if (isOpen) {
            handleRefresh();
        }
        prevScreenRef.current = screen;
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [screen, role]);

  const handleRefresh = async () => {
    setLoading(true);
    setMiraState("thinking");
    try {
      const payload = {
        screen,
        role,
        summary,
        highlights,
        timestamp: new Date().toISOString(),
      };
      
      const response = await xaiAPI.commentor(payload);
      setMessage(response?.data?.text || "I'm analyzing this screen for you.");
      setMiraState("speaking");
      
      // Go back to idle after "speaking" (simulated by reading time)
      setTimeout(() => setMiraState("idle"), 5000);
      
    } catch (error) {
      setMessage("I seem to be having trouble connecting to the neural core.");
      setMiraState("idle");
    } finally {
      setLoading(false);
    }
  };

  const handleToggle = () => {
    if (!isOpen) {
        setIsOpen(true);
        if (!message) handleRefresh();
    } else {
        setIsOpen(false);
    }
  };

  return (
    <div className="fixed bottom-6 right-6 z-50 flex flex-col items-end pointer-events-none">
      
      {/* Balloon / Message Bubble */}
      <AnimatePresence>
        {isOpen && (
          <motion.div 
            initial={{ opacity: 0, scale: 0.8, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.8, y: 10 }}
            className="pointer-events-auto mb-4 bg-background/95 backdrop-blur-md border border-blue-500/30 shadow-2xl rounded-2xl p-4 w-80 relative flex flex-col gap-2"
          >
             {/* Header */}
             <div className="flex justify-between items-start">
                <span className="text-[10px] font-mono text-blue-400 uppercase tracking-wider">MIRA System</span>
                <button onClick={() => setIsOpen(false)} className="text-muted-foreground hover:text-foreground">
                    <X className="w-3 h-3" />
                </button>
             </div>
             
             {/* Content */}
             <div className="text-sm leading-relaxed text-foreground min-h-[60px]">
                {loading ? (
                    <span className="animate-pulse text-muted-foreground">Analyzing operational context...</span>
                ) : (
                    message || "How can I assist you with " + screen + "?"
                )}
             </div>
             
             {/* Footer Actions */}
             <div className="flex justify-between items-center mt-2 border-t border-white/5 pt-2">
                <span className="text-[10px] text-muted-foreground">{role} View</span>
                <div className="flex gap-2">
                    <button 
                        onClick={handleRefresh} 
                        className="p-1.5 hover:bg-white/10 rounded-full transition-colors"
                        title="Get new insight"
                    >
                        <RefreshCw className={`w-3.5 h-3.5 text-blue-400 ${loading ? 'animate-spin' : ''}`} />
                    </button>
                    {/* Placeholder for Voice Interaction */}
                    <button className="p-1.5 hover:bg-white/10 rounded-full transition-colors" title="Voice Input">
                        <Mic className="w-3.5 h-3.5 text-muted-foreground" />
                    </button>
                </div>
             </div>
             
             {/* Arrow */}
             <div className="absolute -bottom-2 right-10 w-4 h-4 bg-background border-r border-b border-blue-500/30 transform rotate-45 rotate-45"></div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Character / Trigger */}
      <div className="pointer-events-auto relative group">
          <div 
            onClick={handleToggle}
            className="cursor-pointer w-20 h-20 transition-transform duration-300 hover:scale-110 active:scale-95 flex items-center justify-center"
          >
             <div className="absolute inset-0 bg-blue-500/20 blur-xl rounded-full opacity-0 group-hover:opacity-50 transition-opacity duration-500" />
             <MiraCharacter state={miraState} className="w-full h-full drop-shadow-lg" />
             
             {/* Static Badge Badge if closed */}
             {!isOpen && (
                 <div className="absolute top-0 right-2 bg-blue-600 w-3 h-3 rounded-full animate-bounce" />
             )}
          </div>
      </div>
    
    </div>
  );
};

export default XAICommentator;
