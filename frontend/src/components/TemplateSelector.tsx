import React from 'react';
import { Check, Film } from 'lucide-react';
import { TemplateInfo } from '../types';

interface TemplateSelectorProps {
  templates: TemplateInfo[];
  selectedTemplateId: string;
  onSelectTemplate: (template: TemplateInfo) => void;
}

export const TemplateSelector: React.FC<TemplateSelectorProps> = ({
  templates,
  selectedTemplateId,
  onSelectTemplate,
}) => {
  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <label className="text-sm font-bold text-white flex items-center gap-2">
          <span>Choose Visual Theme & Stock Background</span>
          <span className="text-[11px] px-2 py-0.5 rounded-full bg-sky-400/20 text-sky-300 font-semibold">
            5 Motion Templates
          </span>
        </label>
        <span className="text-xs text-slate-400">
          Pre-bundled 9:16 vertical motion backgrounds
        </span>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3">
        {templates.map((template) => {
          const isSelected = template.id === selectedTemplateId;

          return (
            <div
              key={template.id}
              onClick={() => onSelectTemplate(template)}
              className={`relative p-3 rounded-2xl border-2 transition-all cursor-pointer select-none flex flex-col items-center text-center group ${
                isSelected
                  ? 'bg-gradient-to-b from-sky-500/20 to-slate-900 border-sky-400 shadow-lg shadow-sky-500/10 scale-[1.02]'
                  : 'bg-slate-900/70 border-slate-700/80 hover:border-slate-500 hover:bg-slate-850'
              }`}
            >
              {isSelected && (
                <div className="absolute top-2 right-2 w-5 h-5 rounded-full bg-sky-400 text-slate-950 flex items-center justify-center shadow">
                  <Check className="w-3.5 h-3.5 stroke-[3]" />
                </div>
              )}

              <div
                className="w-12 h-12 rounded-xl flex items-center justify-center text-2xl mb-2 group-hover:scale-110 transition shadow-inner"
                style={{ backgroundColor: `${template.accent_color}25`, border: `1px solid ${template.accent_color}60` }}
              >
                {template.emoji}
              </div>

              <h4 className="font-bold text-slate-100 text-xs">{template.name}</h4>
              <p className="text-[10px] text-slate-400 line-clamp-2 mt-1 leading-tight">
                {template.description}
              </p>

              <div className="mt-2 flex items-center gap-1 text-[9px] text-slate-300 bg-slate-800 px-2 py-0.5 rounded border border-slate-700 font-mono">
                <Film className="w-2.5 h-2.5 text-sky-400" />
                <span>{template.bg_video}</span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
