// --- components/TextEditTool.tsx ---

import React, { useState, useEffect, useCallback } from "react";
import { HexColorPicker } from "react-colorful";
import { PDFTextElement } from "../contexts/PDFEditContext";
import { useTranslation } from "react-i18next";
import debounce from 'lodash.debounce';

type TextEditToolProps = {
  editingElement: PDFTextElement;
  onUpdate: (data: Partial<PDFTextElement>) => void;
};

const MIN_FONT_SIZE = 1;
const MAX_FONT_SIZE = 72;
const MIN_LETTER_SPACING = -3;
const MAX_LETTER_SPACING = 8;

const FONT_OPTIONS = [
  { value: "Helvetica", label: "Helvetica" },
  { value: "Times-Roman", label: "Times" },
  { value: "Courier", label: "Courier" },
  { value: "NotoSansKR", label: "Noto Sans" },
];

const TextEditTool = ({ editingElement, onUpdate }: TextEditToolProps) => {
  const [text, setText] = useState("");
  const [fontSize, setFontSize] = useState(20);
  const [color, setColor] = useState("#222222");
  const [fontFamily, setFontFamily] = useState("Helvetica");
  const [fontBold, setFontBold] = useState(false);
  const [letterSpacing, setLetterSpacing] = useState(0);
  const [hasBackground, setHasBackground] = useState(false);
  const [backgroundColor, setBackgroundColor] = useState("#ffffff");
  const { t } = useTranslation("editor");

  const debouncedUpdate = useCallback(debounce((data: Partial<PDFTextElement>) => onUpdate(data), 300), [onUpdate]);
  const updateFontSize = (value: number) => {
    if (Number.isNaN(value)) {
      return;
    }

    setFontSize(Math.min(MAX_FONT_SIZE, Math.max(MIN_FONT_SIZE, value)));
  };
  const updateLetterSpacing = (value: number) => {
    if (Number.isNaN(value)) {
      return;
    }

    setLetterSpacing(Math.min(MAX_LETTER_SPACING, Math.max(MIN_LETTER_SPACING, value)));
  };

  useEffect(() => {
    if (editingElement) {
      setText(editingElement.text);
      setFontSize(editingElement.fontSize);
      setColor(editingElement.color);
      setFontFamily(editingElement.fontFamily || "Helvetica");
      setFontBold(editingElement.fontBold || false);
      setLetterSpacing(editingElement.letterSpacing || 0);
      setHasBackground(editingElement.hasBackground);
      setBackgroundColor(editingElement.backgroundColor);
    }
  }, [editingElement]);

  useEffect(() => {
    if (editingElement.text === text && editingElement.fontSize === fontSize && editingElement.color === color && (editingElement.fontFamily || "Helvetica") === fontFamily && (editingElement.fontBold || false) === fontBold && (editingElement.letterSpacing || 0) === letterSpacing && editingElement.hasBackground === hasBackground && editingElement.backgroundColor === backgroundColor) {
        return;
    }
    debouncedUpdate({ text, fontSize, color, fontFamily, fontBold, letterSpacing, hasBackground, backgroundColor });
    
    return () => {
        debouncedUpdate.cancel();
    }
  }, [text, fontSize, color, fontFamily, fontBold, letterSpacing, hasBackground, backgroundColor, debouncedUpdate, editingElement]);

  return (
    <div className="w-full flex flex-col h-full space-y-4">
      <div>
        <label className="panel-label">{t("text")}</label>
        <textarea
          placeholder={t("textPlaceholder")}
          value={text}
          onChange={e => setText(e.target.value)}
          className="w-full form-input resize-none"
          rows={3}
          autoFocus
        />
      </div>
      <div>
        <label className="panel-label">{t("fontSize")}: <strong>{fontSize}px</strong></label>
        <div className="flex items-center gap-3">
          <input
            type="range"
            min={MIN_FONT_SIZE}
            max={MAX_FONT_SIZE}
            value={fontSize}
            onChange={e => updateFontSize(Number(e.target.value))}
            className="w-full theme-transition"
          />
          <input
            type="number"
            min={MIN_FONT_SIZE}
            max={MAX_FONT_SIZE}
            value={fontSize}
            onChange={e => updateFontSize(Number(e.target.value))}
            className="form-input w-20"
          />
        </div>
      </div>
      <div>
        <label className="panel-label">{t("fontFamily", "Font")}</label>
        <select
          value={fontFamily}
          onChange={e => setFontFamily(e.target.value)}
          className="w-full form-input"
        >
          {FONT_OPTIONS.map((font) => (
            <option key={font.value} value={font.value}>{font.label}</option>
          ))}
        </select>
      </div>
      <div>
        <label className="flex items-center gap-2 text-text theme-transition">
          <input
            type="checkbox"
            checked={fontBold}
            onChange={e => setFontBold(e.target.checked)}
            className="theme-transition"
          />
          {t("fontBold", "Bold")}
        </label>
      </div>
      <div>
        <label className="panel-label">{t("letterSpacing", "Letter Spacing")}: <strong>{letterSpacing}px</strong></label>
        <div className="flex items-center gap-3">
          <input
            type="range"
            min={MIN_LETTER_SPACING}
            max={MAX_LETTER_SPACING}
            step={0.1}
            value={letterSpacing}
            onChange={e => updateLetterSpacing(Number(e.target.value))}
            className="w-full theme-transition"
          />
          <input
            type="number"
            min={MIN_LETTER_SPACING}
            max={MAX_LETTER_SPACING}
            step={0.1}
            value={letterSpacing}
            onChange={e => updateLetterSpacing(Number(e.target.value))}
            className="form-input w-20"
          />
        </div>
      </div>
      <div>
        <label className="panel-label">{t("fontColor")}: <strong>{color}</strong></label>
        <HexColorPicker color={color} onChange={setColor} style={{width: '100%', height: 120}}/>
      </div>
      <hr className="border-border my-4" />
      <div>
        <label className="flex items-center gap-2 text-text theme-transition">
          <input
            type="checkbox"
            checked={hasBackground}
            onChange={e => setHasBackground(e.target.checked)}
            className="theme-transition"
          />
          {t("background")}
        </label>
      </div>
      {hasBackground && (
        <div>
          <label className="panel-label">{t("backgroundColor")}: <strong>{backgroundColor}</strong></label>
          <HexColorPicker color={backgroundColor} onChange={setBackgroundColor} style={{width: '100%', height: 120}}/>
        </div>
      )}
    </div>
  );
};

export default TextEditTool;
