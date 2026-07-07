import React, { useState, useEffect, useCallback } from "react";
import { HexColorPicker } from "react-colorful";
import debounce from "lodash.debounce";
import { PDFReplaceElement } from "../contexts/PDFEditContext";
import { useTranslation } from "react-i18next";
import { usePDFEdit } from "../contexts/PDFEditContext";

type ReplaceTextToolProps = {
  editingElement: PDFReplaceElement;
  onUpdate: (data: Partial<PDFReplaceElement>) => void;
};

const FONT_OPTIONS = [
  { value: "Helvetica", label: "Helvetica" },
  { value: "Times-Roman", label: "Times" },
  { value: "Courier", label: "Courier" },
  { value: "NotoSansKR", label: "Noto Sans" },
];

const clamp = (value: number, min: number, max: number) => {
  if (Number.isNaN(value)) return min;
  return Math.min(max, Math.max(min, value));
};

const ReplaceTextTool = ({ editingElement, onUpdate }: ReplaceTextToolProps) => {
  const { t } = useTranslation("editor");
  const { state } = usePDFEdit();
  const [text, setText] = useState("");
  const [isDetecting, setIsDetecting] = useState(false);
  const [width, setWidth] = useState(120);
  const [height, setHeight] = useState(24);
  const [fontSize, setFontSize] = useState(12);
  const [color, setColor] = useState("#111111");
  const [fontFamily, setFontFamily] = useState("Helvetica");
  const [fontBold, setFontBold] = useState(false);
  const [align, setAlign] = useState<"left" | "center" | "right">("center");
  const [fillColor, setFillColor] = useState("#ffffff");
  const [padding, setPadding] = useState(1);
  const [yOffset, setYOffset] = useState(0);

  const debouncedUpdate = useCallback(debounce((data: Partial<PDFReplaceElement>) => onUpdate(data), 300), [onUpdate]);

  useEffect(() => {
    setText(editingElement.text);
    setWidth(editingElement.width);
    setHeight(editingElement.height);
    setFontSize(editingElement.fontSize);
    setColor(editingElement.color);
    setFontFamily(editingElement.fontFamily || "Helvetica");
    setFontBold(editingElement.fontBold || false);
    setAlign(editingElement.align || "center");
    setFillColor(editingElement.fillColor || "#ffffff");
    setPadding(editingElement.padding ?? 1);
    setYOffset(editingElement.yOffset || 0);
  }, [editingElement]);

  useEffect(() => {
    if (
      editingElement.text === text &&
      editingElement.width === width &&
      editingElement.height === height &&
      editingElement.fontSize === fontSize &&
      editingElement.color === color &&
      editingElement.fontFamily === fontFamily &&
      editingElement.fontBold === fontBold &&
      editingElement.align === align &&
      editingElement.fillColor === fillColor &&
      editingElement.padding === padding &&
      (editingElement.yOffset || 0) === yOffset
    ) {
      return;
    }

    debouncedUpdate({ text, width, height, fontSize, color, fontFamily, fontBold, align, fillColor, padding, yOffset });
    return () => debouncedUpdate.cancel();
  }, [text, width, height, fontSize, color, fontFamily, fontBold, align, fillColor, padding, yOffset, debouncedUpdate, editingElement]);

  const handleDetectStyle = async () => {
    if (!state.pdfFile) return;

    setIsDetecting(true);
    try {
      debouncedUpdate.cancel();
      const detected = await window.electron.pdf.detectTextStyle(state.pdfFile, {
        page: editingElement.page,
        x: editingElement.x,
        y: editingElement.y,
        width: editingElement.width,
        height: editingElement.height,
      });

      onUpdate({
        x: detected.x,
        y: detected.y,
        width: detected.width,
        height: detected.height,
        fontSize: Math.max(1, Math.round(detected.fontSize * 10) / 10),
        color: detected.color,
        fontFamily: detected.fontFamily,
        fontBold: detected.fontBold,
        align: detected.align || "center",
        yOffset: detected.yOffset || 0,
      });
    } catch (error) {
      console.error("Failed to detect text style:", error);
    } finally {
      setIsDetecting(false);
    }
  };

  return (
    <div className="w-full flex flex-col h-full space-y-4">
      <div>
        <label className="panel-label">{t("replacementText", "Replacement Text")}</label>
        <input
          value={text}
          onChange={e => setText(e.target.value)}
          className="w-full form-input"
          autoFocus
        />
      </div>
      <button
        type="button"
        onClick={handleDetectStyle}
        disabled={!state.pdfFile || isDetecting}
        className="w-full px-3 py-2 rounded-md bg-primary hover:bg-primary-hover text-white theme-transition disabled:opacity-50 disabled:cursor-not-allowed"
      >
        {isDetecting ? t("detectingStyle", "Detecting...") : t("detectStyle", "Detect Style")}
      </button>
      <div className="grid grid-cols-2 gap-3">
        <div>
          <label className="panel-label">{t("width")}</label>
          <input type="number" min={4} value={width} onChange={e => setWidth(clamp(Number(e.target.value), 4, 1000))} className="w-full form-input" />
        </div>
        <div>
          <label className="panel-label">{t("height")}</label>
          <input type="number" min={4} value={height} onChange={e => setHeight(clamp(Number(e.target.value), 4, 500))} className="w-full form-input" />
        </div>
      </div>
      <div>
        <label className="panel-label">{t("fontSize")}</label>
        <input type="number" min={1} max={72} value={fontSize} onChange={e => setFontSize(clamp(Number(e.target.value), 1, 72))} className="w-full form-input" />
      </div>
      <div>
        <label className="panel-label">{t("fontFamily", "Font")}</label>
        <select value={fontFamily} onChange={e => setFontFamily(e.target.value)} className="w-full form-input">
          {FONT_OPTIONS.map(font => <option key={font.value} value={font.value}>{font.label}</option>)}
        </select>
      </div>
      <div className="grid grid-cols-2 gap-3">
        <label className="flex items-center gap-2 text-text theme-transition">
          <input type="checkbox" checked={fontBold} onChange={e => setFontBold(e.target.checked)} className="theme-transition" />
          {t("fontBold", "Bold")}
        </label>
        <div>
          <label className="panel-label">{t("align", "Align")}</label>
          <select value={align} onChange={e => setAlign(e.target.value as "left" | "center" | "right")} className="w-full form-input">
            <option value="left">{t("alignLeft", "Left")}</option>
            <option value="center">{t("alignCenter", "Center")}</option>
            <option value="right">{t("alignRight", "Right")}</option>
          </select>
        </div>
      </div>
      <div>
        <label className="panel-label">{t("padding", "Padding")}</label>
        <input type="number" min={-10} max={20} step={0.5} value={padding} onChange={e => setPadding(clamp(Number(e.target.value), -10, 20))} className="w-full form-input" />
      </div>
      <div>
        <label className="panel-label">{t("yOffset", "Y Offset")}</label>
        <input type="number" min={-20} max={20} step={0.25} value={yOffset} onChange={e => setYOffset(clamp(Number(e.target.value), -20, 20))} className="w-full form-input" />
      </div>
      <div>
        <label className="panel-label">{t("fontColor")}: <strong>{color}</strong></label>
        <HexColorPicker color={color} onChange={setColor} style={{ width: "100%", height: 120 }} />
      </div>
      <div>
        <label className="panel-label">{t("fill", "Fill")}: <strong>{fillColor}</strong></label>
        <HexColorPicker color={fillColor} onChange={setFillColor} style={{ width: "100%", height: 120 }} />
      </div>
    </div>
  );
};

export default ReplaceTextTool;
