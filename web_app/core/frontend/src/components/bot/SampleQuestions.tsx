import React, { useState } from 'react';
import { HelpCircle, X, ChevronDown, ChevronUp, MessageSquare } from 'lucide-react';

export interface SampleQuestionsProps {
  questions: string[];
  onQuestionSelect: (question: string) => void;
  className?: string;
}

const SampleQuestions: React.FC<SampleQuestionsProps> = ({
  questions,
  onQuestionSelect,
  className = ''
}) => {
  const [isVisible, setIsVisible] = useState(true);
  const [isExpanded, setIsExpanded] = useState(true);

  if (!isVisible) {
    return (
      <div className={`px-4 py-2 ${className}`}>
        <button
          onClick={() => setIsVisible(true)}
          className="text-sm text-gray-500 hover:text-red-500 flex items-center space-x-2 transition-colors"
        >
          <MessageSquare className="w-4 h-4" />
          <span>Show sample questions</span>
        </button>
      </div>
    );
  }

  return (
    <div className={`border-t border-gray-200/50 bg-gradient-to-r from-white to-gray-50 ${className}`}>
      {/* Header */}
      <div className="px-4 py-3 flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <HelpCircle className="w-4 h-4 text-red-500" />
          <span className="text-sm font-semibold text-gray-700">Quick Start Questions</span>
          <span className="text-xs bg-red-100 text-red-600 px-2 py-1 rounded-full">
            {questions.length}
          </span>
        </div>
        
        <div className="flex items-center space-x-1">
          <button
            onClick={() => setIsExpanded(!isExpanded)}
            className="p-1 text-gray-400 hover:text-gray-600 transition-colors rounded"
            aria-label={isExpanded ? "Collapse questions" : "Expand questions"}
          >
            {isExpanded ? (
              <ChevronUp className="w-4 h-4" />
            ) : (
              <ChevronDown className="w-4 h-4" />
            )}
          </button>
          
          <button
            onClick={() => setIsVisible(false)}
            className="p-1 text-gray-400 hover:text-gray-600 transition-colors rounded"
            aria-label="Hide sample questions"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Questions List */}
      {isExpanded && (
        <div className="px-4 pb-3 space-y-2 animate-fade-in">
          <div className="grid grid-cols-1 gap-2">
            {questions.map((question, index) => (
              <button
                key={index}
                onClick={() => onQuestionSelect(question)}
                className="group text-left text-xs bg-white hover:bg-red-50 text-gray-700 hover:text-red-700 px-3 py-2.5 rounded-lg border border-gray-200 hover:border-red-300 transition-all duration-200 shadow-sm hover:shadow-md transform hover:-translate-y-0.5"
              >
                <div className="flex items-start space-x-2">
                  <span className="text-red-400 group-hover:text-red-500 transition-colors flex-shrink-0 mt-0.5">
                    💬
                  </span>
                  <span className="leading-relaxed">{question}</span>
                </div>
              </button>
            ))}
          </div>
          
          {/* Help Text */}
          <div className="mt-3 pt-3 border-t border-gray-200">
            <p className="text-xs text-gray-500 text-center">
              Click any question above to get started, or type your own question below
            </p>
          </div>
        </div>
      )}
    </div>
  );
};

export default SampleQuestions;
