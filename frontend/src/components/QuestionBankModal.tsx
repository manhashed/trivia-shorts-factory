import React, { useState, useEffect } from 'react';
import {
  BookOpen,
  X,
  Search,
  Download,
  ArrowRight,
} from 'lucide-react';
import { TriviaItem, CategoryInfo } from '../types';
import { getQuestionBank, getQuestionBankCategories } from '../services/api';

interface QuestionBankModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSelectQuestions: (questions: TriviaItem[]) => void;
}

export const QuestionBankModal: React.FC<QuestionBankModalProps> = ({
  isOpen,
  onClose,
  onSelectQuestions,
}) => {
  const [categories, setCategories] = useState<CategoryInfo[]>([]);
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  const [questions, setQuestions] = useState<TriviaItem[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    if (isOpen) {
      getQuestionBankCategories().then(setCategories).catch(console.error);
      loadCategoryQuestions('all');
    }
  }, [isOpen]);

  const loadCategoryQuestions = async (cat: string) => {
    setIsLoading(true);
    try {
      const res = await getQuestionBank(cat);
      setQuestions(res.questions);
      setSelectedCategory(cat);
    } catch (err) {
      console.error('Failed to load category questions:', err);
    } finally {
      setIsLoading(false);
    }
  };

  if (!isOpen) return null;

  const filteredQuestions = questions.filter((q) => {
    if (!searchQuery) return true;
    const term = searchQuery.toLowerCase();
    return (
      q.q.toLowerCase().includes(term) ||
      q.a.toLowerCase().includes(term) ||
      (q.category && q.category.toLowerCase().includes(term))
    );
  });

  const handleExportJson = () => {
    const jsonStr = JSON.stringify(filteredQuestions, null, 2);
    const blob = new Blob([jsonStr], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `kids_5_8_quiz_bank_${selectedCategory}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="bg-slate-900 border border-slate-700 w-full max-w-4xl rounded-3xl shadow-2xl flex flex-col max-h-[90vh] overflow-hidden">
        {/* Header */}
        <div className="px-6 py-5 border-b border-slate-800 flex items-center justify-between bg-slate-900/90">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-2xl bg-amber-500/20 text-amber-300 flex items-center justify-center">
              <BookOpen className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-lg font-bold text-white flex items-center gap-2">
                <span>100+ Early Elementary Trivia Bank (Ages 5–8)</span>
                <span className="text-xs px-2.5 py-0.5 rounded-full bg-amber-400 text-slate-950 font-bold">
                  100 Questions
                </span>
              </h2>
              <p className="text-xs text-slate-400">
                Classroom-ready questions across 10 fun categories with multiple choice options.
              </p>
            </div>
          </div>

          <button
            type="button"
            onClick={onClose}
            className="p-2 text-slate-400 hover:text-white rounded-xl hover:bg-slate-800 transition"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Category Filter Pills & Search */}
        <div className="px-6 py-3 border-b border-slate-800 bg-slate-950/60 space-y-3">
          {/* Search bar */}
          <div className="relative">
            <Search className="w-4 h-4 absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400" />
            <input
              type="text"
              placeholder="Search questions, answers, or categories..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full bg-slate-900 border border-slate-700/80 rounded-xl pl-10 pr-4 py-2 text-xs text-slate-200 focus:outline-none focus:border-amber-400"
            />
          </div>

          {/* Category Pills */}
          <div className="flex items-center gap-1.5 overflow-x-auto pb-1 custom-scrollbar text-xs">
            <button
              type="button"
              onClick={() => loadCategoryQuestions('all')}
              className={`px-3 py-1.5 rounded-xl font-semibold whitespace-nowrap transition text-xs ${
                selectedCategory === 'all'
                  ? 'bg-amber-400 text-slate-950 shadow'
                  : 'bg-slate-800 text-slate-300 hover:bg-slate-700'
              }`}
            >
              All Categories (100)
            </button>
            {categories.map((cat) => (
              <button
                key={cat.name}
                type="button"
                onClick={() => loadCategoryQuestions(cat.name)}
                className={`px-3 py-1.5 rounded-xl font-medium whitespace-nowrap transition text-xs ${
                  selectedCategory === cat.name
                    ? 'bg-amber-400 text-slate-950 font-bold shadow'
                    : 'bg-slate-800 text-slate-300 hover:bg-slate-700'
                }`}
              >
                {cat.name} ({cat.count})
              </button>
            ))}
          </div>
        </div>

        {/* Questions List Body */}
        <div className="flex-1 overflow-y-auto p-6 space-y-3 custom-scrollbar bg-slate-950/30">
          {isLoading ? (
            <div className="py-12 text-center text-xs text-amber-300 animate-pulse">
              Loading ages 5–8 questions...
            </div>
          ) : filteredQuestions.length === 0 ? (
            <div className="py-12 text-center text-xs text-slate-500">
              No questions found matching your search.
            </div>
          ) : (
            filteredQuestions.map((q, idx) => (
              <div
                key={q.id || idx}
                className="p-4 rounded-2xl bg-slate-900/80 border border-slate-800 hover:border-slate-700 transition space-y-2 text-xs"
              >
                <div className="flex items-center justify-between">
                  <span className="font-bold text-amber-400">
                    #{idx + 1} • {q.category}
                  </span>
                  <span className="text-[10px] text-slate-400 font-mono">{q.id}</span>
                </div>

                <p className="text-slate-100 font-semibold text-sm">{q.q}</p>

                {q.options && q.options.length > 0 && (
                  <div className="flex flex-wrap gap-1.5 pt-1">
                    {q.options.map((opt, optIdx) => (
                      <span
                        key={optIdx}
                        className="px-2 py-0.5 rounded-md bg-slate-800 text-slate-300 border border-slate-700 text-[11px]"
                      >
                        {String.fromCharCode(65 + optIdx)}: {opt}
                      </span>
                    ))}
                  </div>
                )}

                <p className="text-emerald-400 font-bold pt-1">
                  Answer: <span className="text-emerald-300">{q.a}</span>
                </p>
              </div>
            ))
          )}
        </div>

        {/* Footer Actions */}
        <div className="px-6 py-4 border-t border-slate-800 bg-slate-900 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <button
            type="button"
            onClick={handleExportJson}
            className="inline-flex items-center gap-1.5 text-xs text-slate-400 hover:text-white transition"
          >
            <Download className="w-4 h-4" />
            <span>Export Filtered ({filteredQuestions.length}) as JSON</span>
          </button>

          <div className="flex items-center gap-3">
            <button
              type="button"
              onClick={() => {
                onSelectQuestions(filteredQuestions);
                onClose();
              }}
              className="px-5 py-2.5 rounded-xl bg-gradient-to-r from-amber-400 to-yellow-400 text-slate-950 font-extrabold text-xs shadow-lg shadow-amber-500/20 hover:from-amber-300 hover:to-yellow-300 transition flex items-center gap-1.5"
            >
              <span>Load These {filteredQuestions.length} Questions</span>
              <ArrowRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
