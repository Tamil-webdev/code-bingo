import React, { useState, useEffect } from "react";
import { X, Clock, HelpCircle, AlertCircle, CheckCircle, XCircle } from "lucide-react";
import { SyntaxHighlighter } from "./SyntaxHighlighter";
import api from "../api";

export interface QuestionData {
  id: string;
  question_text: string;
  code_snippet: string | null;
  question_type: string;
  language: string;
  difficulty: string;
  time_limit: number;
  options: { option_label: string; option_text: string }[];
}

interface QuestionModalProps {
  tileId: string;
  onClose: () => void;
  onAnswerSubmitted: (result: {
    is_correct: boolean;
    correct_answer: string;
    explanation: string;
    points_earned: number;
    new_score: number;
    new_bingo_count: number;
    tile_status: string;
  }) => void;
}

export const QuestionModal: React.FC<QuestionModalProps> = ({
  tileId,
  onClose,
  onAnswerSubmitted,
}) => {
  const [question, setQuestion] = useState<QuestionData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [timeLeft, setTimeLeft] = useState(60);
  const [selectedOption, setSelectedOption] = useState("");
  const [textAnswer, setTextAnswer] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [result, setResult] = useState<{
    is_correct: boolean;
    correct_answer: string;
    explanation: string;
    points_earned: number;
  } | null>(null);

  // Fetch question details
  useEffect(() => {
    const fetchQuestion = async () => {
      try {
        const response = await api.get(`/api/game/tile/${tileId}/question`);
        setQuestion(response.data);
        setTimeLeft(response.data.time_limit || 60);
        setLoading(false);
      } catch (err: any) {
        setError(err.response?.data?.detail || "Failed to load question");
        setLoading(false);
      }
    };
    fetchQuestion();
  }, [tileId]);

  // Countdown timer logic
  useEffect(() => {
    if (loading || result || timeLeft <= 0) return;

    const timer = setInterval(() => {
      setTimeLeft((prev) => {
        if (prev <= 1) {
          clearInterval(timer);
          handleSubmit(true); // Auto-submit when time expires
          return 0;
        }
        return prev - 1;
      });
    }, 1000);

    return () => clearInterval(timer);
  }, [loading, result, timeLeft]);

  const handleSubmit = async (isTimeOut = false) => {
    if (submitting || result) return;
    setSubmitting(true);

    const answer = question?.question_type === "multiple_choice" || 
                   question?.question_type === "true_false" || 
                   question?.question_type === "select_complexity"
      ? selectedOption 
      : textAnswer;

    const timeTaken = question ? question.time_limit - timeLeft : 0;

    try {
      const response = await api.post("/api/game/submit-answer", {
        tile_id: tileId,
        answer: isTimeOut ? "TIMEOUT_NO_ANSWER" : answer,
        time_taken_seconds: timeTaken,
      });

      setResult({
        is_correct: response.data.is_correct,
        correct_answer: response.data.correct_answer,
        explanation: response.data.explanation,
        points_earned: response.data.points_earned,
      });

      // Notify parent of updates
      setTimeout(() => {
        onAnswerSubmitted(response.data);
      }, 3000); // Let them view the answer feedback for 3 seconds before auto-closing
    } catch (err: any) {
      setError(err.response?.data?.detail || "Failed to submit answer");
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return (
      <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/80 backdrop-blur-sm">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-amber-500"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/80 backdrop-blur-sm p-4">
        <div className="w-full max-w-md p-6 rounded-2xl glass-card text-center border-rose-500/30">
          <AlertCircle className="w-12 h-12 text-rose-500 mx-auto mb-4" />
          <p className="text-slate-200 mb-6">{error}</p>
          <button
            onClick={onClose}
            className="w-full py-2.5 bg-slate-800 hover:bg-slate-700 text-white rounded-xl font-semibold transition"
          >
            Close
          </button>
        </div>
      </div>
    );
  }

  if (!question) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/85 backdrop-blur-md p-4 overflow-y-auto">
      <div className="w-full max-w-3xl rounded-2xl glass-card border-slate-700/50 shadow-2xl overflow-hidden my-8">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-800 bg-slate-900/60">
          <div className="flex items-center gap-3">
            <HelpCircle className="w-5 h-5 text-amber-500" />
            <span className="font-semibold text-slate-200 uppercase tracking-wider text-sm font-mono">
              {question.language} • {question.difficulty}
            </span>
          </div>

          <div className="flex items-center gap-6">
            {/* Timer */}
            <div className={`flex items-center gap-2 px-3 py-1.5 rounded-full font-mono font-bold text-sm ${
              timeLeft <= 10 ? "bg-rose-950/40 text-rose-400 border border-rose-800/50 animate-pulse" : "bg-slate-800 text-slate-300 border border-slate-700"
            }`}>
              <Clock className="w-4 h-4" />
              <span>{timeLeft}s</span>
            </div>

            <button
              onClick={onClose}
              disabled={submitting}
              className="text-slate-400 hover:text-white transition disabled:opacity-50"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Body */}
        <div className="p-6 space-y-6">
          {/* Question Text */}
          <div className="text-lg md:text-xl font-medium text-slate-100 whitespace-pre-wrap">
            {question.question_text}
          </div>

          {/* Code Snippet (if exists) */}
          {question.code_snippet && (
            <SyntaxHighlighter code={question.code_snippet} language={question.language} />
          )}

          {/* Feedback Section (Correct/Incorrect message) */}
          {result && (
            <div className={`p-4 rounded-xl border flex gap-4 ${
              result.is_correct 
                ? "bg-emerald-950/40 border-emerald-500/30 text-emerald-300"
                : "bg-rose-950/40 border-rose-500/30 text-rose-300"
            }`}>
              <div className="mt-0.5">
                {result.is_correct ? <CheckCircle className="w-6 h-6 text-emerald-400" /> : <XCircle className="w-6 h-6 text-rose-400" />}
              </div>
              <div>
                <h4 className="font-bold text-lg">{result.is_correct ? "Correct! +10 Points" : "Incorrect Answer"}</h4>
                <p className="text-slate-300 text-sm mt-1">Correct Answer: <span className="font-mono font-bold text-white">{result.correct_answer}</span></p>
                {result.explanation && (
                  <p className="text-slate-400 text-xs mt-2 italic leading-relaxed">
                    Explanation: {result.explanation}
                  </p>
                )}
              </div>
            </div>
          )}

          {/* Options / Input Form */}
          {!result && (
            <div className="space-y-4">
              {/* Option Selection or Input */}
              {question.options.length > 0 ? (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {question.options.map((opt) => {
                    const isSelected = selectedOption === opt.option_label;
                    return (
                      <button
                        key={opt.option_label}
                        onClick={() => setSelectedOption(opt.option_label)}
                        className={`flex items-start gap-3 p-4 rounded-xl border text-left transition-all duration-200 ${
                          isSelected
                            ? "bg-amber-950/40 border-amber-500 text-amber-200 shadow-md shadow-amber-500/5"
                            : "bg-slate-800/40 border-slate-700/60 text-slate-300 hover:bg-slate-800 hover:text-white"
                        }`}
                      >
                        <span className={`flex items-center justify-center w-6 h-6 rounded-full font-mono text-xs font-bold border transition ${
                          isSelected 
                            ? "bg-amber-500 border-amber-500 text-slate-950" 
                            : "bg-slate-700/50 border-slate-600 text-slate-400"
                        }`}>
                          {opt.option_label}
                        </span>
                        <span className="flex-1 text-sm md:text-base leading-snug">{opt.option_text}</span>
                      </button>
                    );
                  })}
                </div>
              ) : (
                <div className="space-y-2">
                  <label className="block text-sm font-semibold text-slate-400 font-mono tracking-wider uppercase">
                    Your Answer
                  </label>
                  <input
                    type="text"
                    value={textAnswer}
                    onChange={(e) => setTextAnswer(e.target.value)}
                    placeholder="Type your answer here..."
                    className="w-full px-4 py-3 bg-slate-900 border border-slate-700 rounded-xl text-slate-100 placeholder-slate-500 focus:outline-none focus:border-amber-500 font-mono transition"
                  />
                </div>
              )}
            </div>
          )}
        </div>

        {/* Footer */}
        {!result && (
          <div className="flex items-center justify-end gap-3 px-6 py-4 border-t border-slate-800 bg-slate-900/40">
            <button
              onClick={onClose}
              disabled={submitting}
              className="px-5 py-2.5 bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white rounded-xl font-semibold transition disabled:opacity-50"
            >
              Cancel
            </button>
            <button
              onClick={() => handleSubmit(false)}
              disabled={submitting || (question.options.length > 0 ? !selectedOption : !textAnswer.trim())}
              className="px-6 py-2.5 bg-amber-500 hover:bg-amber-400 disabled:bg-slate-700 text-slate-950 disabled:text-slate-500 rounded-xl font-semibold shadow-lg shadow-amber-500/10 hover:shadow-amber-500/20 hover:-translate-y-0.5 transition-all duration-200"
            >
              {submitting ? "Submitting..." : "Submit Answer"}
            </button>
          </div>
        )}
      </div>
    </div>
  );
};
