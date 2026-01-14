// src/components/VocabularyList.tsx
import React, { useMemo, useState } from 'react';
import { BookMarked, Search, Volume2 } from 'lucide-react';
import type { VocabularyItem, LearningVocabularyItem, VocabularyQuizQuestion } from '../types';

interface VocabularyListProps {
    vocabulary: VocabularyItem[];
    learningVocabulary: LearningVocabularyItem[];
    onSaveVocabulary: (item: LearningVocabularyItem) => void;
    quizQuestions: VocabularyQuizQuestion[];
    onRefreshQuiz: () => void;
}

const VocabularyList: React.FC<VocabularyListProps> = ({
    vocabulary,
    learningVocabulary,
    onSaveVocabulary,
    quizQuestions,
    onRefreshQuiz
}) => {
    const [selectedAnswers, setSelectedAnswers] = useState<Record<string, string>>({});

    const quizState = useMemo(() => {
        return quizQuestions.map((question) => {
            const selection = selectedAnswers[question.word];
            const isCorrect = selection ? selection === question.answer : null;
            return { ...question, selection, isCorrect };
        });
    }, [quizQuestions, selectedAnswers]);

    return (
        <div className="space-y-6">
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                <div>
                    <h1 className="text-3xl font-bold text-slate-900 dark:text-white">Word Bank</h1>
                    <p className="text-slate-500">Track and review words you've learned from reading.</p>
                </div>
                <div className="relative group">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 group-focus-within:text-blue-500 transition-colors" size={18} />
                    <input
                        type="text"
                        placeholder="Search words..."
                        className="pl-10 pr-4 py-2 bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-xl focus:ring-2 focus:ring-blue-500 outline-none w-full md:w-64 transition-all"
                    />
                </div>
            </div>

            <div className="bg-white dark:bg-slate-900 rounded-3xl border border-slate-200 dark:border-slate-800 p-6 space-y-4">
                <div className="flex flex-col md:flex-row md:items-center justify-between gap-3">
                    <div>
                        <h2 className="text-xl font-bold text-slate-900 dark:text-white">Quick Quiz</h2>
                        <p className="text-sm text-slate-500">Test whether you remember your learned words.</p>
                    </div>
                    <button
                        onClick={onRefreshQuiz}
                        className="text-xs font-semibold px-3 py-1.5 rounded-full border border-slate-200 dark:border-slate-700 text-slate-600 dark:text-slate-300 hover:border-blue-500 hover:text-blue-600 transition-colors"
                    >
                        Refresh Quiz
                    </button>
                </div>
                {quizState.length === 0 ? (
                    <p className="text-sm text-slate-500">Add more words to your word bank to unlock quizzes.</p>
                ) : (
                    <div className="space-y-4">
                        {quizState.map((question, index) => (
                            <div
                                key={`${question.word}-${index}`}
                                className="border border-slate-100 dark:border-slate-800 rounded-2xl p-4 space-y-3"
                            >
                                <div className="space-y-1">
                                    <p className="text-xs uppercase tracking-wide text-slate-400">Question {index + 1}</p>
                                    <p className="text-sm font-semibold text-slate-900 dark:text-white">
                                        {question.question}
                                    </p>
                                </div>
                                <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                                    {question.options.map((option, optIndex) => {
                                        const isSelected = question.selection === option;
                                        const isCorrect = question.isCorrect === true && option === question.answer;
                                        const isWrong = question.isCorrect === false && isSelected;
                                        return (
                                            <button
                                                key={`${question.word}-${optIndex}`}
                                                onClick={() =>
                                                    setSelectedAnswers((prev) => ({
                                                        ...prev,
                                                        [question.word]: option
                                                    }))
                                                }
                                                className={`text-left text-sm px-3 py-2 rounded-xl border transition-colors ${
                                                    isCorrect
                                                        ? 'border-emerald-500 bg-emerald-50 text-emerald-700 dark:bg-emerald-500/10 dark:text-emerald-300'
                                                        : isWrong
                                                            ? 'border-rose-500 bg-rose-50 text-rose-700 dark:bg-rose-500/10 dark:text-rose-300'
                                                            : isSelected
                                                                ? 'border-blue-500 bg-blue-50 text-blue-700 dark:bg-blue-500/10 dark:text-blue-300'
                                                                : 'border-slate-200 dark:border-slate-800 text-slate-600 dark:text-slate-300 hover:border-blue-400 hover:text-blue-600'
                                                }`}
                                            >
                                                {option}
                                            </button>
                                        );
                                    })}
                                </div>
                                {question.selection && (
                                    <p className={`text-xs font-semibold ${
                                        question.isCorrect
                                            ? 'text-emerald-600 dark:text-emerald-400'
                                            : 'text-rose-600 dark:text-rose-400'
                                    }`}>
                                        {question.isCorrect ? 'Correct!' : `Not quite. Correct answer: ${question.answer}`}
                                    </p>
                                )}
                            </div>
                        ))}
                    </div>
                )}
            </div>

            <div className="bg-white dark:bg-slate-900 rounded-3xl border border-slate-200 dark:border-slate-800 p-6 space-y-4">
                <div className="flex items-center justify-between">
                    <div>
                        <h2 className="text-xl font-bold text-slate-900 dark:text-white">Daily Vocabulary</h2>
                        <p className="text-sm text-slate-500">Learn new words from the built-in vocabulary list.</p>
                    </div>
                </div>
                {learningVocabulary.length === 0 ? (
                    <p className="text-sm text-slate-500">No new words available right now.</p>
                ) : (
                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                        {learningVocabulary.map((item) => (
                            <div
                                key={item.id}
                                className="border border-slate-100 dark:border-slate-800 rounded-2xl p-4 space-y-3"
                            >
                                <div className="flex items-start justify-between gap-4">
                                    <div>
                                        <h3 className="text-lg font-bold text-slate-900 dark:text-white">
                                            {item.word}
                                        </h3>
                                        {item.translation && (
                                            <p className="text-sm text-emerald-600 dark:text-emerald-400">
                                                {item.translation}
                                            </p>
                                        )}
                                    </div>
                                    <button
                                        onClick={() => onSaveVocabulary(item)}
                                        className="text-xs font-semibold px-3 py-1.5 rounded-full bg-blue-600 text-white hover:bg-blue-700 transition-colors"
                                    >
                                        Add to Word Bank
                                    </button>
                                </div>
                                {item.definition && (
                                    <p className="text-sm text-slate-600 dark:text-slate-400 italic">
                                        {item.definition}
                                    </p>
                                )}
                                {item.example_sentence && (
                                    <div className="text-sm text-slate-500 space-y-1">
                                        <p>“{item.example_sentence}”</p>
                                        {item.example_translation && (
                                            <p className="text-xs text-slate-400">
                                                {item.example_translation}
                                            </p>
                                        )}
                                    </div>
                                )}
                            </div>
                        ))}
                    </div>
                )}
            </div>

            {vocabulary.length === 0 ? (
                <div className="bg-white dark:bg-slate-900 rounded-3xl p-12 text-center border border-dashed border-slate-200 dark:border-slate-800">
                    <BookMarked size={48} className="mx-auto text-slate-300 mb-4" />
                    <h3 className="text-lg font-semibold dark:text-white">Your word bank is empty</h3>
                    <p className="text-slate-500 max-w-xs mx-auto">Start reading and click on words you don't know to add them here.</p>
                </div>
            ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    {vocabulary.map((item, idx) => (
                        <div
                            key={idx}
                            className="bg-white dark:bg-slate-900 p-5 rounded-2xl border border-slate-200 dark:border-slate-800 hover:shadow-md transition-shadow group"
                        >
                            <div className="flex items-start justify-between">
                                <div>
                                    <h3 className="text-xl font-bold text-slate-900 dark:text-white group-hover:text-blue-600 transition-colors">
                                        {item.word}
                                    </h3>
                                    {item.pronunciation && (
                                        <div className="flex items-center space-x-2 text-slate-400 text-sm mt-1">
                                            <Volume2 size={14} className="hover:text-blue-500 cursor-pointer" />
                                            <span>{item.pronunciation}</span>
                                        </div>
                                    )}
                                </div>
                                {item.cefr && (
                                    <span className="px-2 py-0.5 bg-blue-50 dark:bg-blue-900/20 text-blue-600 dark:text-blue-400 text-[10px] font-black rounded-md uppercase">
                                        {item.cefr}
                                    </span>
                                )}
                            </div>
                            <p className="mt-3 text-sm text-slate-600 dark:text-slate-400 leading-relaxed italic border-l-2 border-slate-100 dark:border-slate-800 pl-3">
                                {item.definition || 'No definition available.'}
                            </p>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
};

export default VocabularyList;
