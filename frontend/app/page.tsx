"use client";
import { useState, useCallback } from "react";
import PDFUpload from "@/components/PDFUpload";
import DefectWindow from "@/components/DefectWindow";
import AnnotatedPDF from "@/components/AnnotatedPDF";
import { analyzePDF } from "@/lib/api";
import { AnalysisResponse } from "@/types/compliance";

type Stage = "idle" | "loading" | "done" | "error";

export default function Home() {
  const [stage, setStage] = useState<Stage>("idle");
  const [result, setResult] = useState<AnalysisResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleFile = useCallback(async (file: File) => {
    setStage("loading");
    setError(null);
    setResult(null);
    try {
      const data = await analyzePDF(file);
      setResult(data);
      setStage("done");
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Unknown error");
      setStage("error");
    }
  }, []);

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center gap-3">
          <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center">
            <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
            </svg>
          </div>
          <div>
            <h1 className="text-lg font-bold text-gray-900">PlotPerfect</h1>
            <p className="text-xs text-gray-500">Zoning Compliance Checker</p>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-6 py-8">
        <div className="mb-8">
          <PDFUpload onFile={handleFile} loading={stage === "loading"} />
        </div>

        {stage === "loading" && (
          <div className="flex flex-col items-center gap-4 py-16">
            <div className="w-10 h-10 border-4 border-blue-600 border-t-transparent rounded-full animate-spin" />
            <div className="text-center">
              <p className="font-medium text-gray-700">Analyzing your site plan</p>
              <p className="text-sm text-gray-400 mt-1">Extracting measurements and checking compliance...</p>
            </div>
          </div>
        )}

        {stage === "error" && error && (
          <div className="rounded-xl border border-red-200 bg-red-50 p-6 text-center">
            <p className="font-semibold text-red-700">Analysis failed</p>
            <p className="text-sm text-red-500 mt-1">{error}</p>
          </div>
        )}

        {stage === "done" && result && (
          <div className="grid grid-cols-1 xl:grid-cols-2 gap-8">
            <div className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm">
              <h2 className="text-base font-semibold text-gray-900 mb-5">
                Compliance Defect Window
              </h2>
              <DefectWindow
                results={result.compliance}
                extracted={result.extracted}
                summary={result.summary}
              />
            </div>
            <div className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm flex flex-col">
              {result.annotated_pdf ? (
                <AnnotatedPDF base64Pdf={result.annotated_pdf} />
              ) : (
                <div className="flex-1 flex items-center justify-center text-gray-400 text-sm">
                  Annotated drawing unavailable
                </div>
              )}
            </div>
          </div>
        )}

        {stage === "idle" && (
          <div className="text-center py-12 text-gray-400 text-sm">
            Upload a site plan PDF to begin compliance analysis
          </div>
        )}
      </main>
    </div>
  );
}
