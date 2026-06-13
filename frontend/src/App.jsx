import { Routes, Route, Navigate, Link } from "react-router-dom";
import { useAuth } from "./context/AuthContext";
import ProtectedRoute from "./components/ProtectedRoute";
import LoginPage from "./pages/LoginPage";
import RegisterPage from "./pages/RegisterPage";
import CandidateListPage from "./pages/CandidateListPage";
import CandidateDetailPage from "./pages/CandidateDetailPage";

function Navbar() {
  const { user, logout, isAdmin } = useAuth();
  if (!user) return null;

  return (
    <nav className="bg-white border-b border-gray-200 px-6 py-3 flex items-center justify-between">
      <Link to="/candidates" className="text-lg font-semibold text-indigo-600">
        TechKraft Recruiter
      </Link>
      <div className="flex items-center gap-4">
        <span className="text-sm text-gray-600">
          {user.email}
          <span
            className={`ml-2 px-2 py-0.5 rounded-full text-xs font-medium ${
              isAdmin
                ? "bg-purple-100 text-purple-700"
                : "bg-blue-100 text-blue-700"
            }`}
          >
            {user.role}
          </span>
        </span>
        <button
          onClick={logout}
          className="text-sm text-gray-500 hover:text-red-600 transition-colors"
        >
          Logout
        </button>
      </div>
    </nav>
  );
}

export default function App() {
  return (
    <>
      <Navbar />
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />
        <Route
          path="/candidates"
          element={
            <ProtectedRoute>
              <CandidateListPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/candidates/:id"
          element={
            <ProtectedRoute>
              <CandidateDetailPage />
            </ProtectedRoute>
          }
        />
        <Route path="*" element={<Navigate to="/candidates" replace />} />
      </Routes>
    </>
  );
}
