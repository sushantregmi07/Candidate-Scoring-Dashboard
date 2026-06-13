import { useEffect, useState, useCallback } from "react";
import { useParams, Link } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { getCandidate } from "../api/candidates";
import ScoreForm from "../components/ScoreForm";
import ScoreList from "../components/ScoreList";
import AISummary from "../components/AISummary";
import InternalNotes from "../components/InternalNotes";

const statusColors = {
  new: "bg-sky-100 text-sky-700",
  reviewed: "bg-amber-100 text-amber-700",
  hired: "bg-green-100 text-green-700",
  rejected: "bg-red-100 text-red-700",
};

export default function CandidateDetailPage() {
  const { id } = useParams();
  const { isAdmin } = useAuth();
  const [candidate, setCandidate] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const fetchCandidate = useCallback(async () => {
    try {
      const data = await getCandidate(id);
      setCandidate(data);
      setError("");
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to load candidate");
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => {
    fetchCandidate();
  }, [fetchCandidate]);

  if (loading) {
    return (
      <div className="flex justify-center py-20">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="max-w-3xl mx-auto px-6 py-12 text-center">
        <p className="text-red-600 mb-4">{error}</p>
        <Link
          to="/candidates"
          className="text-indigo-600 hover:underline text-sm"
        >
          Back to list
        </Link>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto px-6 py-8">
      <Link
        to="/candidates"
        className="text-sm text-indigo-600 hover:underline mb-4 inline-block"
      >
        &larr; Back to candidates
      </Link>

      {/* Profile Header */}
      <div className="bg-white rounded-xl border border-gray-200 p-6 mb-5">
        <div className="flex items-start justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">
              {candidate.name}
            </h1>
            <p className="text-gray-500 mt-1">{candidate.email}</p>
            <p className="text-sm text-gray-600 mt-2">
              Applying for:{" "}
              <span className="font-medium">{candidate.role_applied}</span>
            </p>
            {candidate.skills?.length > 0 && (
              <div className="flex flex-wrap gap-1.5 mt-3">
                {candidate.skills.map((s) => (
                  <span
                    key={s}
                    className="px-2.5 py-1 bg-gray-100 text-gray-700 rounded-md text-xs font-medium"
                  >
                    {s}
                  </span>
                ))}
              </div>
            )}
          </div>
          <span
            className={`px-3 py-1.5 rounded-full text-sm font-medium ${
              statusColors[candidate.status] || "bg-gray-100 text-gray-600"
            }`}
          >
            {candidate.status}
          </span>
        </div>
        <p className="text-xs text-gray-400 mt-4">
          Applied on {new Date(candidate.created_at).toLocaleDateString()}
        </p>
      </div>

      <div className="grid gap-5">
        <ScoreList scores={candidate.scores} />
        <ScoreForm candidateId={id} onScoreAdded={fetchCandidate} />
        <AISummary
          candidateId={id}
          existingSummary={candidate.ai_summary}
          onUpdated={fetchCandidate}
        />
        {isAdmin && (
          <InternalNotes
            candidateId={id}
            initialNotes={candidate.internal_notes}
          />
        )}
      </div>
    </div>
  );
}
