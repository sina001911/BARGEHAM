import { useEffect, useState } from "react";
import { academyApi } from "@/lib/api";
import AppShell from "@/components/layout/AppShell";
import LoadingSpinner from "@/components/ui/LoadingSpinner";
import Badge from "@/components/ui/Badge";
import { ArrowLeft, CheckCircle, XCircle, Clock } from "lucide-react";

export default function QuizPage() {
  const quizId = typeof window !== "undefined" ? window.location.hash.match(/quiz\/([^/]+)/)?.[1] : null;
  const [quiz, setQuiz] = useState<any>(null);
  const [attempt, setAttempt] = useState<any>(null);
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const [loading, setLoading] = useState(true);
  const [submitted, setSubmitted] = useState(false);

  const loadQuiz = async () => {
    if (!quizId) return;
    setLoading(true);
    try {
      const q = await academyApi.getQuiz(quizId);
      setQuiz(q);
      // Start a new attempt
      const a = await academyApi.startQuizAttempt(quizId);
      setAttempt(a);
    } catch (err) {
      console.error("Failed to load quiz:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { loadQuiz(); }, [quizId]);

  const handleSelect = (questionId: string, option: string) => {
    setAnswers((prev) => ({ ...prev, [questionId]: option }));
  };

  const handleSubmit = async () => {
    if (!attempt || submitted) return;
    setSubmitted(true);
    let correct = 0;
    const total = quiz?.questions?.length ?? 0;

    for (const q of quiz.questions) {
      try {
        await academyApi.submitQuizAnswer(attempt.id, q.id, answers[q.id] || "");
        if (answers[q.id] === q.correct_answer) correct++;
      } catch {
        // ignore individual submit errors
      }
    }
    setAttempt((prev: any) => ({ ...prev, score: correct, total_questions: total }));
  };

  if (loading) {
    return <AppShell currentPath="#academy"><div className="flex justify-center py-20"><LoadingSpinner /></div></AppShell>;
  }

  if (!quiz || !quiz.questions?.length) {
    return (
      <AppShell currentPath="#academy">
        <div className="flex flex-col items-center justify-center py-20 text-gray-500">
          <span className="text-5xl mb-4">❓</span>
          <p className="text-lg font-medium">آزمونی یافت نشد</p>
          <button onClick={() => { window.location.hash = "#academy"; }}
            className="mt-4 px-4 py-2 bg-bargeham-600 text-white rounded-lg hover:bg-bargeham-700">
            بازگشت
          </button>
        </div>
      </AppShell>
    );
  }

  const progress = submitted
    ? Math.round((attempt?.score ?? 0) / quiz.questions.length * 100)
    : Object.keys(answers).length / quiz.questions.length * 100;

  return (
    <AppShell currentPath="#academy">
      <div className="max-w-2xl mx-auto space-y-6">
        {/* Header */}
        <div className="flex items-center gap-4">
          <button onClick={() => { window.location.hash = "#academy"; }}
            className="p-2 rounded-lg border border-gray-200 hover:bg-gray-50">
            <ArrowLeft className="w-5 h-5 text-gray-600" />
          </button>
          <div className="flex-1">
            <h1 className="text-xl font-bold text-gray-900">{quiz.title}</h1>
            <div className="flex items-center gap-3 mt-1 text-sm text-gray-500">
              <Clock className="w-4 h-4" />
              <span>{quiz.questions?.length ?? 0} سؤال</span>
              <Badge variant="info">{quiz.quiz_type || "چندگزینه‌ای"}</Badge>
            </div>
          </div>
          {!submitted && (
            <span className="text-sm text-gray-500">
              {Object.keys(answers).length}/{quiz.questions.length} پاسخ داده
            </span>
          )}
        </div>

        {/* Progress bar */}
        <div className="w-full bg-gray-100 rounded-full h-2">
          <div className="bg-bargeham-600 h-2 rounded-full transition-all duration-300"
            style={{ width: `${progress}%` }} />
        </div>

        {/* Questions */}
        <div className="space-y-6">
          {quiz.questions.map((q: any, idx: number) => {
            const selected = answers[q.id];
            const isCorrect = submitted && selected === q.correct_answer;
            const isWrong = submitted && selected && selected !== q.correct_answer;

            return (
              <div key={q.id} className={`p-5 rounded-lg border ${
                submitted
                  ? isCorrect ? "border-green-200 bg-green-50"
                    : isWrong ? "border-red-200 bg-red-50"
                    : "border-gray-200 bg-white"
                  : "border-gray-200 bg-white hover:border-bargeham-300"
              } transition-colors`}>
                <div className="flex items-start gap-3 mb-4">
                  <span className="w-7 h-7 rounded-full bg-bargeham-100 text-bargeham-700 flex items-center justify-center text-sm font-bold shrink-0">
                    {idx + 1}
                  </span>
                  <p className="font-medium text-gray-900">{q.question_text}</p>
                </div>
                <div className="space-y-2 mr-10">
                  {(q.options || []).map((opt: string) => {
                    const isSelected = selected === opt;
                    const isCorrectOpt = opt === q.correct_answer;
                    return (
                      <button
                        key={opt}
                        disabled={submitted}
                        onClick={() => handleSelect(q.id, opt)}
                        className={`w-full text-right px-4 py-2.5 rounded-lg border text-sm transition-all ${
                          submitted
                            ? isCorrectOpt ? "border-green-500 bg-green-100 text-green-800"
                              : isSelected && isWrong ? "border-red-500 bg-red-100 text-red-800"
                              : "border-gray-200 text-gray-500"
                            : isSelected
                              ? "border-bargeham-500 bg-bargeham-50 text-bargeham-700"
                              : "border-gray-200 hover:border-bargeham-300 text-gray-700"
                        }`}
                      >
                        <span className="flex items-center gap-2">
                          {submitted && isCorrectOpt && <CheckCircle className="w-4 h-4 text-green-600 shrink-0" />}
                          {submitted && isSelected && isWrong && <XCircle className="w-4 h-4 text-red-600 shrink-0" />}
                          {opt}
                        </span>
                      </button>
                    );
                  })}
                </div>
                {submitted && q.explanation && (
                  <div className="mt-3 mr-10 text-sm text-gray-600 bg-gray-50 p-3 rounded-lg">
                    💡 {q.explanation}
                  </div>
                )}
              </div>
            );
          })}
        </div>

        {/* Submit button */}
        {!submitted && (
          <button
            onClick={handleSubmit}
            disabled={Object.keys(answers).length !== quiz.questions.length}
            className="w-full py-3 bg-bargeham-600 text-white rounded-lg font-semibold hover:bg-bargeham-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            ثبت و مشاهده نتیجه ({Object.keys(answers).length} / {quiz.questions.length})
          </button>
        )}

        {/* Score display */}
        {submitted && (
          <div className={`p-6 rounded-lg text-center ${
            progress >= 70 ? "bg-green-50 border border-green-200"
              : progress >= 40 ? "bg-yellow-50 border border-yellow-200"
              : "bg-red-50 border border-red-200"
          }`}>
            <p className="text-4xl font-bold text-gray-900">{progress}%</p>
            <p className="text-gray-600 mt-1">
              {attempt?.score ?? 0} پاسخ صحیح از {quiz.questions.length} سؤال
            </p>
            <button onClick={() => { window.location.hash = "#academy"; }}
              className="mt-4 px-6 py-2 bg-bargeham-600 text-white rounded-lg hover:bg-bargeham-700">
              بازگشت به دوره
            </button>
          </div>
        )}
      </div>
    </AppShell>
  );
}
