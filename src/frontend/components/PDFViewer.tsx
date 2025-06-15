"use client";

import { useState, useEffect } from "react";
import { Document, Page, pdfjs } from "react-pdf";
import QueryInput from "./QueryInput";
import ReactFlow, {
  addEdge,
  Background,
  Controls,
  MiniMap,
  ReactFlowProvider,
  useNodesState,
  useEdgesState,
  Connection,
  Edge,
  Node,
} from "reactflow";
import "reactflow/dist/style.css";
import "react-pdf/dist/esm/Page/TextLayer.css";

pdfjs.GlobalWorkerOptions.workerSrc = "/pdf.worker.js";

// '/pdf.worker.js'
// `//cdnjs.cloudflare.com/ajax/libs/pdf.js/${pdfjs.version}/pdf.worker.js`

type Chunk = {
  id: string;
  x: number;
  y: number;
  width: number;
  height: number;
  query: string;
  answer: string;
  type: 'text' | 'image';
  loading: boolean;
  color: string;
  fontSize: number;
  references: {
    page: number;
    text: string;
  };
};

export default function PDFViewer() {
  const [file, setFile] = useState<File | null>(null);
  const [numPages, setNumPages] = useState<number>(0);
  const [pageNumber, setPageNumber] = useState<number>(1);
  const [chunks, setChunks] = useState<Chunk[]>([]);

  const [edges, setEdges, onEdgesChange] = useEdgesState([]);
  const [isready, setIsready] = useState(false);
  const [selectedNode, setSelectedNode] = useState<Node | null>(null);

  const [isDeleteModalOpen, setIsDeleteModalOpen] = useState(false);
const [chunkToDelete, setChunkToDelete] = useState<string | null>(null);

  useEffect(() => {
    if (!file) return;

    // 파일이 바뀌었을 때 상태 초기화
    setNumPages(0);
    setPageNumber(1);
    setChunks([]);
    setEdges([]);
    setSelectedNode(null);
    setIsready(false);
  }, [file]);

  useEffect(() => {
    removeHighlight();
  }, [chunks]);

  const uploadPDF = async (file: File) => {
    
    const formData = new FormData();
    formData.append('file', file);

    const res = await fetch('http://localhost:8000/upload_pdf', {
      method: 'POST',
      body: formData,
    });

    if (!res.ok) throw new Error('Upload failed');
    return await res.json();
    
   // return 0;
};

  // ✅ 청크를 ReactFlow 노드로 매핑
  const nodes: Node[] = chunks.map((chunk) => ({
    id: chunk.id,
    type: "default",
    data: {
      label: (
        <div className="w-full h-full relativep-2 pt-5">
          <div className="fixed top-1 right-1 flex space-x-1">
            <button
          onClick={() => handleFontSizeChange(chunk.id, 2)}
          className="text-xs bg-gray-500 text-white px-1 rounded"
        >
          f⁺
        </button>
        <button
          onClick={() => handleFontSizeChange(chunk.id, -2)}
          className="text-xs bg-gray-500 text-white px-1 rounded"
        >
          f⁻
        </button>
        <button
          onClick={() => handleResizeChunk(chunk.id, 1)}
          className="text-xs bg-blue-500 text-white px-1 rounded"
        >
          ＋
        </button>
        <button
          onClick={() => handleResizeChunk(chunk.id, -1)}
          className="text-xs bg-yellow-500 text-white px-1 rounded"
        >
          −
        </button>
        <button
    onClick={() => handleChangeColor(chunk.id)}
    className="text-xs bg-purple-500 text-white px-1 rounded"
  >
    🎨
  </button>
        <button
          onClick={() => requestDeleteChunk(chunk.id)}
          className="text-xs bg-red-500 text-white px-1 rounded"
        >
          X
        </button>
      </div>
            <pre className="whitespace-pre-wrap"><b>Q: </b>{chunk.query}</pre>
          <hr className="my-2 border-t border-gray-300" />
          {chunk.loading ? (
          <div className="text-gray-400 animate-pulse">생성 중...</div>
        ) : chunk.type==='text' ? <div><pre className="whitespace-pre-wrap"><b>A: </b>{chunk.answer}</pre></div> : 
          <div><b>A: </b><img src={chunk.answer} alt="Generate Failed" className="rounded-md border" /></div>}
        </div>
      ),
      references: {
        page: chunk.references.page,
        text: chunk.references.text,
      },
    },
    position: { x: chunk.x, y: chunk.y },
    style: {
      width: chunk.width,
      height: chunk.height,
      background: chunk.color || "#fefcbf",
      border: "1px round rgb(255, 255, 255)",
      padding: 10,
      fontSize: chunk.fontSize,
      overflow: "auto",
    },
  }));

  const requestDeleteChunk = (id: string) => {
  setChunkToDelete(id);
  setIsDeleteModalOpen(true);
};

  const handleResizeChunk = (id: string, direction: number) => {
  const sizeStep = 50; // 한 번에 늘어나는 px
  setChunks((prevChunks) =>
    prevChunks.map((chunk) => {
      if (chunk.id === id) {
        return {
          ...chunk,
          width: Math.max(150, chunk.width + sizeStep * direction),
          height: Math.max(150, chunk.height + sizeStep * direction),
        };
      }
      return chunk;
    })
  );
};

const handleChangeColor = (id: string) => {
  const availableColors = [
    "#fefcbf",
    "#c6f6d5",
    "#bee3f8",
    "#fbd38d",
    "#fed7e2",
    "#e9d8fd",
  ];

  setChunks((prevChunks) =>
    prevChunks.map((chunk) => {
      if (chunk.id === id) {
        const currentIndex = availableColors.indexOf(chunk.color);
        const nextColor = availableColors[(currentIndex + 1) % availableColors.length];
        return { ...chunk, color: nextColor };
      }
      return chunk;
    })
  );
};

const handleFontSizeChange = (id: string, delta: number) => {
  setChunks((prev) =>
    prev.map((chunk) =>
      chunk.id === id
        ? {
            ...chunk,
            fontSize: Math.max(10, chunk.fontSize + delta), // 최소 폰트 크기 제한
          }
        : chunk
    )
  );
};

  const removeHighlight = () => {
    const spans = document.querySelectorAll(
      ".react-pdf__Page__textContent span"
    );

    spans.forEach((span) => {
      if (span.innerHTML.includes("<mark")) {
        // 모든 <span style="...">...< /span> 제거
        span.innerHTML = span.innerHTML.replace(
          /<mark style="[^"]*">(.*?)<\/mark>/g,
          "$1"
        );
      }
    });
  };

  const highlightText = (targetText: string, color: string) => {
    const spans = document.querySelectorAll(
      ".react-pdf__Page__textContent span"
    );

    spans.forEach((span) => {
      if (span.textContent?.includes(targetText)) {
        const html = span.innerHTML.replace(
          targetText,
          `<mark style="background: ${color};">${targetText}</mark>`
        );
        span.innerHTML = html;
      }
    });
  };

  const handleDeleteChunk = (id: string) => {
    removeHighlight();
    setChunks((prev) => prev.filter((chunk) => chunk.id !== id));
    setSelectedNode((prevSelected) => {
      if (prevSelected?.id === id) return null;
      return prevSelected;
    });
    setEdges((prev) =>
      prev.filter((edge) => edge.source !== id && edge.target !== id)
    );
  };

  const getRandomColor = () => {
    const colors = [
      "#fefcbf",
      "#c6f6d5",
      "#bee3f8",
      "#fbd38d",
      "#fed7e2",
      "#e9d8fd",
    ];
    return colors[Math.floor(Math.random() * colors.length)];
  };

  const onNodesChange = (changes: any) => {
    // 노드 위치 변경 시 chunks 상태도 동기화
    changes.forEach((change: any) => {
      if (change.type === "position" && change.position) {
        setChunks((prev) =>
          prev.map((chunk) =>
            chunk.id === change.id
              ? { ...chunk, x: change.position.x, y: change.position.y }
              : chunk
          )
        );
      }
    });
  };

  const onConnect = (params: Edge | Connection) =>
    setEdges((eds) => addEdge(params, eds));
  const onEdgeClick = (_: any, edge: Edge) =>
    setEdges((eds) => eds.filter((e) => e.id !== edge.id));
  const onNodeClick = (_: any, node: Node) => {
    const select = nodes.find((n) => n.id === node.id);
    if (select) setSelectedNode(select);

    const sc = chunks.find((c) => c.id === node.id);
    setPageNumber(node.data.references.page);
    if (sc) highlightText(node.data.references.text, sc.color);
  };
  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0];
    if (selectedFile) {
      setFile(selectedFile);
      try {
      const result = await uploadPDF(selectedFile);
      console.log(result);
      setIsready(true);
    } catch (err) {
      console.error(err);
      setIsready(false);
    }
    }
  };

  const generateLLMResponse = async (
    id: string, query: string, type: 'text' | 'image'
  ) => {
    if(type==='text'){
      
        try {
        const res = await fetch('http://localhost:8000/process_query', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ id, query }),
        });

        if (!res.ok) throw new Error('Server error');
        return await res.json();
      } catch (err) {
        console.error(err);
        throw err;
      }
      
     /* return { ai_answer: "This is the AI-generated answer.",
      page: 1,
      text: ""};
     */
    }
    else if(type==='image'){
      
      try {
        const res = await fetch('http://localhost:8000/generate-image', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ text_prompt: query }),
        });

        if (!res.ok) throw new Error('Server error');
        return await res.json();
      } catch (err) {
        console.error(err);
        throw err;
      }
      
     /*
        return {
      message: "Image generated and saved successfully!",
      original_prompt: "When the stars threw down their spears",
      optimized_prompt: "A dramatic celestial scene showing stars casting their spears in a cosmic battle",
      image_url: "http://localhost:8000/image_gen/image_When_the_stars_threw_4a8232b9.png"
      }
      */
    }
  };

  const createQueryResponseChunk = async (text: string, type: 'text'| 'image') => {
    const id = crypto.randomUUID();
    if (!text.trim()) return;
    const response = await generateLLMResponse(id, text, type);
    const newChunk: Chunk = {
      id: id,
      x: 50 + chunks.length * 30,
      y: 50 + chunks.length * 30,
      width: 300,
      height: type==='text' ? 150 : 300,
      query: text,
      answer: type==='text' ? response?.ai_answer : response?.image_url,
      color: getRandomColor(),
      fontSize: 12,
      type: type,
      loading: true,
      references: {
        page: type==='text' ? response?.page : pageNumber,
        text: type==='text' ? response?.text : text,
      },
    };
    setChunks((prev) => [...prev, newChunk]);

    setTimeout(() => {
      setChunks((prev) =>
        prev.map((chunk) =>
          chunk.id === id ? { ...chunk, loading: false } : chunk
        )
      );
    }, 1500);
  };

  const onDocumentLoadSuccess = ({ numPages }: { numPages: number }) => {
    setNumPages(numPages);
    setIsready(true);
  };

  return (
    <div className="p-4 space-y-4">
      {isDeleteModalOpen && (
  <div className="fixed inset-0 bg-black/10 backdrop-blur-sm flex items-center justify-center z-50">
    <div className="bg-white rounded-xl p-6 w-96 shadow-2xl border border-gray-200">
      <h2 className="text-lg font-semibold mb-4 text-gray-800">정말 삭제하시겠습니까?</h2>
      <p className="mb-6 text-sm text-gray-600">삭제된 청크는 복구할 수 없습니다.</p>
      <div className="flex justify-end gap-3">
        <button
          onClick={() => setIsDeleteModalOpen(false)}
          className="px-4 py-2 text-sm rounded-lg bg-gray-200 hover:bg-gray-300"
        >
          취소
        </button>
        <button
          onClick={() => {
            if (chunkToDelete) {
              handleDeleteChunk(chunkToDelete);
            }
            setIsDeleteModalOpen(false);
            setChunkToDelete(null);
          }}
          className="px-4 py-2 text-sm rounded-lg bg-red-500 text-white hover:bg-red-600"
        >
          삭제
        </button>
      </div>
    </div>
  </div>
)}
      <input type="file" accept="application/pdf" onChange={handleFileChange} />

      <div className="flex gap-4">
        <div className="border w-[1200px] h-[1000px] relative bg-white overflow-auto">
          {file && (
            <Document file={file} onLoadSuccess={onDocumentLoadSuccess}>
              <Page pageNumber={pageNumber} renderAnnotationLayer={false} />
            </Document>
          )}
          <div className="sticky bottom-2 left-2 bg-white p-1 rounded shadow">
            <button
              onClick={() => setPageNumber((p) => Math.max(p - 1, 1))}
              disabled={pageNumber <= 1}
              className="px-2"
            >
              ◀
            </button>
            <span className="mx-2">
              페이지 {pageNumber} / {numPages}
            </span>
            <button
              onClick={() => setPageNumber((p) => Math.min(p + 1, numPages))}
              disabled={pageNumber >= numPages}
              className="px-2"
            >
              ▶
            </button>
          </div>
        </div>

        <div className="w-[1500px] h-[1000px] border overflow-auto">
          <ReactFlowProvider>
            <ReactFlow
              nodes={nodes}
              edges={edges}
              onNodesChange={onNodesChange}
              onEdgesChange={onEdgesChange}
              onConnect={onConnect}
              onNodeClick={onNodeClick}
              onEdgeClick={onEdgeClick}
              fitView
            >
              <MiniMap />
              <Controls />
              <Background />
            </ReactFlow>
          </ReactFlowProvider>
        </div>
      </div>
      <div className="flex items-center p-2 border-t bg-white">
        <QueryInput
          onSubmit={createQueryResponseChunk} isready={isready}
        />
      </div>
    </div>
  );
}
