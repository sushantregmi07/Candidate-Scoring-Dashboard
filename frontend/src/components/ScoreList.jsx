export default function ScoreList({ scores, isAdmin = false }) {
  if (!scores || scores.length === 0) {
    return (
      <div className="bg-white rounded-xl border border-gray-200 p-5">
        <h3 className="font-semibold text-gray-900 mb-3">Scores</h3>
        <p className="text-sm text-gray-400">No scores yet.</p>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-xl border border-gray-200 p-5">
      <h3 className="font-semibold text-gray-900 mb-3">
        Scores ({scores.length})
      </h3>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-gray-100">
              <th className="text-left py-2 pr-4 text-xs font-medium text-gray-500">
                Category
              </th>
              <th className="text-left py-2 pr-4 text-xs font-medium text-gray-500">
                Score
              </th>
              {isAdmin && (
                <th className="text-left py-2 pr-4 text-xs font-medium text-gray-500">
                  Reviewer
                </th>
              )}
              <th className="text-left py-2 pr-4 text-xs font-medium text-gray-500">
                Note
              </th>
              <th className="text-left py-2 text-xs font-medium text-gray-500">
                Date
              </th>
            </tr>
          </thead>
          <tbody>
            {scores.map((s) => (
              <tr key={s.id} className="border-b border-gray-50">
                <td className="py-2 pr-4 font-medium text-gray-800">
                  {s.category}
                </td>
                <td className="py-2 pr-4">
                  <span className="inline-flex items-center justify-center w-7 h-7 rounded-lg bg-indigo-50 text-indigo-700 font-semibold text-sm">
                    {s.score}
                  </span>
                </td>
                {isAdmin && (
                  <td className="py-2 pr-4 text-gray-600 text-xs">
                    <span className="font-medium text-gray-700">
                      {s.reviewer_username || "Unknown"}
                    </span>
                    <br />
                    <span className="text-gray-400">
                      {s.reviewer_email}
                    </span>
                  </td>
                )}
                <td className="py-2 pr-4 text-gray-600">
                  {s.note || <span className="text-gray-300">&mdash;</span>}
                </td>
                <td className="py-2 text-gray-400 text-xs">
                  {new Date(s.created_at).toLocaleDateString()}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
