
import React from 'react';

export const MiraCharacter = ({ state = "idle", className = "" }) => {
  // state options: idle, thinking, speaking, alert
  
  return (
    <div className={`relative ${className} select-none pointer-events-none`}>
       <svg viewBox="0 0 120 120" className="w-full h-full overflow-visible">
          <defs>
             {/* Neon Gradient */}
             <linearGradient id="miraNeon" x1="0%" y1="0%" x2="100%" y2="100%">
                 <stop offset="0%" stopColor="#60A5FA" /> {/* blue-400 */}
                 <stop offset="50%" stopColor="#3B82F6" /> {/* blue-500 */}
                 <stop offset="100%" stopColor="#2563EB" /> {/* blue-600 */}
             </linearGradient>
             
             {/* Glow Filter */}
             <filter id="glow" x="-50%" y="-50%" width="200%" height="200%">
                <feGaussianBlur stdDeviation="3" result="coloredBlur"/>
                <feMerge>
                    <feMergeNode in="coloredBlur"/>
                    <feMergeNode in="SourceGraphic"/>
                </feMerge>
             </filter>
          </defs>

          {/* Orbit rings (Thinking/Active state) */}
          <g className={`transition-opacity duration-500 ${state === 'thinking' ? 'opacity-100' : 'opacity-0'}`}>
            <ellipse cx="60" cy="60" rx="30" ry="10" fill="none" stroke="#60A5FA" strokeWidth="1" opacity="0.5">
               <animateTransform attributeName="transform" type="rotate" from="0 60 60" to="360 60 60" dur="3s" repeatCount="indefinite" />
            </ellipse>
            <ellipse cx="60" cy="60" rx="30" ry="10" fill="none" stroke="#60A5FA" strokeWidth="1" opacity="0.3">
               <animateTransform attributeName="transform" type="rotate" from="90 60 60" to="450 60 60" dur="4s" repeatCount="indefinite" />
            </ellipse>
          </g>

          {/* The M Character Construction */}
          <g transform="translate(60, 60)">
             {/* Animation Wrapper */}
             <g className={`transition-transform duration-500 ${state === 'speaking' ? 'animate-bounce-subtle' : 'animate-float'}`}>
               
               {/* Body (Letter M) - Centered */}
               <path 
                  d="M-30,20 L-30,-20 L0,10 L30,-20 L30,20" 
                  fill="none" 
                  stroke="url(#miraNeon)" 
                  strokeWidth="8" 
                  strokeLinecap="round" 
                  strokeLinejoin="round"
                  filter="url(#glow)"
               />
               
               {/* Eyes - Give it personality */}
               <g className="transition-transform duration-300">
                  <circle cx="-12" cy="-5" r="3.5" fill="white" className={`${state === 'thinking' ? 'animate-blink' : ''}`} />
                  <circle cx="12" cy="-5" r="3.5" fill="white" className={`${state === 'thinking' ? 'animate-blink' : ''}`} />
               </g>

               {/* Mouth/Expression (Optional, minimal) */}
               {state === 'speaking' && (
                  <path d="M-5,10 Q0,15 5,10" fill="none" stroke="white" strokeWidth="2" opacity="0.8" />
               )}

             </g>
          </g>
       </svg>
       
       <style>{`
         @keyframes float {
           0%, 100% { transform: translateY(0px); }
           50% { transform: translateY(-3px); }
         }
         @keyframes bounce-subtle {
            0%, 100% { transform: translateY(0px) scale(1); }
            50% { transform: translateY(-2px) scale(1.02); }
         }
         @keyframes blink {
            0%, 90%, 100% { transform: scaleY(1); }
            95% { transform: scaleY(0.1); }
         }
         .animate-float { animation: float 4s ease-in-out infinite; }
         .animate-bounce-subtle { animation: bounce-subtle 0.5s ease-in-out infinite; }
         .animate-blink { animation: blink 3s infinite; transform-origin: center; }
       `}</style>
    </div>
  );
};
