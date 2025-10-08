import React, { useState, useEffect } from 'react';

// --- Type Declaration for Eel ---
declare global {
    interface Window {
        eel: {
            expose: (fn: Function, name:string) => void;
            start_listening: () => void;
        };
    }
}

interface ActionState {
    message: string;
    color: 'green' | 'red';
}

// --- CSS Styles ---
const styles = `
    body {
      margin: 0;
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen',
        'Ubuntu', 'Cantarell', 'Fira Sans', 'Droid Sans', 'Helvetica Neue',
        sans-serif;
      -webkit-font-smoothing: antialiased;
      -moz-osx-font-smoothing: grayscale;
    }

    .App {
      background-color: #000;
      min-height: 100vh;
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      font-size: calc(10px + 2vmin);
      color: white;
      padding: 1rem;
      box-sizing: border-box;
      position: relative;
    }

    .guard-status {
      position: absolute;
      top: 1.5rem;
      right: 1.5rem;
      font-size: 1rem;
      font-weight: 600;
      padding: 0.5rem 1rem;
      border-radius: 9999px;
      color: white;
      transition: background-color 300ms ease-in-out, box-shadow 300ms ease-in-out;
      text-shadow: 0 1px 3px rgba(0,0,0,0.2);
    }
    .guard-status.on {
      background-color: #10B981;
      box-shadow: 0 0 15px rgba(16, 185, 129, 0.7);
    }
    .guard-status.off {
      background-color: #4A5568;
    }

    .App-main {
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      text-align: center;
    }

    .visualizer {
      display: flex;
      align-items: center; 
      justify-content: center;
      gap: 0.8rem;
      width: 18rem;
      margin-bottom: 3rem;
      height: 500px;
    }

    .bar {
      width: 20%;
      background-color: #D1D3D4;
      border-radius: 1rem; 
      transition: background-color 100ms ease-in-out;
    }

    .text-output {
      display: flex;
      flex-direction: column;
      align-items: center; 
      justify-content: center;
      width: 100%;
      max-width: 42rem;
      padding-left: 1rem;
      padding-right: 1rem;
    }

    .label {
      font-size: 0.875rem;
      font-weight: 500;
      color: #6B7280;
      text-transform: uppercase;
      letter-spacing: 0.05em;
      margin-bottom: 0.25rem;
    }

    .recognized-text {
      z-index: 10;
      font-size: 2rem;
      font-weight: 600;
      color: white;
      min-height: 2.5rem;
      margin-top: 0;
      margin-bottom: 1.5rem;
      word-wrap: break-word;
    }

    .match-info {
      font-size: 1rem;
      color: #9CA3AF;
      margin-top: 0.25rem;
      height: 1.5rem;
    }

    .action-notification {
      margin-top: 2rem;
      padding: 1rem;
      border-radius: 0.5rem;
      text-align: center;
      font-weight: bold;
      font-size: 1.25rem;
      transition: all 300ms;
      animation: pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
      width: 100%;
      max-width: 42rem;
    }

    .action-notification--green {
      background-color: rgba(16, 185, 129, 0.2);
      border: 1px solid #10B981;
      color: #6EE7B7;
    }

    .action-notification--red {
      background-color: rgba(239, 68, 68, 0.2);
      border: 1px solid #EF4444;
      color: #F87171;
    }

    @keyframes pulse {
      50% {
        opacity: 0.5;
      }
    }

    .App-footer {
      position: absolute;
      bottom: 1rem;
      text-align: center;
      color: #374151;
      font-size: 0.875rem;
    }
`;

// --- React Component ---
const App: React.FC = () => {
    const [bars, setBars] = useState<number[]>(Array(16).fill(0));
    const [recognizedText, setRecognizedText] = useState<string>("");
    const [actionState, setActionState] = useState<ActionState | null>(null);
    const [isGuardModeOn, setIsGuardModeOn] = useState<boolean>(false);

    useEffect(() => {
        if (window.eel) {
            window.eel.expose(updateFrequencyBars, 'update_frequency_bars');
            window.eel.expose(updateData, 'update_data');
            window.eel.expose(triggerAction, 'trigger_action');
            window.eel.expose(updateGuardMode, 'update_guard_mode');
            window.eel.start_listening();
        } else {
            console.warn("Eel is not available. Running in browser mode.");
            updateData("Ready (Browser Mode)"); 
        }
    }, []);
    
    const updateFrequencyBars = (newBars: number[]): void => setBars(newBars);
    const updateData = (text: string): void => {
        setRecognizedText(text);
    };
    
    const triggerAction = (message: string, color: 'green' | 'red'): void => {
        setActionState({ message, color });
        setTimeout(() => setActionState(null), 3000);
    }
    
    const updateGuardMode = (status: boolean): void => {
        setIsGuardModeOn(status);
    };

    const reorderBarsForDisplay = (bars: number[]): number[] => {
        const leftHalf = bars.filter((_, i) => i % 2 === 0).reverse();
        const rightHalf = bars.filter((_, i) => i % 2 !== 0);
        return [...leftHalf, ...rightHalf];
    };

    return (
        <>
            <style>{styles}</style>
            <div className="App">
                <div className={`guard-status ${isGuardModeOn ? 'on' : 'off'}`}>
                    Guard Mode: <strong>{isGuardModeOn ? 'On' : 'Off'}</strong>
                </div>

                <main className="App-main">
                    <div className="visualizer">
                        {reorderBarsForDisplay(bars).map((height, index) => (
                            <div
                                key={index}
                                className="bar"
                                style={{ 
                                    height: `${Math.min(500, Math.max(0, height))}px`,
                                }}
                            ></div>
                        ))}
                    </div>
                    
                    <div className="text-output">
                        <p className="recognized-text" title={recognizedText}>
                            {recognizedText || "..."}
                        </p>
                    </div>

                    {actionState && (
                        <div className={`action-notification action-notification--${actionState.color}`}>
                            {actionState.message}
                        </div>
                    )}
                </main>
            </div>
        </>
    );
}

export default App;
