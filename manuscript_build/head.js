const fs = require("fs");
const { Document, Packer, Paragraph, TextRun, HeadingLevel, AlignmentType, Table, TableRow, TableCell,
        WidthType, ShadingType, BorderStyle, ImageRun, PageBreak, Footer, PageNumber, LevelFormat } = require("docx");
const J = JSON.parse(fs.readFileSync("/tmp/proj/manuscript_numbers.json"));
const FIG = "/tmp/proj/figures/";
const F = (x, d = 1) => Number(x).toFixed(d);
const pct = (x, d = 1) => (100 * x).toFixed(d);

// ---------- inline markup: **bold**, *italic* ----------
function runs(text, base = {}) {
  const out = []; const re = /(\*\*[^*]+\*\*|\*[^*]+\*)/g; let last = 0, m;
  while ((m = re.exec(text))) {
    if (m.index > last) out.push(new TextRun({ text: text.slice(last, m.index), ...base }));
    const t = m[0];
    if (t.startsWith("**")) out.push(new TextRun({ text: t.slice(2, -2), bold: true, ...base }));
    else out.push(new TextRun({ text: t.slice(1, -1), italics: true, ...base }));
    last = m.index + t.length;
  }
  if (last < text.length) out.push(new TextRun({ text: text.slice(last), ...base }));
  return out;
}
const P = (t, o = {}) => new Paragraph({ children: runs(t), spacing: { after: 120, line: 360 }, alignment: AlignmentType.JUSTIFIED, ...o });
const H1 = (t) => new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun(t)], spacing: { before: 240, after: 120 } });
const H2 = (t) => new Paragraph({ heading: HeadingLevel.HEADING_2, children: [new TextRun(t)], spacing: { before: 180, after: 100 } });
const B = (t) => new Paragraph({ numbering: { reference: "bul", level: 0 }, children: runs(t), spacing: { after: 60, line: 320 } });
const CAP = (t) => new Paragraph({ children: runs(t, { size: 20 }), spacing: { after: 200 }, alignment: AlignmentType.JUSTIFIED });
function IMG(file, w, h) {
  return new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 120, after: 60 },
    children: [new ImageRun({ type: "png", data: fs.readFileSync(FIG + file), transformation: { width: w, height: h } })] });
}
const border = { style: BorderStyle.SINGLE, size: 4, color: "999999" };
const borders = { top: border, bottom: border, left: border, right: border };
function TABLE(head, rows, widths) {
  const total = widths.reduce((a, b) => a + b, 0);
  const cell = (t, i, hdr) => new TableCell({ borders, width: { size: widths[i], type: WidthType.DXA },
    shading: hdr ? { fill: "E7ECF3", type: ShadingType.CLEAR } : undefined, margins: { top: 40, bottom: 40, left: 70, right: 70 },
    children: [new Paragraph({ children: runs(String(t), { size: 18, bold: !!hdr }), alignment: i === 0 ? AlignmentType.LEFT : AlignmentType.CENTER })] });
  return new Table({ width: { size: total, type: WidthType.DXA }, columnWidths: widths,
    rows: [new TableRow({ tableHeader: true, children: head.map((h, i) => cell(h, i, true)) }),
           ...rows.map(r => new TableRow({ children: r.map((c, i) => cell(c, i, false)) }))] });
}
// ---------- numbers ----------
const rq1 = (setup, target, spec) => J.rq1.find(r => r.setup === setup && r.target === target && r.spec === spec);
const cov = (target, method, level) => J.cov.find(r => r.target === target && r.method === method && r.level === level);
const n3 = (method, level, approach) => J.rq3.find(r => r.method === method && r.level === level && r.approach === approach);
const pfmt = p => (p === 0 ? "< 0.0001" : (p < 0.001 ? p.toFixed(4) : p.toFixed(3)));
const b10 = r => `${F(1000 * r.beta, 2)} [${F(1000 * r.ci_lo, 2)}, ${F(1000 * r.ci_hi, 2)}]`;
const L = rq1("main", "load", "A"), N = rq1("main", "net", "A"), S = rq1("main", "solar", "A"), PL = rq1("placebo", "load", "A");

