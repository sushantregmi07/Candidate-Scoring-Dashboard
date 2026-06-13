import { useEffect, useState, useCallback } from "react";
import { useSearchParams, Link } from "react-router-dom";
import { listCandidates } from "../api/candidates";

const STATUS_OPTIONS = ["", "new", "reviewed", "hired", "rejected"];

const statusColors = {
  new: "bg-sky-100 text-sky-700",
  reviewed: "bg-amber-100 text-amber-700",
  hired: "bg-green-100 text-green-700",
  rejected: "bg-red-100 text-red-700",
};

export default function CandidateListPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const [data, setData] = useState({ items: [], total: 0, page: 1, pages: 0 });
  const [loading, setLoading] = useState(true);

  const status = searchParams.get("status") || "";
  const role_applied = searchParams.get("role_applied") || "";
  const skill = searchParams.get("skill") || "";
  const keyword = searchParams.get("keyword") || "";
  const page = parseInt(searchParams.get("page") || "1", 10);

  const updateParam = useCallback(
    (key, value) => {
      setSearchParams((prev) => {
        const next = new URLSearchParams(prev);
        if (value) {
          next.set(key, value);
        } else {
          next.delete(key);
        }
        if (key !== "page") next.set("page", "1");
        return next;
      });
    },
    [setSearchParams]
  );

  useEffect(() => {
    let cancelled = false;
    setLoading(true);

    const params = {};
    if (status) params.status = status;
    if (role_applied) params.role_applied = role_applied;
    if (skill) params.skill = skill;
    if (keyword) params.keyword = keyword;
    params.page = page;
    params.page_size = 10;

    listCandidates(params)
      .then((res) => {
        if (!cancelled) setData(res);
      })
      .catch(() => {})
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [status, role_applied, skill, keyword, page]);

  return (
    <div className="max-w-6xl mx-auto px-6 py-8">
      <h1 className="text-2xl font-bold text-gray-900 mb-6">Candidates</h1>

      {/* Filter Bar */}
      <div className="bg-white rounded-xl border border-gray-200 p-4 mb-6 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
        <div>
          <label className="block text-xs font-medium text-gray-500 mb-1">
            Status
          </label>
          <select
            value={status}
            onChange={(e) => updateParam("status", e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
          >
            <option value="">All Statuses</option>
            {STATUS_OPTIONS.filter(Boolean).map((s) => (
              <option key={s} value={s}>
                {s.charAt(0).toUpperCase() + s.slice(1)}
              </option>
            ))}
          </select>
        </div>
        <div>
          <label className="block text-xs font-medium text-gray-500 mb-1">
            Role Applied
          </label>
          <input
            type="text"
            value={role_applied}
            onChange={(e) => updateParam("role_applied", e.target.value)}
            placeholder="e.g. Backend Engineer"
            className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
          />
        </div>
        <div>
          <label className="block text-xs font-medium text-gray-500 mb-1">
            Skill
          </label>
          <input
            type="text"
            value={skill}
            onChange={(e) => updateParam("skill", e.target.value)}
            placeholder="e.g. React"
            className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
          />
        </div>
        <div>
          <label className="block text-xs font-medium text-gray-500 mb-1">
            Keyword
          </label>
          <input
            type="text"
            value={keyword}
            onChange={(e) => updateParam("keyword", e.target.value)}
            placeholder="Search name or email"
            className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
          />
        </div>
      </div>

      {/* Results */}
      {loading ? (
        <div className="flex justify-center py-12">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600" />
        </div>
      ) : data.items.length === 0 ? (
        <div className="text-center py-12 text-gray-500">
          No candidates found matching your filters.
        </div>
      ) : (
        <>
          <div className="grid gap-3">
            {data.items.map((c) => (
              <Link
                key={c.id}
                to={`/candidates/${c.id}`}
                className="bg-white rounded-xl border border-gray-200 p-4 hover:border-indigo-300 hover:shadow-sm transition-all flex items-center justify-between"
              >
                <div>
                  <h3 className="font-semibold text-gray-900">{c.name}</h3>
                  <p className="text-sm text-gray-500 mt-0.5">
                    {c.role_applied} &middot; {c.email}
                  </p>
                  {c.skills?.length > 0 && (
                    <div className="flex flex-wrap gap-1 mt-2">
                      {c.skills.map((s) => (
                        <span
                          key={s}
                          className="px-2 py-0.5 bg-gray-100 text-gray-600 rounded text-xs"
                        >
                          {s}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
                <span
                  className={`px-3 py-1 rounded-full text-xs font-medium ${
                    statusColors[c.status] || "bg-gray-100 text-gray-600"
                  }`}
                >
                  {c.status}
                </span>
              </Link>
            ))}
          </div>

          {/* Pagination */}
          {data.pages > 1 && (
            <div className="flex items-center justify-center gap-3 mt-6">
              <button
                disabled={page <= 1}
                onClick={() => updateParam("page", String(page - 1))}
                className="px-4 py-2 text-sm border border-gray-300 rounded-lg disabled:opacity-40 hover:bg-gray-50 transition-colors"
              >
                Previous
              </button>
              <span className="text-sm text-gray-600">
                Page {data.page} of {data.pages}
              </span>
              <button
                disabled={page >= data.pages}
                onClick={() => updateParam("page", String(page + 1))}
                className="px-4 py-2 text-sm border border-gray-300 rounded-lg disabled:opacity-40 hover:bg-gray-50 transition-colors"
              >
                Next
              </button>
            </div>
          )}
        </>
      )}
    </div>
  );
}
