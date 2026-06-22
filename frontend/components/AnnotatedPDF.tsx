"use client";
import { useEffect, useRef, useState } from "react";

interface Props {
  base64Pdf: string;
}

export default function AnnotatedPDF({ base64Pdf }: Props) {
  const [blobUrl, setBlobUrl] = useState<string | null>(null);
  const prevUrl = useRef<string | null>(null);

  useEffect(() => {
    const bytes = Uint8Array.from(atob(base64Pdf), (c) => c.charCodeAt(0));
    const blob = new Blob([bytes], { type: "application/pdf" });
    const url = URL.createObjectURL(blob);
    setBlobUrl(url);
    prevUrl.current = url;

    return () => URL.revokeObjectURL(url);
  }, [base64Pdf]);

  const handleDownload = () => {
    if (!blobUrl) return;
    const a = document.createElement("a");
    a.href = blobUrl;
    a.download = "annotated_site_plan.pdf";
    a.click();
  };

  return (
    <div className="flex flex-col gap-3 h-full">
      <div className="flex items-center justify-between">
        <h2 className="text-sm font-semibold text-gray-700">Annotated Drawing</h2>
        <button
          onClick={handleDownload}
          disabled={!blobUrl}
          className="text-xs bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white px-3 py-1.5 rounded-lg transition-colors flex items-center gap-1.5"
        >
          <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
              d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
          </svg>
          Download PDF
        </button>
      </div>
      {blobUrl ? (
        <iframe
          src={blobUrl}
          className="w-full flex-1 rounded-lg border border-gray-200 min-h-[500px]"
          title="Annotated Site Plan"
        />
      ) : (
        <div className="flex-1 flex items-center justify-center text-gray-400 text-sm min-h-[500px]">
          Loading preview...
        </div>
      )}
    </div>
  );
}
