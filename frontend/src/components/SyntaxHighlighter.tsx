import React from "react";

interface SyntaxHighlighterProps {
  code: string;
  language: string;
}

export const SyntaxHighlighter: React.FC<SyntaxHighlighterProps> = ({ code, language }) => {
  return (
    <div className="relative rounded-lg overflow-hidden border border-slate-700 bg-slate-900 font-mono text-sm leading-relaxed p-4 shadow-inner text-emerald-400">
      <div className="absolute top-2 right-3 text-xs text-slate-500 uppercase tracking-widest select-none">
        {language}
      </div>
      <pre className="overflow-x-auto whitespace-pre-wrap break-all">
        <code>{code}</code>
      </pre>
    </div>
  );
};
