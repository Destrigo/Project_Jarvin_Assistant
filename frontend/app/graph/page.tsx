"use client";
import dynamic from "next/dynamic";

const Graph3D = dynamic(() => import("@/components/Graph3D"), { ssr: false });

export default function GraphPage() {
  return (
    <div style={{ height: "calc(100dvh - 49px)", width: "100%" }}>
      <Graph3D />
    </div>
  );
}
