import { useState } from "react";
import { submitScore } from "../api/candidates";

const CATEGORIES = [
  "Technical",
  "Communication",
  "Problem Solving",
  "Culture Fit",
  "Experience",
];

export default function ScoreForm({ candidateId, onScoreAdded }) {
  const [category, setCategory] = useState(CATEGORIES[0]);
  const [score, setScore] = useState(null);
  const [note, setNote] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  const canSubmit = category && score !== null && !loading;

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError("");
    setSuccess("");
    try {
      await submitScore(candidateId, {
        category,
        score,
        note: note || undefined,
      });
      setScore(null);
      setNote("");
      setCategory(CATEGORIES[0]);
      setSuccess("Score submitted successfully");
      setTimeout(() => setSuccess(""), 2000);
      onScoreAdded();
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to submit score");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-white rounded-xl border border-gray-200 p-5">
      <h3 className="font-semibold text-gray-900 mb-4">Submit Score</h3>

      {error && (
        <div className="mb-3 p-2 bg-red-50 border border-red-200 rounded text-sm text-red-700">
          {error}
        </div>
      )}
      {success && (
        <div className="mb-3 p-2 bg-green-50 border border-green-200 rounded text-sm text-green-700">
          {success}
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-3">
        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="block text-xs font-medium text-gray-500 mb-1">
              Category
            </label>
            <select
              value={category}
              onChange={(e) => setCategory(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
            >
              {CATEGORIES.map((c) => (
                <option key={c} value={c}>
                  {c}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-500 mb-1">
              Score (1-5)
            </label>
            <div className="flex items-center gap-1">
              {[1, 2, 3, 4, 5].map((val) => (
                <button
                  key={val}
                  type="button"
                  onClick={() => setScore(val)}
                  className={`w-9 h-9 rounded-lg text-sm font-medium transition-colors ${
                    score === val
                      ? "bg-indigo-600 text-white"
                      : "bg-gray-100 text-gray-600 hover:bg-gray-200"
                  }`}
                >
                  {val}
                </button>
              ))}
            </div>
          </div>
        </div>
        <div>
          <label className="block text-xs font-medium text-gray-500 mb-1">
            Note (optional)
          </label>
          <textarea
            value={note}
            onChange={(e) => setNote(e.target.value)}
            rows={2}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 resize-none"
            placeholder="Add context about this score..."
          />
        </div>
        <button
          type="submit"
          disabled={!canSubmit}
          className="px-4 py-2 bg-indigo-600 text-white rounded-lg text-sm font-medium hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          {loading ? "Submitting..." : "Submit Score"}
        </button>
      </form>
    </div>
  );
}
