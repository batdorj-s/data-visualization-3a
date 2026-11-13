// Usage: node build_pptx.js <report_data.json> <out.pptx>
const fs = require("fs");
const path = require("path");
process.env.NODE_PATH = path.join(__dirname, "node_modules");
require("module").Module._initPaths();
const pptxgen = require("pptxgenjs");

const SKILL = process.env.PPTX_SKILL_DIR ||
  path.join(process.env.HOME, "Library/Application Support/Claude/local-agent-mode-sessions/skills-plugin/55f7d4be-b3a4-43c4-843f-980ee7d8dba5/71db1d2d-0b1f-42a9-b0fc-6a1494826452/skills/pptx");

const [, , dataPath, outPath] = process.argv;
const data = JSON.parse(fs.readFileSync(dataPath, "utf8"));
const ROOT = path.resolve(path.dirname(dataPath), "..");

const THEME = {
  name: "MBA Court",
  headFontFace: "Cambria",
  bodyFontFace: "Calibri",
  colors: {
    dk1: "1F2430", lt1: "FFFFFF", dk2: "2B2F3A", lt2: "F2F3F5",
    accent1: "E07A1F", accent2: "0072B2", accent3: "D55E00", accent4: "009E73", accent5: "9E9E9E", accent6: "56B4E9",
    hlink: "0072B2", folHlink: "6B6B6B",
  },
};

const pres = new pptxgen();
pres.layout = "LAYOUT_16x9"; // 10 x 5.625 in
pres.title = "MBA лигийн гүйцэтгэлийн шинжилгээ";
pres.theme = { headFontFace: THEME.headFontFace, bodyFontFace: THEME.bodyFontFace };
const C = pres.SchemeColor;
const FOOTER = { text: "MBA лигийн шинжилгээ · F.ITC341", options: { x: 0.5, y: 5.25, w: 6, h: 0.25, fontSize: 9, color: C.text2 } };

pres.defineSlideMaster({
  title: "DARK_TITLE",
  background: { color: C.text1 },
  objects: [
    { placeholder: { options: { name: "title", type: "title", x: 0.6, y: 1.6, w: 8.8, h: 1.4, fontSize: 40, bold: true,
      color: C.background1, valign: "bottom", align: "left" }, text: "" } },
    { placeholder: { options: { name: "body", type: "body", x: 0.6, y: 3.15, w: 8.8, h: 1.2, fontSize: 18,
      color: C.accent1, valign: "top" }, text: "" } },
  ],
});
pres.defineSlideMaster({
  title: "IMAGE_RIGHT_TEXT",
  background: { color: C.background1 },
  objects: [
    { placeholder: { options: { name: "title", type: "title", x: 0.5, y: 0.25, w: 9.0, h: 0.85, fontSize: 26, bold: true,
      color: C.text1, valign: "middle", align: "left" }, text: "" } },
    { placeholder: { options: { name: "body", type: "body", x: 6.95, y: 1.35, w: 2.55, h: 3.7, fontSize: 14,
      color: C.text1, valign: "top" }, text: "" } },
    { text: FOOTER },
  ],
  slideNumber: { x: 9.0, y: 5.22, w: 0.5, h: 0.3, fontSize: 9, color: C.text2 },
});
pres.defineSlideMaster({
  title: "STATS",
  background: { color: C.background2 },
  objects: [
    { placeholder: { options: { name: "title", type: "title", x: 0.5, y: 0.25, w: 9.0, h: 0.85, fontSize: 28, bold: true,
      color: C.text1, valign: "middle", align: "left" }, text: "" } },
    { placeholder: { options: { name: "body", type: "body", x: 0.5, y: 3.55, w: 9.0, h: 1.4, fontSize: 16,
      color: C.text1, valign: "top" }, text: "" } },
    { text: FOOTER },
  ],
  slideNumber: { x: 9.0, y: 5.22, w: 0.5, h: 0.3, fontSize: 9, color: C.text2 },
});

