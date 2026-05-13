import React, { useState } from "react";

interface DebugPanelProps {
    data: any;
}

export const DebugPanel: React.FC<DebugPanelProps> = ({ data }) => {
    const [isVisible, setIsVisible] = useState(true);

    const side = data?.instant_metrics?.side || {};
    const front = data?.instant_metrics?.front || {};

    const MetricRow = ({ label, value, color = "#00d4ff" }: { label: string, value: any, color?: string }) => (
        <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "12px", gap: "15px" }}>
            <span style={{ color: "#555", fontSize: "14px", fontWeight: "bold" }}>{label}</span>
            <span style={{ color: color, fontWeight: "bold", fontSize: "22px" }}>{value ?? "N/A"}</span>
        </div>
    );

    return (
        <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
            <label style={{ 
                fontSize: "14px", 
                cursor: "pointer", 
                color: isVisible ? "#0f0" : "#444",
                alignSelf: "flex-end",
                userSelect: "none"
            }}>
                <input 
                    type="checkbox" 
                    checked={isVisible} 
                    onChange={(e) => {
                        console.log("debug panel's data: ", JSON.stringify(data))
                        setIsVisible(e.target.checked);
                    }} 
                    style={{ marginRight: "8px", transform: "scale(1.5)" }}
                />
                DEBUG_MODE
            </label>

            {isVisible && (
                <div style={{ 
                    width: "600px", 
                    background: "#000", 
                    border: "2px solid #333", 
                    padding: "25px", 
                    borderRadius: "4px",
                    fontFamily: "monospace",
                    boxShadow: "0 0 30px rgba(0,0,0,1)"
                }}>
                    <div style={{ 
                        color: "#0f0", 
                        textAlign: "center",
                        borderBottom: "1px solid #333", 
                        paddingBottom: "12px", 
                        marginBottom: "20px", 
                        fontSize: "18px",
                        letterSpacing: "3px"
                    }}>
                        DEBUG_PANEL
                    </div>
                    
                    {/* GIANT PHASE & BAR SECTION */}
                    <div style={{ display: "flex", justifyContent: "space-around", marginBottom: "25px" }}>
                        <div style={{ textAlign: "center" }}>
                            <div style={{ color: "#888", fontSize: "14px", marginBottom: "8px" }}>PHASE</div>
                            <div style={{ 
                                color: side?.is_repping ? "#0f0" : "#fff",
                                fontWeight: "extrabold",
                                fontSize: "36px",
                                textShadow: side?.is_repping ? "0 0 15px rgba(0,255,0,0.5)" : "none"
                            }}>
                                {side?.is_repping ? "REPPING" : "LOCKOUT"}
                            </div>
                            <div style={{ color: "#444", fontSize: "12px", marginTop: "5px" }}>FRAME: {data?.frame_id || 0}</div>
                        </div>
                        <div style={{ textAlign: "center", borderLeft: "2px solid #222", paddingLeft: "40px" }}>
                            <div style={{ color: "#888", fontSize: "14px", marginBottom: "8px" }}>BAR_Y</div>
                            <div style={{ fontSize: "36px", color: "#fff", fontWeight: "bold" }}>
                                {data?.bar?.position?.toFixed(3) || "0.000"}
                            </div>
                        </div>
                    </div>

                    {/* LARGE SIDE-BY-SIDE METRICS */}
                    <div style={{ display: "flex", gap: "40px", borderTop: "2px solid #222", paddingTop: "25px" }}>
                        
                        {/* SIDE VIEW */}
                        <div style={{ flex: 1 }}>
                            <div style={{ color: "#ff9d00", marginBottom: "15px", fontSize: "16px", fontWeight: "bold", textAlign: "center", borderBottom: "2px solid #ff9d00", paddingBottom: "8px" }}>
                                SIDE_VIEW
                            </div>
                            <MetricRow label="BACK" value={side.back_angle !== undefined ? Math.round(side.back_angle) + "°" : "N/A"} color="#ff9d00" />
                            <MetricRow label="RATIO" value={side.hip_knee_ratio?.toFixed(3)} color="#ff9d00" />
                            <MetricRow label="FLARE" value={side.elbow_flare?.toFixed(3)} color="#ff9d00" />
                        </div>

                        {/* FRONT VIEW */}
                        <div style={{ flex: 1, borderLeft: "2px solid #222", paddingLeft: "40px" }}>
                            <div style={{ color: "#00d4ff", marginBottom: "15px", fontSize: "16px", fontWeight: "bold", textAlign: "center", borderBottom: "2px solid #00d4ff", paddingBottom: "8px" }}>
                                FRONT_VIEW
                            </div>
                            <MetricRow label="KNEE" value={front.knee_distance?.toFixed(3)} />
                            <MetricRow label="ANKLE" value={front.ankle_distance?.toFixed(3)} />
                            <MetricRow label="SHLDR" value={front.shoulder_width?.toFixed(3)} />
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};