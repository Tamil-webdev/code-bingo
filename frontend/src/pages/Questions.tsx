import React, { useState, useEffect } from "react";
import { Plus, HelpCircle, Upload, Search, Trash2, SlidersHorizontal, AlertCircle } from "lucide-react";
import api from "../api";

interface Option {
  option_label: string;
  option_text: string;
  is_correct: boolean;
}

interface Question {
  id: string;
  question_text: string;
  code_snippet: string | null;
  question_type: string;
  language: string;
  difficulty: string;
  correct_answer: string;
  explanation: string | null;
  tags: string[];
}

export const Questions: React.FC = () => {
  const [questions, setQuestions] = useState<Question[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  // Filters
  const [search, setSearch] = useState("");
  const [lang, setLang] = useState("");
  const [diff, setDiff] = useState("");
  const [type, setType] = useState("");
  
  // Pagination
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);

  // Modals
  const [showCreate, setShowCreate] = useState(false);

  // New Question form state
  const [qText, setQText] = useState("");
  const [qSnippet, setQSnippet] = useState("");
  const [qLang, setQLang] = useState("python");
  const [qDiff, setQDiff] = useState("easy");
  const [qType, setQType] = useState("multiple_choice");
  const [qCorrect, setQCorrect] = useState("");
  const [qExpl, setQExpl] = useState("");
  const [qTags, setQTags] = useState("");
  const [qOptions, setQOptions] = useState<Option[]>([
    { option_label: "A", option_text: "", is_correct: false },
    { option_label: "B", option_text: "", is_correct: false },
    { option_label: "C", option_text: "", is_correct: false },
    { option_label: "D", option_text: "", is_correct: false }
  ]);

  const fetchQuestions = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams({
        page: String(page),
        per_page: "12",
      });
      if (search) params.append("search", search);
      if (lang) params.append("language", lang);
      if (diff) params.append("difficulty", diff);
      if (type) params.append("question_type", type);

      const response = await api.get(`/api/questions/?${params.toString()}`);
      setQuestions(response.data.items);
      setTotalPages(response.data.pages);
      setLoading(false);
    } catch (err) {
      setError("Failed to fetch questions");
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchQuestions();
  }, [page, lang, diff, type]);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setPage(1);
    fetchQuestions();
  };

  const handleCreateQuestion = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!qText.trim() || !qCorrect.trim()) return;

    try {
      // Process options
      const filteredOptions = qOptions.map((opt) => ({
        ...opt,
        is_correct: opt.option_label.toUpperCase() === qCorrect.toUpperCase()
      })).filter(o => o.option_text.trim() !== "");

      await api.post("/api/questions/", {
        question_text: qText.trim(),
        code_snippet: qSnippet.trim() || null,
        language: qLang,
        difficulty: qDiff,
        question_type: qType,
        correct_answer: qCorrect.trim(),
        explanation: qExpl.trim() || null,
        tags: qTags.split(",").map(t => t.trim()).filter(Boolean),
        options: filteredOptions
      });

      setSuccess("Question created successfully!");
      setShowCreate(false);
      // Reset
      setQText("");
      setQSnippet("");
      setQCorrect("");
      setQExpl("");
      setQTags("");
      fetchQuestions();
    } catch (err: any) {
      setError(err.response?.data?.detail || "Failed to save question");
    }
  };

  const handleDeleteQuestion = async (id: string) => {
    if (!confirm("Are you sure you want to delete this question?")) return;
    try {
      await api.delete(`/api/questions/${id}`);
      setSuccess("Question removed");
      fetchQuestions();
    } catch (err) {
      setError("Failed to delete question");
    }
  };

  const handleCSVUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    const formData = new FormData();
    formData.append("file", file);

    try {
      setError("");
      setSuccess("");
      await api.post("/api/questions/bulk-upload", formData, {
        headers: {
          "Content-Type": "multipart/form-data",
        },
      });
      setSuccess("CSV Question bank successfully uploaded!");
      fetchQuestions();
    } catch (err: any) {
      setError(err.response?.data?.detail || "Failed to process CSV file");
    }
  };

  return (
    <div className="space-y-8">
      {/* Top Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-extrabold tracking-wide">
            Question <span className="text-amber-500">Bank</span>
          </h1>
          <p className="text-slate-400 text-sm mt-1">
            Build custom quiz pools, manage multiple choice options, and perform CSV uploads
          </p>
        </div>

        <div className="flex flex-wrap gap-3">
          <label className="px-4 py-2.5 bg-slate-800 hover:bg-slate-700 text-slate-200 font-semibold rounded-xl flex items-center gap-2 text-sm cursor-pointer transition">
            <Upload className="w-4.5 h-4.5" />
            Upload CSV
            <input type="file" accept=".csv" onChange={handleCSVUpload} className="hidden" />
          </label>

          <button
            onClick={() => setShowCreate(true)}
            className="px-5 py-2.5 bg-amber-500 hover:bg-amber-400 text-slate-950 font-bold rounded-xl flex items-center gap-2 text-sm transition"
          >
            <Plus className="w-5 h-5" />
            Add Question
          </button>
        </div>
      </div>

      {error && (
        <div className="p-4 bg-rose-950/30 border border-rose-800/30 text-rose-300 rounded-xl flex gap-3 text-sm">
          <AlertCircle className="w-5 h-5" />
          <span>{error}</span>
        </div>
      )}

      {success && (
        <div className="p-4 bg-emerald-950/30 border border-emerald-800/30 text-emerald-300 rounded-xl text-sm">
          {success}
        </div>
      )}

      {/* Filter and Search Bar */}
      <div className="p-4 rounded-2xl bg-[#0E1524]/60 border border-slate-800 flex flex-col md:flex-row gap-4 items-center justify-between">
        <form onSubmit={handleSearchSubmit} className="flex gap-2 w-full md:max-w-md">
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search keywords..."
            className="w-full px-4 py-2 bg-slate-900 border border-slate-700 rounded-xl text-slate-200 text-sm focus:outline-none"
          />
          <button type="submit" className="p-2.5 bg-slate-800 hover:bg-slate-700 text-white rounded-xl">
            <Search className="w-4.5 h-4.5" />
          </button>
        </form>

        <div className="flex flex-wrap gap-3 items-center w-full md:w-auto">
          <SlidersHorizontal className="w-4.5 h-4.5 text-slate-500 hidden md:block" />
          
          <select
            value={lang}
            onChange={(e) => { setLang(e.target.value); setPage(1); }}
            className="px-3 py-2 bg-slate-900 border border-slate-700 rounded-xl text-slate-300 text-xs focus:outline-none"
          >
            <option value="">All Languages</option>
            <option value="python">Python</option>
            <option value="java">Java</option>
            <option value="c">C</option>
            <option value="cpp">C++</option>
            <option value="sql">SQL</option>
            <option value="html">HTML</option>
            <option value="javascript">JavaScript</option>
            <option value="mixed">Mixed</option>
          </select>

          <select
            value={diff}
            onChange={(e) => { setDiff(e.target.value); setPage(1); }}
            className="px-3 py-2 bg-slate-900 border border-slate-700 rounded-xl text-slate-300 text-xs focus:outline-none"
          >
            <option value="">All Difficulties</option>
            <option value="easy">Easy</option>
            <option value="medium">Medium</option>
            <option value="hard">Hard</option>
          </select>

          <select
            value={type}
            onChange={(e) => { setType(e.target.value); setPage(1); }}
            className="px-3 py-2 bg-slate-900 border border-slate-700 rounded-xl text-slate-300 text-xs focus:outline-none"
          >
            <option value="">All Types</option>
            <option value="multiple_choice">Multiple Choice</option>
            <option value="guess_output">Guess Output</option>
            <option value="fill_blank">Fill in Blank</option>
            <option value="true_false">True / False</option>
            <option value="debug_code">Debug Code</option>
            <option value="arrange_code">Arrange Code</option>
            <option value="select_complexity">Select Complexity</option>
            <option value="code_tracing">Code Tracing</option>
          </select>
        </div>
      </div>

      {/* Grid of Questions */}
      {loading ? (
        <div className="flex items-center justify-center py-12">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-amber-500"></div>
        </div>
      ) : questions.length === 0 ? (
        <div className="text-center py-12 text-slate-500">
          <HelpCircle className="w-12 h-12 mx-auto mb-4 opacity-30" />
          <p>No questions matched your filter query.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {questions.map((q) => (
            <div key={q.id} className="p-6 rounded-2xl glass-card border-slate-800 flex flex-col justify-between space-y-4">
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <div className="flex gap-2">
                    <span className="px-2 py-0.5 rounded bg-slate-800 text-[10px] uppercase font-bold tracking-wider text-slate-300">
                      {q.language}
                    </span>
                    <span className="px-2 py-0.5 rounded bg-slate-800 text-[10px] uppercase font-bold tracking-wider text-slate-300">
                      {q.difficulty}
                    </span>
                  </div>
                  <button
                    onClick={() => handleDeleteQuestion(q.id)}
                    className="p-1.5 text-slate-500 hover:text-rose-400 transition"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>

                <p className="text-slate-200 text-sm font-medium line-clamp-3 leading-relaxed">
                  {q.question_text}
                </p>

                {q.code_snippet && (
                  <pre className="p-2 bg-slate-900 border border-slate-800 rounded-lg text-xs text-emerald-400 overflow-x-auto truncate font-mono">
                    <code>{q.code_snippet.substring(0, 100)}...</code>
                  </pre>
                )}
              </div>

              <div className="pt-3 border-t border-slate-800 flex items-center justify-between text-xs text-slate-400">
                <span>Correct Answer: <span className="text-amber-400 font-bold font-mono">{q.correct_answer}</span></span>
                <span className="capitalize">{q.question_type.replace("_", " ")}</span>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Pagination buttons */}
      {totalPages > 1 && (
        <div className="flex items-center justify-center gap-4 pt-4">
          <button
            onClick={() => setPage(p => Math.max(1, p - 1))}
            disabled={page === 1}
            className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-white rounded-lg disabled:opacity-50 text-xs font-bold"
          >
            Previous
          </button>
          <span className="text-sm text-slate-400">Page {page} of {totalPages}</span>
          <button
            onClick={() => setPage(p => Math.min(totalPages, p + 1))}
            disabled={page === totalPages}
            className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-white rounded-lg disabled:opacity-50 text-xs font-bold"
          >
            Next
          </button>
        </div>
      )}

      {/* Create Question Modal */}
      {showCreate && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/80 backdrop-blur-sm p-4 overflow-y-auto">
          <form onSubmit={handleCreateQuestion} className="w-full max-w-2xl p-6 rounded-2xl glass-card border-slate-700 space-y-4 my-8">
            <h2 className="text-xl font-bold text-slate-200 font-mono">Add Coding Challenge</h2>

            <div className="grid grid-cols-3 gap-3">
              <div className="space-y-1">
                <label className="text-[10px] uppercase font-mono font-bold text-slate-400">Language</label>
                <select
                  value={qLang}
                  onChange={(e) => setQLang(e.target.value)}
                  className="w-full px-3 py-1.5 bg-slate-900 border border-slate-700 rounded-lg text-slate-200"
                >
                  <option value="python">Python</option>
                  <option value="java">Java</option>
                  <option value="c">C</option>
                  <option value="cpp">C++</option>
                  <option value="sql">SQL</option>
                  <option value="html">HTML</option>
                  <option value="javascript">JavaScript</option>
                  <option value="mixed">Mixed</option>
                </select>
              </div>

              <div className="space-y-1">
                <label className="text-[10px] uppercase font-mono font-bold text-slate-400">Difficulty</label>
                <select
                  value={qDiff}
                  onChange={(e) => setQDiff(e.target.value)}
                  className="w-full px-3 py-1.5 bg-slate-900 border border-slate-700 rounded-lg text-slate-200"
                >
                  <option value="easy">Easy</option>
                  <option value="medium">Medium</option>
                  <option value="hard">Hard</option>
                </select>
              </div>

              <div className="space-y-1">
                <label className="text-[10px] uppercase font-mono font-bold text-slate-400">Type</label>
                <select
                  value={qType}
                  onChange={(e) => setQType(e.target.value)}
                  className="w-full px-3 py-1.5 bg-slate-900 border border-slate-700 rounded-lg text-slate-200"
                >
                  <option value="multiple_choice">Multiple Choice</option>
                  <option value="guess_output">Guess Output</option>
                  <option value="fill_blank">Fill in Blank</option>
                  <option value="true_false">True / False</option>
                  <option value="debug_code">Debug Code</option>
                </select>
              </div>
            </div>

            <div className="space-y-1">
              <label className="text-[10px] uppercase font-mono font-bold text-slate-400">Question Text</label>
              <textarea
                value={qText}
                onChange={(e) => setQText(e.target.value)}
                placeholder="What is the result of..."
                required
                className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-slate-200 focus:outline-none"
              />
            </div>

            <div className="space-y-1">
              <label className="text-[10px] uppercase font-mono font-bold text-slate-400">Code Snippet (Optional)</label>
              <textarea
                value={qSnippet}
                onChange={(e) => setQSnippet(e.target.value)}
                placeholder="def hello():..."
                className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-slate-200 focus:outline-none font-mono"
              />
            </div>

            {/* Options setup */}
            {qType === "multiple_choice" && (
              <div className="space-y-2">
                <label className="text-[10px] uppercase font-mono font-bold text-slate-400">Multiple Choice Options</label>
                <div className="grid grid-cols-2 gap-3">
                  {qOptions.map((opt, idx) => (
                    <div key={opt.option_label} className="flex gap-2 items-center">
                      <span className="font-bold text-amber-500 font-mono text-sm">{opt.option_label}</span>
                      <input
                        type="text"
                        value={opt.option_text}
                        onChange={(e) => {
                          const val = e.target.value;
                          setQOptions(prev => prev.map((o, i) => i === idx ? { ...o, option_text: val } : o));
                        }}
                        placeholder={`Option ${opt.option_label}`}
                        className="w-full px-3 py-1 bg-slate-900 border border-slate-700 rounded-lg text-slate-200"
                      />
                    </div>
                  ))}
                </div>
              </div>
            )}

            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-1">
                <label className="text-[10px] uppercase font-mono font-bold text-slate-400">Correct Answer</label>
                <input
                  type="text"
                  value={qCorrect}
                  onChange={(e) => setQCorrect(e.target.value)}
                  placeholder="e.g. A, or exact text string"
                  required
                  className="w-full px-3 py-1.5 bg-slate-900 border border-slate-700 rounded-lg text-slate-200"
                />
              </div>

              <div className="space-y-1">
                <label className="text-[10px] uppercase font-mono font-bold text-slate-400">Tags (comma separated)</label>
                <input
                  type="text"
                  value={qTags}
                  onChange={(e) => setQTags(e.target.value)}
                  placeholder="arrays, algorithms"
                  className="w-full px-3 py-1.5 bg-slate-900 border border-slate-700 rounded-lg text-slate-200"
                />
              </div>
            </div>

            <div className="space-y-1">
              <label className="text-[10px] uppercase font-mono font-bold text-slate-400">Explanation</label>
              <textarea
                value={qExpl}
                onChange={(e) => setQExpl(e.target.value)}
                placeholder="Why is this answer correct?"
                className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-slate-200 focus:outline-none"
              />
            </div>

            <div className="flex justify-end gap-3 pt-2">
              <button
                type="button"
                onClick={() => setShowCreate(false)}
                className="px-4 py-2 bg-slate-800 text-slate-300 rounded-lg text-xs font-bold"
              >
                Cancel
              </button>
              <button
                type="submit"
                className="px-4 py-2 bg-amber-500 text-slate-950 font-bold rounded-lg text-xs"
              >
                Save
              </button>
            </div>
          </form>
        </div>
      )}
    </div>
  );
};
