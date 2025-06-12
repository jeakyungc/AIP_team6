"use client";

import React from "react";

interface ChunkBoxProps {
  title: string;
  content: string;
  index: number;
  type: 'text' | 'image';
  loading?: boolean;
  onDelete?: () => void;
}

export default function ChunkBox({ title, content, index, type, loading = false, onDelete }: ChunkBoxProps) {
  return (
    <div className="relative rounded-xl border border-gray-300 bg-white shadow-md p-4 w-[260px] text-sm flex flex-col gap-2">
      {/* 인덱스 번호 */}
      <div className="absolute -top-2 -left-2 bg-black text-white text-xs w-5 h-5 rounded-full flex items-center justify-center">
        {index}
      </div>

      {/* 삭제 버튼 */}
      <button
        onClick={() => {
          if (confirm('정말 삭제하시겠습니까?')) onDelete?.();
        }}
        className="absolute top-2 right-2 text-gray-400 hover:text-red-500"
      >
        <span className="material-symbols-outlined text-base">close</span>
      </button>

      {/* 타입 라벨 */}
      <span className="text-xs font-medium text-gray-500 uppercase tracking-wide">{type === 'image' ? '이미지' : '텍스트'}</span>

      {/* 콘텐츠 */}
      <div className="min-h-[80px]">
        {loading ? (
          <div className="text-gray-400 animate-pulse">생성 중...</div>
        ) : (
          type === 'image' ? (
            <img src={content} alt="Generated" className="rounded-md border" />
          ) : (
            <p className="text-gray-700 whitespace-pre-wrap">{content}</p>
          )
        )}
      </div>
    </div>
  );
}
