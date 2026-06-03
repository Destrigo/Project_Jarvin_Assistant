"use client";
import { useState } from "react";
import Sidebar from "@/components/Sidebar";
import Chat from "@/components/Chat";

export default function Home() {
  const [injected, setInjected] = useState<string>("");

  return (
    <div style={{ display: "flex", flex: 1, overflow: "hidden", height: "100%" }}>
      <Sidebar onInject={(text) => setInjected(text)} />
      <Chat
        injectedMessage={injected}
        onInjectedConsumed={() => setInjected("")}
      />
    </div>
  );
}
