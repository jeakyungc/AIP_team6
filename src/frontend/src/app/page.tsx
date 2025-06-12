// src/app/page.tsx

'use client';

import PDFViewer from './components/PDFViewer';
import FlowCanvas from './components/FlowCanvas';
import QueryInput from './components/QueryInput';
import React from 'react';

export default function HomePage() {
  return (
    <main className="relative flex flex-col h-screen bg-gray-50">
      {/* 헤더 */}
      <header className="p-4 bg-white shadow border-b">
        <h1
          className="text-2xl text-neutral-800"
          style={{ fontFamily: 'var(--font-climate-crisis)' }}
        >
          CHUNK-IT
        </h1>
      </header>

      {/* 본문 */}
      <div className="flex flex-1 relative">
        {/* 좌측 PDF 뷰어 */}
        <div className="w-1/2 h-full border-r overflow-auto">
          <PDFViewer />
        </div>

        {/* 우측 Flow 노드 캔버스 */}
        <div className="w-1/2 h-full relative overflow-auto">
          <FlowCanvas />
        </div>
      </div>

    </main>
  );
}
