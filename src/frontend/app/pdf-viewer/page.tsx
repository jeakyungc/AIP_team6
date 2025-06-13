import PDFViewer from '@/components/PDFViewer'

export default function PDFViewerPage() {
  return (
    <div className="p-4">
      <h1 className="text-xl font-bold mb-4">📄 PDF 청크 뷰어</h1>
      <PDFViewer />
    </div>
  )
}
