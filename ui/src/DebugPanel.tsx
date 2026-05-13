import React, { useState } from "react";

interface DebugPanelProps {
    data: any;
}

export const DebugPanel: React.FC<DebugPanelProps> = ({ data }) => {
    const [isVisible, setIsVisible] = useState(false);

    return (
        <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
            <label style={{ 
                fontSize: "11px", 
                cursor: "pointer", 
                color: isVisible ? "#0f0" : "#444",
                alignSelf: "flex-end" 
            }}>
                <input 
                    type="checkbox" 
                    checked={isVisible} 
                    onChange={(e) => setIsVisible(e.target.checked)} 
                    style={{ marginRight: "5px" }}
                />
                DEBUG_MODE
            </label>

            {isVisible && (
                <div style={{ 
                    width: "280px", 
                    background: "#0a0a0a", 
                    border: "1px solid #333", 
                    padding: "15px", 
                    borderRadius: "2px",
                    fontFamily: "monospace" 
                }}>
                    <div style={{ 
                        color: "#0f0", 
                        borderBottom: "1px solid #333", 
                        paddingBottom: "5px", 
                        marginBottom: "12px", 
                        fontSize: "12px" 
                    }}>
                        DEBUG_PANEL
                    </div>
                    
                    <div style={{ fontSize: "11px", display: "flex", flexDirection: "column", gap: "15px" }}>
                        <div>
                            <div style={{ color: "#888" }}>PHASE</div>
                            <div style={{ color: data?.phase === "REPPING" ? "#0f0" : "#fff" }}>
                                {data?.phase || "IDLE"}
                            </div>
                        </div>

                        <div>
                            <div style={{ color: "#888" }}>BAR_Y</div>
                            <div>{data?.bar?.position?.toFixed(4) || "0.0000"}</div>
                        </div>

                        <div style={{ borderTop: "1px solid #222", paddingTop: "10px" }}>
                            <div style={{ color: "#ff00ff", marginBottom: "5px" }}>INSTANT_METRICS</div>
                            <pre style={{ 
                                margin: 0, 
                                color: "#00d4ff", 
                                fontSize: "10px", 
                                lineHeight: "1.4", 
                                overflowX: "hidden",
                                whiteSpace: "pre-wrap" 
                            }}>
                                {JSON.stringify(data?.instant_metrics, null, 2)}
                            </pre>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};