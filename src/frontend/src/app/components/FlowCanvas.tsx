"use client";

import React, { useState } from "react";
import ChunkBox from "./ChunkBox";
import QueryInput from "./QueryInput";

interface Chunk {
  id: number;
  text: string;
  type: 'text' | 'image';
  loading: boolean;
}

export default function FlowCanvas() {
  const [chunks, setChunks] = useState<Chunk[]>([]);

  const handleAddChunk = (text: string, type: 'text' | 'image') => {
    const id = chunks.length + 1;
    const newChunk: Chunk = { id, text, type, loading: true };
    setChunks((prev) => [...prev, newChunk]);

    // 시뮬레이션용 지연 후 로딩 해제
    setTimeout(() => {
      setChunks((prev) =>
        prev.map((chunk) =>
          chunk.id === id ? { ...chunk, loading: false } : chunk
        )
      );
    }, 1500);
  };

  return (
    <div className="h-full w-full relative overflow-auto bg-gray-50 p-6">
      <div className="flex flex-wrap gap-4">
        {chunks.map((chunk) => (
          <ChunkBox
            key={chunk.id}
            title={`노드 ${chunk.id}`}
            index={chunk.id}
            content={chunk.text}
            type={chunk.type}
            loading={chunk.loading}
          />
        ))}
      </div>

      <QueryInput onSubmit={handleAddChunk} />
    </div>
  );
}
