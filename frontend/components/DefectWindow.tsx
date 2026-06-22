"use client";
import { ComplianceResult, ExtractedData } from "@/types/compliance";

interface Props {
  results: ComplianceResult[];
  extracted: ExtractedData;
  summary: { total: number; pass: number; fail: number; unknown: number };
}

function ConfidencePill({ value }: { value: number }) {
  const color =
    value >= 80 ? "bg-green-100 text-green-700" :
    value >= 50 ? "bg-yellow-100 text-yellow-700" :
                  "bg-red-100 text-red-700";
  return (
    <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${color}`}>
      {value}%
    </span>
  );
}

function StatusBadge({ status }: { status: string }) {
  const styles = {
    PASS: "bg-green-100 text-green-700 border-green-200",
    FAIL: "bg-red-100 text-red-700 border-red-200",
    UNKNOWN: "bg-gray-100 text-gray-500 border-gray-200",
  }[status] ?? "bg-gray-100 text-gray-500";
  return (
    <span className={`text-xs font-bold px-2.5 py-1 rounded border ${styles}`}>
      {status}
    </span>
  );
}

export default function DefectWindow({ results, extracted, summary }: Props) {
  const failures = results.filter((r) => r.status === "FAIL");

  return (
    <div className="flex flex-col gap-6">
      {/* Summary bar */}
      <div className="grid grid-cols-3 gap-3">
        {[
          { label: "Passed", count: summary.pass, color: "text-green-600 bg-green-50 border-green-200" },
          { label: "Failed", count: summary.fail, color: "text-red-600 bg-red-50 border-red-200" },
          { label: "Unknown", count: summary.unknown, color: "text-gray-500 bg-gray-50 border-gray-200" },
        ].map(({ label, count, color }) => (
          <div key={label} className={`rounded-lg border p-3 text-center ${color}`}>
            <div className="text-2xl font-bold">{count}</div>
            <div className="text-xs font-medium mt-0.5">{label}</div>
          </div>
        ))}
      </div>

      {/* Failures callout */}
      {failures.length > 0 && (
        <div className="rounded-lg border border-red-200 bg-red-50 p-4">
          <h3 className="text-sm font-semibold text-red-700 mb-2">
            {failures.length} Compliance Failure{failures.length > 1 ? "s" : ""} Detected
          </h3>
          <ul className="space-y-1">
            {failures.map((f) => (
              <li key={f.rule_key} className="text-sm text-red-600">
                <span className="font-medium">{f.label}:</span>{" "}
                {f.actual} (required {f.required})
                {f.deficiency != null && (
                  <span className="ml-1 text-red-500">— deficient by {f.deficiency}{f.required.includes("m") ? "m" : f.required.includes("%") ? "%" : ""}</span>
                )}
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Compliance table */}
      <div className="overflow-x-auto rounded-lg border border-gray-200">
        <table className="w-full text-sm">
          <thead>
            <tr className="bg-gray-50 border-b border-gray-200">
              <th className="text-left px-4 py-3 font-semibold text-gray-600">Rule</th>
              <th className="text-left px-4 py-3 font-semibold text-gray-600">Required</th>
              <th className="text-left px-4 py-3 font-semibold text-gray-600">Actual</th>
              <th className="text-left px-4 py-3 font-semibold text-gray-600">Confidence</th>
              <th className="text-left px-4 py-3 font-semibold text-gray-600">Status</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {results.map((r) => (
              <tr
                key={r.rule_key}
                className={r.status === "FAIL" ? "bg-red-50/50" : ""}
                title={r.note}
              >
                <td className="px-4 py-3 font-medium text-gray-800">{r.label}</td>
                <td className="px-4 py-3 text-gray-600">{r.required}</td>
                <td className="px-4 py-3 text-gray-800">
                  {r.actual ?? <span className="text-gray-400 italic">Unable to determine</span>}
                </td>
                <td className="px-4 py-3">
                  <ConfidencePill value={r.confidence} />
                </td>
                <td className="px-4 py-3">
                  <StatusBadge status={r.status} />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Extracted data detail */}
      <details className="group">
        <summary className="cursor-pointer text-sm font-medium text-gray-500 hover:text-gray-700 select-none">
          View all extracted values
        </summary>
        <div className="mt-3 grid grid-cols-2 gap-2 text-xs">
          {Object.entries(extracted).map(([key, field]) => (
            <div key={key} className="bg-gray-50 rounded p-2 border border-gray-100">
              <div className="font-medium text-gray-600 capitalize">{key.replace(/_/g, " ")}</div>
              <div className="text-gray-800 mt-0.5">
                {field.value != null ? `${field.value} ${field.unit}` : "—"}
                <span className="ml-2 text-gray-400">({field.confidence}%)</span>
              </div>
              {field.note && <div className="text-gray-400 mt-0.5 truncate" title={field.note}>{field.note}</div>}
            </div>
          ))}
        </div>
      </details>
    </div>
  );
}
