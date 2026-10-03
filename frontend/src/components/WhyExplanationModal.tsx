import React from "react";
import { X, HelpCircle, CheckCircle2, AlertTriangle, ShieldCheck, Info } from "lucide-react";
import { ExplanationBlock } from "../types/asset";

interface WhyModalProps {
  isOpen: boolean;
  onClose: () => void;
  title: string;
  category: "moderation" | "tags" | "crop" | "recommendations" | "quality";
  data?: ExplanationBlock;
}

export const WhyExplanationModal: React.FC<WhyModalProps> = ({
  isOpen,
  onClose,
  title,
  category,
  data,
}) => {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm animate-fadeIn">
      <div className="glass-card w-full max-w-lg rounded-3xl p-6 border-slate-700/80 shadow-2xl relative bg-slate-900/95 space-y-4">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-slate-800 pb-3">
          <div className="flex items-center space-x-2">
            <div className="p-2 rounded-xl bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
              <HelpCircle className="w-4 h-4" />
            </div>
            <div>
              <h3 className="text-sm font-semibold text-white">{title}</h3>
              <p className="text-[11px] text-slate-400 capitalize">Explainable AI & Grounded Reasoning</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-xl text-slate-400 hover:text-white hover:bg-slate-800/80 transition"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Content */}
        {!data ? (
          <div className="p-4 rounded-2xl bg-slate-950/50 border border-slate-800 text-xs text-slate-400">
            Insufficient metadata to explain this decision.
          </div>
        ) : (
          <div className="space-y-4">
            <div className="p-3.5 rounded-2xl bg-indigo-950/30 border border-indigo-500/20 text-xs text-indigo-200 font-medium">
              {data.summary}
            </div>

            <div className="space-y-2">
              <div className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
                Grounded Decision Signals
              </div>
              <ul className="space-y-2">
                {data.points && data.points.length > 0 ? (
                  data.points.map((pt, idx) => (
                    <li
                      key={idx}
                      className="flex items-start space-x-2.5 text-xs text-slate-300 p-2.5 rounded-xl bg-slate-950/40 border border-slate-800/80"
                    >
                      <span className="text-cyan-400 mt-0.5">•</span>
                      <span>{pt}</span>
                    </li>
                  ))
                ) : (
                  <li className="text-xs text-slate-500 italic">No specific signals were recorded.</li>
                )}
              </ul>
            </div>
          </div>
        )}

        {/* Footer */}
        <div className="pt-2 border-t border-slate-800/80 flex justify-end">
          <button
            onClick={onClose}
            className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium rounded-xl transition"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
};
