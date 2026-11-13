// Usage: node build_docx.js <report_data.json> <out.docx>
const fs = require("fs");
const path = require("path");
const {
  AlignmentType, BorderStyle, Document, Footer, HeadingLevel, ImageRun, LevelFormat, Packer, PageNumber,
  Paragraph, ShadingType, Table, TableCell, TableRow, TextRun, WidthType,
} = require("docx");

const [, , dataPath, outPath] = process.argv;
const data = JSON.parse(fs.readFileSync(dataPath, "utf8"));
const ROOT = path.resolve(path.dirname(dataPath), ".."); // report_data.json нь mba_analysis/report/ дотор
const FONT = "Arial";
const CONTENT_DXA = 11906 - 2 * 1134; // A4, 2 см захтай
const HEADER_FILL = "0072B2";

function para(text, opts = {}) {
  return new Paragraph({ spacing: { after: 120 }, ...opts, children: [new TextRun({ text, font: FONT, ...(opts.run || {}) })] });
}

function draft(text) {
  return new Paragraph({
    spacing: { before: 60, after: 160 },
    children: [
      new TextRun({ text: data.draft_label + " ", bold: true, highlight: "yellow", font: FONT }),
      new TextRun({ text, highlight: "yellow", font: FONT }),
    ],
  });
}

function caption(text) {
  return new Paragraph({ spacing: { before: 60, after: 200 }, alignment: AlignmentType.LEFT,
    children: [new TextRun({ text, italics: true, size: 18, color: "4D4D4D", font: FONT })] });
}

function figure(b) {
  const widthPx = Math.round((b.width_cm / 2.54) * 96);
  const heightPx = Math.round(widthPx * (b.height_px / b.width_px));
  return [
    new Paragraph({ keepNext: true, alignment: AlignmentType.CENTER, spacing: { before: 120 },
      children: [new ImageRun({ type: "png", data: fs.readFileSync(path.join(ROOT, b.path)),
        transformation: { width: widthPx, height: heightPx },
        altText: { title: b.caption, description: b.caption, name: path.basename(b.path) } })] }),
    caption(b.caption),
  ];
}

function columnWidths(b) {
  const weights = b.columns.map((c, i) => {
    const lens = [c.length, ...b.rows.map((r) => (r[i] || "").length)];
    return Math.max(Math.min(Math.max(...lens), 60), c.length + 3, 9) + 4;
  });
  const total = weights.reduce((a, x) => a + x, 0);
  const widths = weights.map((w) => Math.floor((w / total) * CONTENT_DXA));
  widths[widths.length - 1] += CONTENT_DXA - widths.reduce((a, x) => a + x, 0);
  return widths;
}

function cell(text, width, header) {
  return new TableCell({
    width: { size: width, type: WidthType.DXA },
    shading: header ? { type: ShadingType.CLEAR, fill: HEADER_FILL, color: "auto" } : undefined,
    margins: { top: 40, bottom: 40, left: 80, right: 80 },
    children: [new Paragraph({ children: [new TextRun({ text, size: 16, bold: header, color: header ? "FFFFFF" : "000000", font: FONT })] })],
  });
}

function table(b) {
  const widths = columnWidths(b);
  const border = { style: BorderStyle.SINGLE, size: 4, color: "BFBFBF" };
  return [
    caption(b.caption),
    new Table({
      width: { size: CONTENT_DXA, type: WidthType.DXA },
      columnWidths: widths,
      borders: { top: border, bottom: border, left: border, right: border, insideHorizontal: border, insideVertical: border },
      rows: [
        new TableRow({ tableHeader: true, children: b.columns.map((c, i) => cell(c, widths[i], true)) }),
        ...b.rows.map((r) => new TableRow({ children: r.map((v, i) => cell(v, widths[i], false)) })),
      ],
    }),
    new Paragraph({ spacing: { after: 120 }, children: [] }),
  ];
}

function bullets(b) {
  return b.items.map((t) => new Paragraph({ numbering: { reference: "bullets", level: 0 }, spacing: { after: 60 },
    children: [new TextRun({ text: t, font: FONT })] }));
}

const children = [
  new Paragraph({ heading: HeadingLevel.TITLE, children: [new TextRun({ text: "MBA лигийн гүйцэтгэлийн шинжилгээ", font: FONT })] }),
  para("F.ITC341 Өгөгдлийн дүрслэл · Бие даалт · Дата татсан огноо: 2026-11-12", { run: { color: "4D4D4D" } }),
  draft("Шар өнгөөр тодруулсан хэсгүүд нь тоон үр дүнд суурилсан ноорог юм. Даалгаврын шаардлагын дагуу эдгээрийг өөрийн үгээр дахин бичиж, тодруулгыг арилгана."),
];
for (const s of data.sections) {
  children.push(new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun({ text: s.title, font: FONT })] }));
  for (const b of s.blocks) {
    if (b.type === "para") children.push(para(b.text));
    else if (b.type === "draft") children.push(draft(b.text));
    else if (b.type === "figure") children.push(...figure(b));
    else if (b.type === "table") children.push(...table(b));
    else if (b.type === "bullets") children.push(...bullets(b));
    else if (b.type === "h2") children.push(new Paragraph({ heading: HeadingLevel.HEADING_2, children: [new TextRun({ text: b.text, font: FONT })] }));
  }
}

const doc = new Document({
  creator: "MBA analysis",
  title: "MBA лигийн гүйцэтгэлийн шинжилгээ",
  styles: {
    default: { document: { run: { font: FONT, size: 22 }, paragraph: { spacing: { line: 276 } } } },
    paragraphStyles: [
      { id: "Title", name: "Title", basedOn: "Normal", run: { font: FONT, size: 36, bold: true },
        paragraph: { spacing: { before: 0, after: 120 }, keepNext: true } },
      { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { font: FONT, size: 30, bold: true, color: "1F2430" },
        paragraph: { spacing: { before: 280, after: 120 }, keepNext: true, outlineLevel: 0 } },
      { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { font: FONT, size: 24, bold: true, color: "1F2430" },
        paragraph: { spacing: { before: 200, after: 80 }, keepNext: true, outlineLevel: 1 } },
    ],
  },
  numbering: { config: [{ reference: "bullets", levels: [{ level: 0, format: LevelFormat.BULLET, text: "•",
    alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 540, hanging: 270 } } } }] }] },
  sections: [{
    properties: { page: { margin: { top: 1134, bottom: 1134, left: 1134, right: 1134 } } },
    footers: { default: new Footer({ children: [new Paragraph({ alignment: AlignmentType.CENTER,
      children: [new TextRun({ children: [PageNumber.CURRENT], size: 18, font: FONT })] })] }) },
    children,
  }],
});

Packer.toBuffer(doc).then((buf) => { fs.writeFileSync(outPath, buf); console.log("wrote", outPath); });
