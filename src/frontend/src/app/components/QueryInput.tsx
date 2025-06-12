"use client";

import React, { useState } from 'react';

interface QueryInputProps {
  onSubmit: (text: string, mode: 'text' | 'image') => void;
}

export default function QueryInput({ onSubmit }: QueryInputProps) {
  const [mode, setMode] = useState<'text' | 'image'>('text');
  const [input, setInput] = useState('');

  const handleSubmit = () => {
    if (!input.trim()) return;
    onSubmit(input, mode);
    setInput('');
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') handleSubmit();
  };

  return (
    <div className="fixed bottom-4 left-1/2 -translate-x-1/2 z-50 w-full max-w-5xl px-6 py-4 flex flex-col gap-3">
      {/* 토글 버튼 */}
      <div className="relative mx-auto">
        <div className="flex backdrop-blur-md bg-gray-300/40 rounded-full w-[240px] h-12 items-center relative">
          <div
            className={`absolute h-10 w-1/2 rounded-full backdrop-blur-md bg-neutral-700/80 transition-all duration-300 ease-in-out z-0 ${mode === 'image' ? 'left-1/2' : 'left-0'}`}
          ></div>
          <button
            onClick={() => setMode('text')}
            className={`flex items-center justify-center gap-1 w-1/2 z-10 text-sm font-medium transition ${mode === 'text' ? 'text-white' : 'text-gray-700/80'}`}
          >
            <span className="material-symbols-outlined text-base">insert_text</span> 텍스트
          </button>
          <button
            onClick={() => setMode('image')}
            className={`flex items-center justify-center gap-1 w-1/2 z-10 text-sm font-medium transition ${mode === 'image' ? 'text-white' : 'text-gray-700/80'}`}
          >
            <span className="material-symbols-outlined text-base">stylus_note</span> 이미지
          </button>
        </div>
      </div>

      {/* 입력창 + 전송 버튼 */}
      <div className="flex items-center bg-white/40 backdrop-blur-xs rounded-3xl border border-gray-300 px-4 py-3">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="질문을 입력하세요"
          className="flex-1 text-gray-900 placeholder-gray-400 bg-transparent outline-none border-none text-base"
        />
        <button
          onClick={handleSubmit}
          className="flex items-center justify-center bg-neutral-900 text-white hover:bg-neutral-700 transition rounded-full h-12 w-12"
        >
          <span className="material-symbols-outlined">arrow_upward</span>
        </button>
      </div>
    </div>
  )
}