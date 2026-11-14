"use client";

import dynamic from "next/dynamic";
import React from "react";

// Dynamically import Plotly with SSR disabled to prevent server-side DOM errors
const Plot = dynamic(() => import("react-plotly.js"), {
  ssr: false,
  loading: () => (
    <div className="w-full h-64 flex items-center justify-center text-xs text-slate-400 bg-slate-50 rounded-lg animate-pulse border border-slate-200">
      Loading interactive visualization...
    </div>
  ),
});

interface PlotlyChartProps {
  data: any[];
  layout?: any;
  config?: any;
  style?: React.CSSProperties;
  className?: string;
}

export function PlotlyChart({ data, layout, config, style, className }: PlotlyChartProps) {
  const defaultLayout = {
    autosize: true,
    paper_bgcolor: "#FFFFFF",
    plot_bgcolor: "#FFFFFF",
    font: {
      color: "#001C58",
      family: "Inter, system-ui, -apple-system, sans-serif",
      size: 11,
    },
    margin: { l: 45, r: 25, t: 35, b: 45 },
    xaxis: {
      gridcolor: "#F1F5F9",
      zerolinecolor: "#E2E8F0",
      tickfont: { color: "#64748B", size: 10 },
      titlefont: { color: "#001C58", size: 11, weight: "bold" },
    },
    yaxis: {
      gridcolor: "#F1F5F9",
      zerolinecolor: "#E2E8F0",
      tickfont: { color: "#64748B", size: 10 },
      titlefont: { color: "#001C58", size: 11, weight: "bold" },
    },
    legend: {
      font: { color: "#1E293B", size: 11 },
      orientation: "h",
      y: -0.2,
      x: 0,
    },
    ...layout,
  };

  const defaultConfig = {
    responsive: true,
    displayModeBar: false,
    ...config,
  };

  return (
    <div className={`w-full overflow-hidden bg-white rounded-lg ${className || ""}`}>
      <Plot
        data={data}
        layout={defaultLayout}
        config={defaultConfig}
        style={{ width: "100%", height: "100%", minHeight: "260px", ...style }}
        useResizeHandler
      />
    </div>
  );
}
