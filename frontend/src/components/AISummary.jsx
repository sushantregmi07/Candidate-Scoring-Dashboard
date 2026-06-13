import { useState } from "react";
import { generateSummary } from "../api/candidates";

export default function AISummary({ candidateId, existingSummary, onUpdated }) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleGenerate = async () => {
    setLoading(true);
    setError("");
    try {
      await generateSummary(candidateId);
      onUpdated();
    } catch (err) {
      setError(
        err.response?.data?.detail ||
          "Failed to generate summary. Please try again."
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-white rounded-xl border border-gray-200 p-5">
      <div className="flex items-center justify-between mb-3">
        <h3 className="font-semibold text-gray-900">AI Summary</h3>
        <button
          onClick={handleGenerate}
          disabled={loading}
          className="px-3 py-1.5 text-xs font-medium bg-violet-600 text-white rounded-lg hover:bg-violet-700 disabled:opacity-50 transition-colors flex items-center gap-1.5"
        >
          {loading && (
            <div className="animate-spin rounded-full h-3 w-3 border-b-2 border-white" />
          )}
          {loading
            ? "Generating..."
            : existingSummary
            ? "Regenerate"
            : "Generate Summary"}
        </button>
      </div>

      {error && (
        <div className="p-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700 flex items-start gap-2">
          <svg
            className="w-4 h-4 mt-0.5 flex-shrink-0"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M12 9v2m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
            />
          </svg>
          <span>{error}</span>
        </div>
      )}

      {loading && !error && (
        <div className="flex items-center gap-3 p-4 bg-violet-50 rounded-lg">
          <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-violet-600" />
          <span className="text-sm text-violet-700">
            Analyzing candidate profile...
          </span>
        </div>
      )}

      {!loading && !error && existingSummary && (
        <p className="text-sm text-gray-700 leading-relaxed bg-gray-50 rounded-lg p-4">
          {existingSummary}
        </p>
      )}

      {!loading && !error && !existingSummary && (
        <p className="text-sm text-gray-400">
          No summary generated yet. Click the button to generate one.
        </p>
      )}
    </div>
  );
}