function pngSize(file) {
  const buf = fs.readFileSync(file);
  return { w: buf.readUInt32BE(16), h: buf.readUInt32BE(20) };
}

function fit(file, box) {
  const { w, h } = pngSize(file);
  const scale = Math.min(box.w / w, box.h / h);
  const W = w * scale, H = h * scale;
  return { x: box.x + (box.w - W) / 2, y: box.y + (box.h - H) / 2, w: W, h: H };
}

function bullets(items) {
  return items.map((t, i) => ({ text: t, options: { bullet: { indent: 14 }, breakLine: i < items.length - 1, paraSpaceAfter: 8 } }));
}

const SECTIONS = { 0: "Танилцуулга", 2: "Өгөгдөл", 3: "Дүрслэл", 8: "Машин суралцал", 10: "Шийдэл ба дүгнэлт" };
let section = null;

data.slides.forEach((s, i) => {
  if (SECTIONS[i]) {
    section = SECTIONS[i];
    pres.addSection({ title: section });
  }
  if (s.layout === "title" || s.layout === "closing") {
    const slide = pres.addSlide({ masterName: "DARK_TITLE", sectionTitle: section });
    slide.addText(s.title, { placeholder: "title" });
    if (s.layout === "title") {
      slide.addText(s.subtitle, { placeholder: "body" });
    } else {
      slide.addText(bullets(s.bullets), { placeholder: "body", fontSize: 18, color: C.background1 });
    }
    slide.addShape(pres.shapes.OVAL, { x: 8.45, y: 0.45, w: 0.9, h: 0.9, fill: { color: C.accent1 }, line: { color: C.accent1 },
      objectName: "ball" });
    slide.addNotes(s.notes);
  } else if (s.layout === "stats") {
    const slide = pres.addSlide({ masterName: "STATS", sectionTitle: section });
    slide.addText(s.title, { placeholder: "title" });
    s.stats.forEach(([value, label], k) => {
      const x = 0.5 + k * 3.05;
      slide.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y: 1.35, w: 2.85, h: 1.95, rectRadius: 0.12,
        fill: { color: C.background1 }, line: { color: C.background1 }, objectName: `stat-card-${k}`,
        shadow: { type: "outer", color: "000000", blur: 6, offset: 2, angle: 90, opacity: 0.12 } });
      slide.addText(value, { x, y: 1.5, w: 2.85, h: 1.0, fontSize: 48, bold: true, color: C.accent1, align: "center",
        fontFace: THEME.headFontFace, isTextBox: true, objectName: `stat-value-${k}` });
      slide.addText(label, { x, y: 2.5, w: 2.85, h: 0.5, fontSize: 14, color: C.text2, align: "center", isTextBox: true,
        objectName: `stat-label-${k}` });
    });
    slide.addText(bullets(s.bullets), { placeholder: "body" });
    slide.addNotes(s.notes);
  } else {
    const slide = pres.addSlide({ masterName: "IMAGE_RIGHT_TEXT", sectionTitle: section });
    slide.addText(s.title, { placeholder: "title" });
    const file = path.join(ROOT, s.image);
    slide.addImage({ path: file, ...fit(file, { x: 0.5, y: 1.25, w: 6.25, h: 3.9 }), altText: s.title,
      objectName: "figure" });
    slide.addText(bullets(s.bullets), { placeholder: "body" });
    slide.addNotes(s.notes);
  }
});

(async () => {
  await pres.writeFile({ fileName: outPath });
  const themeScript = path.join(SKILL, "scripts", "apply_theme.js");
  if (fs.existsSync(themeScript)) {
    const { applyTheme } = require(themeScript);
    await applyTheme(outPath, THEME);
  } else {
    console.warn("apply_theme.js олдсонгүй — theme-ийн өнгө Office-ийн стандарт хэвээр (PPTX_SKILL_DIR-ийг тохируулна уу)");
  }
  console.log("wrote", outPath);
})();
