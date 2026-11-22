// Builds the 8-page IEEE-format conference paper (A4, two columns) from experiment results.
//   node docs/paper/build_paper.js      (NODE_PATH may point at a folder that has `docx`)
const fs = require("fs");
const path = require("path");
const {
  Document, Packer, Paragraph, TextRun, ImageRun, Table, TableRow, TableCell, Tab,
  AlignmentType, WidthType, BorderStyle, SectionType, LevelFormat, VerticalAlign, HighlightColor,
  TabStopType, Math: OMath, MathRun, MathFraction, MathSum, MathSuperScript, MathSubScript,
  MathSubSuperScript, MathRoundBrackets,
} = require("docx");

const ROOT = path.resolve(__dirname, "..", "..");
const R = JSON.parse(fs.readFileSync(path.join(ROOT, "ml/reports/improved/improved_results.json")));
const FIG = path.join(__dirname, "figures");
const X = JSON.parse(fs.readFileSync(path.join(FIG, "extra_results.json")));
const SHAP_TOP = JSON.parse(fs.readFileSync(path.join(FIG, "shap_top_features.json")));
const AV = JSON.parse(fs.readFileSync(path.join(FIG, "assistant_verification.json")));
const META = JSON.parse(fs.readFileSync(path.join(ROOT, "ml/models/lead_conversion_metadata.json")));
const OUT = path.join(__dirname, process.env.PAPER_OUT || "Decision_Intel_IEEE_Paper.docx");

// ------------------------------------------------------------------ numbers
const [FULL, LF] = R.lead;
const [S_BASE, S_CW, S_SM, S_EARLY] = R.student;
const get = (s, m) => s.rows.find((r) => r.model === m);
const best = (s, k) => s.rows.reduce((a, b) => (b.test[k] > a.test[k] ? b : a));
const f4 = (v) => v.toFixed(4);
const f3 = (v) => v.toFixed(3);
const f3s = (v) => v.toFixed(3).replace(/^0/, "");
const pc = (v, d = 1) => (100 * v).toFixed(d) + "%";
const LONG = {
  "Logistic Regression": "Logistic Regression", "Random Forest": "Random Forest",
  XGBoost: "XGBoost", LightGBM: "LightGBM", CatBoost: "CatBoost",
  "Stacking (RF+XGB+LGBM+Cat)": "the stacking ensemble",
  "XGBoost (Optuna-tuned)": "the tuned XGBoost", "LightGBM (Optuna-tuned)": "the tuned LightGBM",
};
const SHORT = {
  "Logistic Regression": "LR", "Random Forest": "RF", XGBoost: "XGBoost", LightGBM: "LightGBM",
  CatBoost: "CatBoost", "Stacking (RF+XGB+LGBM+Cat)": "Stacking",
  "XGBoost (Optuna-tuned)": "XGBoost-T", "LightGBM (Optuna-tuned)": "LightGBM-T",
};
const xF = get(FULL, "XGBoost"), xL = get(LF, "XGBoost");
const bF = best(FULL, "roc_auc"), bL = best(LF, "roc_auc"), bLf1 = best(LF, "f1");
const lrL = get(LF, "Logistic Regression");
const boostL = LF.rows.filter((r) => !["Logistic Regression", "Random Forest"].includes(r.model));
const spreadL = Math.max(...boostL.map((r) => r.test.roc_auc)) - Math.min(...boostL.map((r) => r.test.roc_auc));
const cvStdL = LF.rows.filter((r) => r.cv).map((r) => r.cv.roc_auc.std);
const meanStdL = cvStdL.reduce((a, b) => a + b, 0) / cvStdL.length;
const sB = best(S_BASE, "f1"), sC = best(S_CW, "f1"), sS = best(S_SM, "f1"), sE = best(S_EARLY, "f1");
const sBest = [sC, sS].reduce((a, b) => (b.test.f1 > a.test.f1 ? b : a));
const sBestName = sBest === sC ? "class weighting" : "SMOTE";
const ENR = R.student_classes.indexOf("Enrolled");
const shapTop = SHAP_TOP.slice(0, 4).map((t) => t[0]);
const TK = X.topk_leakage_free;
const CM = X.confusion_leakage_free;
const SEG = X.segments;
const BUD = X.budget.scenarios;
const eqS = BUD["Equal split"], lp40 = BUD["LP optimum (cap 40%)"], lp100 = BUD["LP optimum (cap 100%)"];
const effSorted = Object.entries(X.budget.efficiency).sort((a, b) => b[1] - a[1]);
const cpaGain = (eqS.cpa - lp40.cpa) / eqS.cpa;

// ------------------------------------------------------------------ references (cited in order of first use)
const REFS = {
  siemens: "G. Siemens and P. Long, “Penetrating the fog: Analytics in learning and education,” EDUCAUSE Review, vol. 46, no. 5, pp. 30–40, 2011.",
  duncan: "B. A. Duncan and C. P. Elkan, “Probabilistic modeling of a sales funnel to prioritize leads,” in Proc. 21st ACM SIGKDD Int. Conf. Knowledge Discovery and Data Mining, 2015, pp. 1751–1758.",
  kaufman: "S. Kaufman, S. Rosset, C. Perlich, and O. Stitelman, “Leakage in data mining: Formulation, detection, and avoidance,” ACM Trans. Knowledge Discovery from Data, vol. 6, no. 4, pp. 1–21, 2012.",
  rf: "L. Breiman, “Random forests,” Machine Learning, vol. 45, no. 1, pp. 5–32, 2001, doi: 10.1023/A:1010933404324.",
  friedman: "J. H. Friedman, “Greedy function approximation: A gradient boosting machine,” Annals of Statistics, vol. 29, no. 5, pp. 1189–1232, 2001.",
  xgb: "T. Chen and C. Guestrin, “XGBoost: A scalable tree boosting system,” in Proc. 22nd ACM SIGKDD Int. Conf. Knowledge Discovery and Data Mining, 2016, pp. 785–794, doi: 10.1145/2939672.2939785.",
  lgbm: "G. Ke, Q. Meng, T. Finley, T. Wang, W. Chen, W. Ma, Q. Ye, and T.-Y. Liu, “LightGBM: A highly efficient gradient boosting decision tree,” in Advances in Neural Information Processing Systems 30, 2017, pp. 3146–3154.",
  cat: "L. Prokhorenkova, G. Gusev, A. Vorobev, A. V. Dorogush, and A. Gulin, “CatBoost: Unbiased boosting with categorical features,” in Advances in Neural Information Processing Systems 31, 2018.",
  stack: "D. H. Wolpert, “Stacked generalization,” Neural Networks, vol. 5, no. 2, pp. 241–259, 1992.",
  optuna: "T. Akiba, S. Sano, T. Yanase, T. Ohta, and M. Koyama, “Optuna: A next-generation hyperparameter optimization framework,” in Proc. 25th ACM SIGKDD Int. Conf. Knowledge Discovery and Data Mining, 2019, pp. 2623–2631.",
  kohavi: "R. Kohavi, “A study of cross-validation and bootstrap for accuracy estimation and model selection,” in Proc. 14th Int. Joint Conf. Artificial Intelligence (IJCAI), 1995, pp. 1137–1145.",
  shap: "S. M. Lundberg and S.-I. Lee, “A unified approach to interpreting model predictions,” in Advances in Neural Information Processing Systems 30, 2017, pp. 4765–4774.",
  treeshap: "S. M. Lundberg, G. Erion, H. Chen, A. DeGrave, J. M. Prutkin, B. Nair, R. Katz, J. Himmelfarb, N. Bansal, and S.-I. Lee, “From local explanations to global understanding with explainable AI for trees,” Nature Machine Intelligence, vol. 2, no. 1, pp. 56–67, 2020.",
  rudin: "C. Rudin, “Stop explaining black box machine learning models for high stakes decisions and use interpretable models instead,” Nature Machine Intelligence, vol. 1, no. 5, pp. 206–215, 2019.",
  hegarcia: "H. He and E. A. Garcia, “Learning from imbalanced data,” IEEE Trans. Knowledge and Data Engineering, vol. 21, no. 9, pp. 1263–1284, 2009.",
  smote: "N. V. Chawla, K. W. Bowyer, L. O. Hall, and W. P. Kegelmeyer, “SMOTE: Synthetic minority over-sampling technique,” J. Artificial Intelligence Research, vol. 16, pp. 321–357, 2002.",
  fawcett: "T. Fawcett, “An introduction to ROC analysis,” Pattern Recognition Letters, vol. 27, no. 8, pp. 861–874, 2006.",
  niculescu: "A. Niculescu-Mizil and R. Caruana, “Predicting good probabilities with supervised learning,” in Proc. 22nd Int. Conf. Machine Learning (ICML), 2005, pp. 625–632.",
  kmeans: "J. MacQueen, “Some methods for classification and analysis of multivariate observations,” in Proc. 5th Berkeley Symp. Mathematical Statistics and Probability, vol. 1, 1967, pp. 281–297.",
  rousseeuw: "P. J. Rousseeuw, “Silhouettes: A graphical aid to the interpretation and validation of cluster analysis,” J. Computational and Applied Mathematics, vol. 20, pp. 53–65, 1987.",
  realinho: "V. Realinho, J. Machado, L. Baptista, and M. V. Martins, “Predicting student dropout and academic success,” Data, vol. 7, no. 11, Art. no. 146, 2022, doi: 10.3390/data7110146.",
  leads: "ashydv, “Leads dataset,” Kaggle. [Online]. Available: https://www.kaggle.com/datasets/ashydv/leads-dataset (accessed Nov. 22, 2026).",
  ji: "Z. Ji, N. Lee, R. Frieske, T. Yu, D. Su, Y. Xu, E. Ishii, Y. J. Bang, A. Madotto, and P. Fung, “Survey of hallucination in natural language generation,” ACM Computing Surveys, vol. 55, no. 12, Art. no. 248, pp. 1–38, 2023.",
  lewis: "P. Lewis, E. Perez, A. Piktus, F. Petroni, V. Karpukhin, N. Goyal, H. Küttler, M. Lewis, W.-t. Yih, T. Rocktäschel, S. Riedel, and D. Kiela, “Retrieval-augmented generation for knowledge-intensive NLP tasks,” in Advances in Neural Information Processing Systems 33, 2020, pp. 9459–9474.",
  sklearn: "F. Pedregosa et al., “Scikit-learn: Machine learning in Python,” J. Machine Learning Research, vol. 12, pp. 2825–2830, 2011.",
};
const order = [];
const cite = (...keys) => "[" + keys.map((k) => {
  if (!REFS[k]) throw new Error("unknown ref " + k);
  if (!order.includes(k)) order.push(k);
  return order.indexOf(k) + 1;
}).join("], [") + "]";

// ------------------------------------------------------------------ formatting helpers
const FONT = "Times New Roman";
const ROMAN = ["I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X", "XI", "XII", "XIII", "XIV", "XV", "XVI", "XVII", "XVIII", "XIX", "XX"];
let figNo = 0, tabNo = 0, eqNo = 0, secNo = 0, subNo = 0;

function runs(text, size = 20, extra = {}) {
  return text.split(/(\*\*[^*]+\*\*|\*[^*]+\*)/).filter(Boolean).map((t) => {
    if (t.startsWith("**")) return new TextRun({ text: t.slice(2, -2), bold: true, font: FONT, size, ...extra });
    if (t.startsWith("*")) return new TextRun({ text: t.slice(1, -1), italics: true, font: FONT, size, ...extra });
    return new TextRun({ text: t, font: FONT, size, ...extra });
  });
}
const P = (text, o = {}) => new Paragraph({
  alignment: AlignmentType.JUSTIFIED, indent: o.noIndent ? undefined : { firstLine: 202 },
  spacing: { after: 0, line: 240 }, children: runs(text, 20),
});
const H1 = (text) => { secNo++; subNo = 0; return new Paragraph({
  alignment: AlignmentType.CENTER, keepNext: true, spacing: { before: 120, after: 60 },
  children: [new TextRun({ text: `${ROMAN[secNo - 1]}. ${text}`, font: FONT, size: 24, smallCaps: true, bold: true })],
}); };
const H2 = (text) => { subNo++; return new Paragraph({
  keepNext: true, spacing: { before: 80, after: 20 },
  children: [new TextRun({ text: `${String.fromCharCode(64 + subNo)}. ${text}`, font: FONT, size: 24, italics: true })],
}); };
const bullet = (text) => new Paragraph({
  numbering: { reference: "bul", level: 0 }, alignment: AlignmentType.JUSTIFIED,
  spacing: { after: 0 }, children: runs(text),
});

// equations: math centred in the column, number right-aligned
const m = (t) => new MathRun(t);
const frac = (n, d) => new MathFraction({ numerator: n, denominator: d });
const sum = (sub, sup, body) => new MathSum({ children: body, subScript: sub, superScript: sup });
const sp = (b, s) => new MathSuperScript({ children: b, superScript: s });
const sb = (b, s) => new MathSubScript({ children: b, subScript: s });
const sbsp = (b, s, u) => new MathSubSuperScript({ children: b, subScript: s, superScript: u });
const br = (c) => new MathRoundBrackets({ children: c });
function EQ(parts) {
  eqNo++;
  return new Paragraph({
    spacing: { before: 60, after: 60 },
    tabStops: [{ type: TabStopType.CENTER, position: 2510 }, { type: TabStopType.RIGHT, position: 5021 }],
    children: [new TextRun({ children: [new Tab()] }), new OMath({ children: parts }),
      new TextRun({ children: [new Tab(), `(${eqNo})`], font: FONT, size: 20 })],
  });
}

function pngSize(file) {
  const b = fs.readFileSync(file);
  return { w: b.readUInt32BE(16), h: b.readUInt32BE(20), data: b };
}
function figure(file, caption, widthPx = 322) {
  figNo++;
  const { w, h, data } = pngSize(path.join(FIG, file));
  return [
    new Paragraph({ alignment: AlignmentType.CENTER, keepNext: true, spacing: { before: 40 },
      children: [new ImageRun({ type: "png", data, transformation: { width: widthPx, height: Math.round(widthPx * h / w) },
        altText: { title: `Fig. ${figNo}`, description: caption, name: file } })] }),
    new Paragraph({ alignment: AlignmentType.JUSTIFIED, spacing: { before: 20, after: 60 },
      children: runs(`Fig. ${figNo}.  ${caption}`, 16) }),
  ];
}
const thin = { style: BorderStyle.SINGLE, size: 4, color: "000000" };
const borders = { top: thin, bottom: thin, left: thin, right: thin };
function table(caption, header, rows, widths, boldCells = new Set()) {
  tabNo++;
  const total = widths.reduce((a, b) => a + b, 0);
  const cell = (t, w, bold, center) => new TableCell({
    borders, width: { size: w, type: WidthType.DXA }, verticalAlign: VerticalAlign.CENTER,
    margins: { top: 15, bottom: 15, left: 40, right: 40 },
    children: [new Paragraph({ alignment: center ? AlignmentType.CENTER : AlignmentType.LEFT, keepNext: true, keepLines: true,
      children: [new TextRun({ text: t, font: FONT, size: 15, bold })] })],
  });
  return [
    new Paragraph({ alignment: AlignmentType.CENTER, keepNext: true, spacing: { before: 60 },
      children: [new TextRun({ text: `TABLE ${ROMAN[tabNo - 1]}`, font: FONT, size: 16, smallCaps: true })] }),
    new Paragraph({ alignment: AlignmentType.CENTER, keepNext: true, spacing: { after: 50 },
      children: [new TextRun({ text: caption, font: FONT, size: 16, smallCaps: true })] }),
    new Table({
      width: { size: total, type: WidthType.DXA }, columnWidths: widths, alignment: AlignmentType.CENTER,
      rows: [
        new TableRow({ tableHeader: true, children: header.map((h, i) => cell(h, widths[i], true, i > 0)) }),
        ...rows.map((r, ri) => new TableRow({ cantSplit: true,
          children: r.map((t, i) => cell(t, widths[i], boldCells.has(`${ri},${i}`), i > 0)) })),
      ],
    }),
    new Paragraph({ spacing: { after: 0, line: 120 }, children: [] }),
  ];
}
function metricTable(caption, suite) {
  const keys = ["accuracy", "balanced_accuracy", "precision", "recall", "f1", "roc_auc"];
  const bold = new Set();
  keys.forEach((k, j) => {
    const mx = Math.max(...suite.rows.map((r) => r.test[k]));
    suite.rows.forEach((r, i) => { if (r.test[k] === mx) bold.add(`${i},${j + 1}`); });
  });
  return table(caption, ["Model", "Acc.", "Bal. Acc.", "Prec.", "Rec.", "F1", "AUC"],
    suite.rows.map((r) => [SHORT[r.model], ...keys.map((k) => f4(r.test[k]))]),
    [1157, 644, 644, 644, 644, 644, 644], bold);
}

const pc2 = (v) => (100 * v).toFixed(2) + "%";
const metricSentence = (t) => `**${pc2(t.accuracy)} accuracy**, **${pc2(t.balanced_accuracy)} balanced accuracy**, **${pc2(t.precision)} precision**, **${pc2(t.recall)} recall**, **${pc2(t.f1)} F1-score** and **${f4(t.roc_auc)} ROC-AUC**`;
const accRange = (suite) => `${pc2(Math.min(...suite.rows.map((r) => r.test.accuracy)))} to ${pc2(Math.max(...suite.rows.map((r) => r.test.accuracy)))}`;
// ------------------------------------------------------------------ content
const body = [];
const add = (...xs) => xs.flat().forEach((x) => body.push(x));

add(new Paragraph({ alignment: AlignmentType.JUSTIFIED, spacing: { after: 80 }, children: [
  new TextRun({ text: "ABSTRACT—", bold: true, font: FONT, size: 20 }),
  ...runs(`Admission offices collect thousands of enquiries a year, and only a fraction of them become enrolled students. Deciding whom to call first, and where to spend the next campaign budget, is still largely guesswork. We built Decision-Intel, a web platform (SvelteKit and FastAPI) that scores each enquiry, explains the score with SHAP, groups leads into engagement segments, and compares budget allocations with a capped linear program. On the 9,240-lead *Leads X Education* dataset we benchmark eight classifiers, including LightGBM, CatBoost, Optuna-tuned boosters and a stacking ensemble, under stratified 5-fold cross-validation and a held-out test set. A leakage audit changes the picture. Seven columns are filled in by sales staff after contact; with them, XGBoost reaches a ROC-AUC of ${f4(xF.test.roc_auc)}, and without them ${f4(xL.test.roc_auc)}. About ${pc(X.ablation[1].gain / X.ablation[5].gain, 0)} of this gap comes from a single column, *Tags*, some of whose values effectively record the outcome. On the leakage-free features ${LONG[bL.model]} gives the best ROC-AUC (${f4(bL.test.roc_auc)}), and the top 10% of ranked leads convert at ${pc(TK[0].precision)}, ${TK[0].lift.toFixed(1)} times the base rate. With a 40% per-channel cap, the budget optimiser lowers projected cost per acquisition by ${pc(cpaGain)} relative to an equal split. A grounded Admission Assistant chatbot explains each stored score and its SHAP factors in plain language; in our checks it reproduced 25 of 25 stored predictions exactly and invented no fees, deadlines or admission chances. The platform supports staff judgment; it does not make admission decisions.`, 20),
] }));
add(new Paragraph({ alignment: AlignmentType.JUSTIFIED, spacing: { after: 120 }, children: [
  new TextRun({ text: "Index Terms—", italics: true, font: FONT, size: 20 }),
  ...runs("lead conversion prediction, student recruitment, gradient boosting, explainable AI, SHAP, data leakage, budget allocation, grounded chatbot, decision-support systems", 20),
] }));

// I. INTRODUCTION
add(H1("Introduction"));
add(P(`Private colleges in India, like most universities elsewhere, now recruit students the way companies sell products. Prospective students arrive through search ads, social media, education portals, chat widgets on the college website, and word of mouth. Each enquiry is a lead, and a counsellor has to decide whether to call it today, next week, or not at all. Institutions have used analytics to support such decisions for more than a decade ${cite("siemens")}, yet in many admission offices the call list is still sorted by arrival time.`));
add(P(`Predicting which leads will convert is a well-studied task in sales ${cite("duncan")}. Two problems keep these models from being trusted in an admission office. The first is opacity: a counsellor who sees a score of 0.82 wants to know why. The second is less visible. Many lead datasets contain fields that the sales team fills in during follow-up, such as a call outcome or a quality grade. A model trained on those fields looks excellent offline and then fails on fresh enquiries, which do not have them yet. This is target leakage ${cite("kaufman")}, and we found that it accounts for a large share of the accuracy usually reported on the dataset we use.`));
add(P("This paper describes **Decision-Intel**, the platform we built to address both problems, and the experiments behind it. Our contributions are:"));
add(bullet("a working web platform (SvelteKit, FastAPI, SQLite) that brings lead scoring, per-lead SHAP explanations, K-Means engagement segments, channel analytics and budget scenarios into one authenticated workflow;"));
add(bullet("a benchmark of eight classifiers, from Logistic Regression to a four-model stacking ensemble, with Optuna tuning, stratified 5-fold cross-validation and a held-out test set;"));
add(bullet("a leakage audit that separates post-contact columns from enquiry-time information and measures how much they inflate reported performance;"));
add(bullet("a capacity analysis showing what precision counsellors can expect when they can only call the top 10–40% of leads, together with a calibration check;"));
add(bullet("a capped linear program for channel budget allocation, and an auxiliary student-outcome experiment on class imbalance;"));
add(bullet("a grounded Admission Assistant chatbot that explains stored scores and SHAP factors in plain language without inventing facts, with role-based access."));
add(P("Section II reviews related work. Section III defines the problem. Section IV describes the platform and the methods. Section V presents the results and discusses them, Section VI concludes, and Section VII lists future enhancements."));

// II. LITERATURE SURVEY
add(H1("Literature Survey"));
add(P(`*Lead scoring and recruitment analytics.* Siemens and Long argued early on that data could guide decisions across the student life cycle, including recruitment ${cite("siemens")}. In sales, Duncan and Elkan modelled the funnel as a sequence of probabilistic stages and used it to rank leads ${cite("duncan")}. Studies of lead scoring usually report one random split and say little about whether each input exists at the moment a lead is scored.`));
add(P(`*Tree ensembles for tabular data.* Random Forest averages many decorrelated trees ${cite("rf")}. Gradient boosting instead fits trees one after another to the errors left by the previous ones ${cite("friedman")}. XGBoost added regularisation and a fast sparse-aware implementation ${cite("xgb")}. LightGBM grows trees leaf-wise using histogram-based splits ${cite("lgbm")}, and CatBoost uses ordered boosting with native handling of categorical inputs ${cite("cat")}. Stacked generalisation combines several learners through a second-level model trained on their out-of-fold predictions ${cite("stack")}.`));
add(P(`*Tuning and validation.* Optuna searches hyperparameters with a Tree-structured Parzen Estimator and prunes poor trials ${cite("optuna")}. Kohavi compared ways of estimating accuracy and recommended stratified ten-fold cross-validation for model selection ${cite("kohavi")}. We use stratified five-fold cross-validation, which keeps training time practical, together with an untouched test set for the final numbers.`));
add(P(`*Explanations.* SHAP attributes a prediction to its inputs using Shapley values from game theory ${cite("shap")}, and TreeSHAP computes them exactly and quickly for tree models ${cite("treeshap")}. Rudin cautions that post-hoc explanations of black boxes can mislead in high-stakes settings ${cite("rudin")}. For this reason we present SHAP values as descriptions of the model, not as causes of conversion.`));
add(P(`*Leakage, imbalance and probability quality.* Kaufman et al. define leakage as the use of information at training time that will not exist at prediction time, and give practical ways to detect it ${cite("kaufman")}. He and Garcia survey learning from imbalanced data ${cite("hegarcia")}. SMOTE, one of the methods they cover, creates synthetic minority samples ${cite("smote")}. ROC analysis summarises ranking quality ${cite("fawcett")}. Niculescu-Mizil and Caruana showed that boosted trees can produce poorly calibrated probabilities ${cite("niculescu")}, which matters when staff read a score as a chance of enrolment.`));
add(P(`*Segmentation and budgeting.* K-Means ${cite("kmeans")} is a standard way to group customers, and the silhouette coefficient measures how well separated the groups are ${cite("rousseeuw")}. Channel budgeting is often treated as an optimisation over historical return on spend. Simple linear formulations are transparent but ignore diminishing returns.`));
add(P(`*Conversational assistants.* Large language models write fluent text but can state things that no source supports, a problem known as hallucination ${cite("ji")}. Retrieval-augmented generation reduces it by conditioning the model on retrieved documents ${cite("lewis")}. Our assistant takes a stricter route: answers are assembled from database records and a curated knowledge base, and an optional language model may only rephrase them.`));
add(P("*Research gap.* We found no published system that combines a leakage-aware lead-conversion benchmark, per-lead explanations, capacity-oriented evaluation, budget planning and a grounded assistant in a deployable tool for admission teams. Most prior work stops at a model accuracy figure. Our aim was to build something a counsellor could use on a Monday morning, and to report honestly how well it can be expected to work."));

// III. PROBLEM STATEMENT
add(H1("Problem Statement"));
add(P("Let a historical dataset contain leads, each described by a feature vector *x* and a label *y* ∈ {0, 1} that records whether the lead converted. We split the features into two groups: *x*ᴀ, which is known when the enquiry arrives (source, origin, website activity, stated occupation), and *x*ₚ, which is recorded later by sales staff. The task is to learn a scoring function that uses only the first group:", { noIndent: false }));
add(EQ([m("s"), br([m("x")]), m(" = P"), br([m("y=1 | "), sb([m("x")], [m("A")])])]));
add(P("Counsellors then work through leads in decreasing order of *s*, as far as their capacity allows. Alongside the score, the system has to explain each prediction, group leads into understandable segments, summarise channel performance, and propose a budget split across channels for a total budget *B*."));
add(P("We set five requirements. **Availability**: no input may depend on events after the first contact. **Explainability**: every score comes with the features that drove it. **Reliability**: results are checked with cross-validation as well as a held-out set. **Usefulness**: performance is reported at realistic calling capacities, not only as a global metric. **Oversight**: the tool advises staff, who keep the final decision, and it never judges academic merit or eligibility. The first requirement alone rules out seven of the dataset's columns, as the leakage audit in Section IV explains."));

// IV. PROPOSED METHODOLOGY
add(H1("Proposed Methodology"));
add(H2("System Architecture"));
add(P("Fig. 1 shows the platform. The SvelteKit frontend gives counsellors and managers dashboards for scores, explanations, segments, channel summaries and budget scenarios. A FastAPI backend handles login, validation and the REST services, and stores leads, predictions, datasets and saved scenarios in SQLite. Model artifacts live outside the database and are versioned separately. The deployed model is trained by a script that uses the same preprocessing module as the API, so served scores come from exactly the pipeline whose held-out ROC-AUC is " + META.held_out_metrics.roc_auc.toFixed(4) + ". The Admission Assistant sits beside the model services and reads their stored outputs."));
add(figure("fig1_architecture.png", "Architecture of the Decision-Intel platform.", 300));
add(H2("Implementation"));
add(P("The backend is organised into nine FastAPI routers, summarised in Table I. Access is role-based: students use a small enquiry portal, admission and marketing managers work with leads and analytics, and an administrator manages users and system settings. Passwords are stored as salted PBKDF2-SHA256 hashes with 600,000 iterations, and session tokens are random values kept on the server only as SHA-256 hashes. Every request body passes through Pydantic validation; a custom budget split, for example, is rejected if it does not add up to the total or names an unknown channel. Lead files are uploaded as a CSV, or a ZIP holding one CSV, of at most 5 MB, and the schema is checked before any record is stored."));
add(table("Backend Services and Access Roles",
  ["Router", "Access", "Main functions"],
  [["/auth", "All users", "Register, login, logout, profile"],
   ["/student", "Student", "Submit and track enquiries"],
   ["/leads", "Managers", "Lead records, scores, SHAP factors"],
   ["/datasets", "Signed-in", "Upload and validate lead files"],
   ["/workspace", "Signed-in", "Overview, channels, segments, simulate"],
   ["/analytics", "Signed-in", "Channel summaries"],
   ["/budget", "Signed-in", "Saved budget simulations"],
   ["/admin", "Administrator", "Users, datasets, configuration"],
   ["/assistant", "Signed-in", "Chatbot answers and chat history"]],
  [1150, 1150, 2721]));
add(P("Each lead's detail page shows its stored conversion probability, score band, engagement segment and four strongest SHAP factors, so staff see the reasons next to the score. The backend is covered by 38 automated unit and HTTP integration tests, which run against a temporary database so that testing can never change the application's data."));

add(H2("Datasets"));
add(P(`The lead experiments use the *Leads X Education* dataset ${cite("leads")}. It holds 9,240 enquiries for an online education company, and 38.54% of them converted. After removing the identifiers *Prospect ID* and *Lead Number* and five columns that hold the same value in every row (${META.excluded_constant_columns.join(", ")}), 5 numeric and 24 categorical inputs remain. For the auxiliary experiment we use the student dropout and academic-success data of Realinho et al. ${cite("realinho")}: 4,424 students, 36 features, and three outcomes (Dropout, Enrolled, Graduate). Table II summarises both datasets.`));
add(table("Datasets and Feature Sets",
  ["Dataset / set", "Rows", "Features", "Target"],
  [["Leads – full", "9,240", "5 num + 24 cat", "Converted (38.5%)"],
   ["Leads – leakage-free", "9,240", "3 num + 19 cat", "Converted (38.5%)"],
   ["Student outcome", "4,424", "19 num + 17 cat", "3 classes"]],
  [1700, 800, 1260, 1261]));

add(H2("Leakage Audit"));
add(P(`We went through the data dictionary column by column and asked one question: would this value exist on the day the enquiry arrives? Seven columns failed. *Tags*, *Lead Quality* and *Lead Profile* are set by the sales team after talking to the lead. The four *Asymmetrique* activity and profile indices and scores are internal grades assigned later. *Tags* is the clearest case, as Table III shows: some tag values are effectively the outcome written in words. Following Kaufman et al. ${cite("kaufman")}, we therefore evaluate two feature sets. The **full** set matches the model the platform originally served; the platform now serves the leakage-free set. The **leakage-free** set drops all seven columns.`));
add(table("Selected Tags Values and Their Conversion Rates",
  ["Tag value", "Leads", "Converted"],
  [["Will revert after reading the email", "2,072", "96.9%"], ["Closed by Horizzon", "358", "99.4%"],
   ["Lost to EINS", "175", "97.7%"], ["Ringing", "1,203", "2.8%"], ["Already a student", "465", "0.6%"]],
  [2821, 1100, 1100]));

add(H2("Preprocessing"));
add(P(`In the benchmark, numeric inputs are filled with the median and standardised, and categorical inputs are filled with the most frequent value and one-hot encoded; categories seen fewer than five times are merged and categories that appear only at prediction time are ignored. The deployed pipeline uses the same imputation and one-hot encoding without standardisation, which tree models do not need. Every transformation sits inside a scikit-learn pipeline ${cite("sklearn")} and is fitted on training folds only, so no information from test data reaches preprocessing.`));

add(H2("Classification Models"));
add(P("Logistic Regression (LR) is the linear baseline. It maps a weighted sum of the inputs to a probability:"));
add(EQ([m("p"), br([m("x")]), m(" = "), frac([m("1")], [m("1+"), sp([m("e")], [m("−("), sb([m("β")], [m("0")]), m("+"), sp([m("β")], [m("T")]), m("x)")])])]));
add(P(`Random Forest (RF) averages 300 trees ${cite("rf")}. The three boosting libraries build an additive model of *M* trees *h*ₘ, each scaled by a learning rate η ${cite("friedman")}:`));
add(EQ([sb([m("F")], [m("M")]), br([m("x")]), m(" = "), sum([m("m=1")], [m("M")], [m("η "), sb([m("h")], [m("m")]), br([m("x")])])]));
add(P(`XGBoost fits each tree by minimising a regularised objective ${cite("xgb")}, where ℓ is the log-loss, *T* the number of leaves and *w* the leaf weights:`));
add(EQ([m("ℒ = "), sum([m("i")], [], [m("ℓ"), br([sb([m("y")], [m("i")]), m(", "), sb([m("ŷ")], [m("i")])])]), m(" + "), sum([m("m")], [], [m("γ"), sb([m("T")], [m("m")]), m(" + "), frac([m("λ")], [m("2")]), sp([m("‖"), sb([m("w")], [m("m")]), m("‖")], [m("2")])])]));
add(P(`Our default XGBoost uses 400 trees, depth 4 and learning rate 0.08. LightGBM ${cite("lgbm")} uses 400 trees with 31 leaves, and CatBoost ${cite("cat")} uses 300 iterations of depth 6. The stacking ensemble ${cite("stack")} feeds the out-of-fold probabilities *p*ₖ of RF, XGBoost, LightGBM and CatBoost into a logistic meta-learner:`));
add(EQ([sb([m("p")], [m("stack")]), m(" = σ"), br([sb([m("α")], [m("0")]), m(" + "), sum([m("k=1")], [m("4")], [sb([m("α")], [m("k")]), sb([m("p")], [m("k")]), br([m("x")])])])]));

add(H2("Hyperparameter Optimisation"));
add(P(`XGBoost and LightGBM were also tuned with Optuna's TPE sampler ${cite("optuna")}. Each of the 20 trials was scored by 3-fold cross-validation inside the training split, maximising ROC-AUC for leads and macro F1 for students. Table IV lists the search space and the values chosen on the leakage-free lead data. We refer to the tuned models as XGBoost-T and LightGBM-T.`));
{
  const px = LF.tuned_params.XGBoost, pl = LF.tuned_params.LightGBM;
  const r2 = (v) => (typeof v === "number" && !Number.isInteger(v) ? v.toPrecision(3) : String(v));
  add(table("Optuna Search Space and Selected Values (Leakage-Free)",
    ["Hyperparameter", "Range", "XGBoost-T", "LightGBM-T"],
    [["n_estimators", "200–900", r2(px.n_estimators), r2(pl.n_estimators)],
     ["max_depth / num_leaves", "3–8 / 15–127", r2(px.max_depth), r2(pl.num_leaves)],
     ["learning_rate (log)", "0.01–0.2", r2(px.learning_rate), r2(pl.learning_rate)],
     ["subsample", "0.6–1.0", r2(px.subsample), r2(pl.subsample)],
     ["colsample_bytree", "0.5–1.0", r2(px.colsample_bytree), r2(pl.colsample_bytree)],
     ["min_child_weight / samples", "1–10 / 5–60", r2(px.min_child_weight), r2(pl.min_child_samples)],
     ["reg_lambda (log)", "0.001–10", r2(px.reg_lambda), r2(pl.reg_lambda)]],
    [1621, 1200, 1100, 1100]));
}

add(H2("Evaluation Protocol and Metrics"));
add(P(`The data are split 80:20 with stratification and seed 42. On the training part we run stratified 5-fold cross-validation and report the mean and standard deviation ${cite("kohavi")}. Final numbers come from a single pass over the untouched 20% test set. We report accuracy, balanced accuracy, precision *P*, recall *R*, F1 and ROC-AUC ${cite("fawcett")}, with a 0.5 threshold for the threshold-based metrics:`));
add(EQ([m("P="), frac([m("TP")], [m("TP+FP")]), m(",  R="), frac([m("TP")], [m("TP+FN")]), m(",  F1="), frac([m("2PR")], [m("P+R")])]));
add(P(`For students we use macro averages over the three classes. Because counsellors read scores as chances, we also measure calibration with the Brier score ${cite("niculescu")}, where *N* is the number of test leads:`));
add(EQ([m("BS = "), frac([m("1")], [m("N")]), sum([m("i=1")], [m("N")], [sp([br([sb([m("p")], [m("i")]), m(" − "), sb([m("y")], [m("i")])])], [m("2")])])]));
add(P("Finally, to reflect limited calling capacity, we report precision among the top *k*% of leads ranked by score, and the lift over the base conversion rate π:"));
add(EQ([m("Lift@k = "), frac([m("Precision@k")], [m("π")])]));
add(P(`For the imbalanced student data we compare three options: no balancing, balanced class weights, and SMOTE ${cite("smote")} applied after encoding within each training fold ${cite("hegarcia")}.`));

add(H2("Explanations, Segments and Budget Scenarios"));
add(P(`TreeSHAP ${cite("treeshap")} splits each prediction into a base value φ₀ and one contribution φⱼ per feature ${cite("shap")}:`));
add(EQ([m("f"), br([m("x")]), m(" = "), sb([m("φ")], [m("0")]), m(" + "), sum([m("j=1")], [m("d")], [sb([m("φ")], [m("j")])])]));
add(P("The dashboard shows the largest contributions for each lead. For global importance we add up the one-hot parts of each source feature. Segments come from K-Means with *k* = 4 on the standardised engagement features, which minimises the within-cluster spread:"));
add(EQ([sb([m("min")], [m("C,μ")]), m(" "), sum([m("k=1")], [m("4")], [sum([m("x∈"), sb([m("C")], [m("k")])], [], [sp([m("‖x − "), sb([m("μ")], [m("k")]), m("‖")], [m("2")])])])]));
add(P(`Visits, time on site and page views are log-transformed before clustering, because a few leads with more than a hundred visits would otherwise form a cluster of their own. Clusters are then named Low Engagement, Casual Browsers, Engaged Prospects and High Intent in order of their mean engagement. For budgets, the platform computes each channel's efficiency *e*ᴄ as historical conversions divided by spend. It then offers equal, efficiency-weighted, custom and optimised splits. The optimised split solves a linear program with a cap α on any single channel's share:`));
add(EQ([sb([m("max")], [m("b")]), m(" "), sum([m("c")], [], [sb([m("e")], [m("c")]), sb([m("b")], [m("c")])]), m("  s.t.  "), sum([m("c")], [], [sb([m("b")], [m("c")])]), m("=B,  0≤"), sb([m("b")], [m("c")]), m("≤αB")]));
add(P("Projected cost per acquisition is *B* divided by the projected conversions. Efficiency is assumed constant, so this is a planning aid, not a forecast."));
add(H2("Admission Assistant"));
add(P("The assistant is a chat panel on every signed-in page, served by a ninth router (/assistant) that reuses the existing sessions and roles. A rule-based router handles each message in a fixed order: greetings, questions about a lead (managers only), a student's own enquiries, prediction statistics, safety rules for admission-chance and fee or eligibility questions, and finally retrieval over 18 curated topics that describe the platform. Retrieval compares the question's content words with each topic's example questions using word and character n-gram TF-IDF, so that misspellings still match:"));
add(EQ([m("score = 0.55 "), sb([m("s")], [m("word")]), m(" + 0.45 "), sb([m("s")], [m("char")])]));
add(P(`A topic is answered when its score reaches 0.40 and it shares at least one content word with the question; between 0.24 and 0.40 the assistant asks “Did you mean…?”, and below that it says it does not know. Lead answers reuse the stored prediction endpoint, or the live prediction endpoint when nothing is stored, and never compute a score of their own. Because SHAP factors refer to one-hot categories, a factor such as City = Mumbai on a lead with no city is rendered as “City is not Mumbai”. Fees, eligibility rules and deadlines are not stored, so the assistant says so instead of answering. Lead-level answers follow the same rule as the leads router: only admission and marketing managers receive them. An optional language model (Claude) may rewrite a grounded answer for fluency, but a rewrite is discarded if it contains any number that is not in the grounded facts ${cite("ji")}.`));
add(P(`The assistant also has practical safeguards. A message may contain at most 1,000 characters, and each user may send at most 20 messages per minute. Conversations are stored in their own table, separate from leads, enquiries and predictions; the last 200 messages of each user are kept, and users can clear their history at any time. When the chat opens, the assistant greets the user by name and suggests starter questions that match the user's role, so a student sees questions about enquiries and programmes while a manager sees questions about scores and SHAP factors.`));

// V. RESULTS AND DISCUSSION
add(H1("Results and Discussion"));
add(H2("Experimental Setup"));
add(P("All experiments ran on a laptop with an Intel Core i3-1115G4 (4 logical cores) under Windows 11. We used Python 3.14, scikit-learn 1.9.1, XGBoost 3.4.1, LightGBM 4.7.0, CatBoost 1.2.10, Optuna 5.0.0, imbalanced-learn 0.14.2 and SHAP 0.52.0. The full benchmark, including all tuning, finished in 28 minutes."));
add(P(`Every leakage-free model fitted and cross-validated in ${Math.min(...Object.values(X.model_seconds))}–${Math.max(...Object.values(X.model_seconds))} s, and the full Optuna search for XGBoost took ${X.tuning_seconds.XGBoost} s, so retraining on new enquiry data is cheap enough to run every week.`));

add(H2("Lead Conversion with All Features"));
add(P(`Table V gives the held-out results when every column is used. All eight models clear the majority-class baseline (accuracy 61.47%) by a wide margin, with accuracy ranging from ${accRange(FULL)}. On the held-out test set (20% of the data, 1,848 leads), the default XGBoost achieves ${metricSentence(xF.test)}. ${SHORT[bF.model]} reaches the best ROC-AUC, ${f4(bF.test.roc_auc)}. The default XGBoost reaches ${f4(xF.test.roc_auc)}, close to the 0.9792 recorded for the model the platform originally served. The models are very close to one another, and a reviewer could fairly ask whether any of them is learning something a counsellor does not already know.`));
add(metricTable("Lead Conversion – All Features (Held-Out)", FULL));

add(H2("Effect of Removing Post-Contact Columns"));
add(P(`Table VI repeats the benchmark without the seven post-contact columns. Accuracy drops to between ${accRange(LF)}, every model loses between 0.09 and 0.10 ROC-AUC, and F1 falls from around 0.91 to between ${f3(Math.min(...LF.rows.map((r) => r.test.f1)))} and ${f3(Math.max(...LF.rows.map((r) => r.test.f1)))}. Fig. 2 shows that the drop is uniform across model families, which points to the data rather than any single algorithm. These lower figures are the honest estimate of what the platform can do with a fresh enquiry.`));
add(metricTable("Lead Conversion – Leakage-Free Features (Held-Out)", LF));
add(P(`Without leakage, ${LONG[bL.model]} has the best ROC-AUC (${f4(bL.test.roc_auc)}) and ${LONG[bLf1.model]} the best F1 (${f4(bLf1.test.f1)}). Logistic Regression trails at ${f4(lrL.test.roc_auc)}, so the non-linear models do add something. The boosted variants, however, lie within ${f3s(spreadL)} of each other, about the size of one cross-validation standard deviation (${f3s(meanStdL)}). Tuning and stacking help a little; they do not transform the result. The model the platform now serves, a leakage-free XGBoost trained with the production settings, achieves ${metricSentence(META.held_out_metrics)} on its own held-out split, in line with Table VI.`));
add(figure("fig2_lead_auc.png", "Held-out ROC-AUC, all vs. leakage-free features (T = tuned).", 230));

add(P(`Which column is responsible? Table VII adds each post-contact group back to the leakage-free set, one at a time, and retrains the default XGBoost. *Tags* alone lifts ROC-AUC by ${X.ablation[1].gain.toFixed(3)}, about ${pc(X.ablation[1].gain / X.ablation[5].gain, 0)} of the full gap. The Asymmetrique scores, Lead Quality and Lead Profile each add between 0.016 and 0.027. Any institution reusing this dataset should, at a minimum, drop *Tags*.`));
add(table("Leakage Ablation: Adding Post-Contact Columns Back (XGBoost)",
  ["Feature set", "ROC-AUC", "Gain"],
  X.ablation.map((a) => [a.added, f4(a.auc), a.gain ? "+" + a.gain.toFixed(4) : "–"]),
  [2621, 1200, 1200]));
add(H2("Cross-Validation Stability"));
add(P("Table VIII compares the 5-fold estimates with the held-out numbers. On the leakage-free features cross-validation is 0.016 to 0.023 ROC-AUC higher than the held-out score, and the fold-to-fold spread is small, so the test split is somewhat harder than average but not unusual. The stacking ensemble is left out here because it already uses internal cross-validation, and nesting it again would have multiplied the run time several times over on our hardware."));
{
  const rows = LF.rows.filter((r) => r.cv).map((r) => {
    const f = get(FULL, r.model);
    return [SHORT[r.model], `${f3s(f.cv.roc_auc.mean)} ± ${f3s(f.cv.roc_auc.std)}`,
      `${f3s(r.cv.roc_auc.mean)} ± ${f3s(r.cv.roc_auc.std)}`, `${f3s(r.cv.f1.mean)} ± ${f3s(r.cv.f1.std)}`];
  });
  add(table("Stratified 5-Fold Cross-Validation on the Training Split",
    ["Model", "AUC – all", "AUC – leak-free", "F1 – leak-free"], rows, [1157, 1288, 1288, 1288]));
}

add(H2("Ranking, Calibration and Calling Capacity"));
add(P(`Fig. 3 shows ROC curves for the leakage-free models. The curves are almost on top of each other, and all of them rise steeply at the left. That steep start is what an admission office cares about, because it means the first leads on the list are very likely to convert. Table IX makes this concrete for the tuned XGBoost. If counsellors can only reach the top 10% of the test leads (${TK[0].n} people), ${pc(TK[0].precision)} of them convert, against a base rate of ${pc(X.test_base_rate)}. At 30% capacity the list still converts at ${pc(TK[2].precision)} and captures ${pc(TK[2].recall)} of all conversions.`));
add(P(`Because only 38.5% of leads convert, we also looked at precision–recall curves (Fig. 4), which are more sensitive to errors on the positive class. The tuned boosters reach an average precision of ${f3(X.average_precision["LGBM-T"])} (LightGBM-T) and ${f3(X.average_precision["XGB-T"])} (XGBoost-T), against ${f3(X.average_precision.LR)} for Logistic Regression. Precision stays above 0.8 until roughly two-thirds of converters have been found.`));
add(figure("fig3_lead_roc_leakage_free.png", "ROC curves on the held-out test set, leakage-free features.", 235));
add(figure("fig_pr.png", "Precision–recall curves on the held-out test set, leakage-free features. The dashed line is the base rate.", 240));
add(table("Precision and Lift at Limited Calling Capacity (XGBoost-T, Leakage-Free)",
  ["Top k%", "Leads called", "Precision", "Recall", "Lift"],
  TK.map((t) => [`${Math.round(t.k * 100)}%`, String(t.n), pc(t.precision), pc(t.recall), t.lift.toFixed(2)]),
  [1000, 1000, 1007, 1007, 1007]));
add(P(`Calibration is good in both settings (Fig. 5). The Brier score is ${f3(X.brier.leakage_free)} without leakage and ${f3(X.brier.full)} with it. In the leakage-free case the predicted probabilities follow the observed rates closely across the whole range, so a score of 0.7 can be read as roughly a 70% chance. At the 0.5 threshold the confusion matrix shows that ${CM[1][1]} of ${CM[1][0] + CM[1][1]} converters are found, while ${CM[0][1]} non-converters are flagged by mistake.`));
add(P(`The 0.5 threshold is a convention, not a requirement. Fig. 6 sweeps the threshold for the same model. F1 peaks at ${X.threshold.best_threshold.toFixed(2)} (F1 ${f3(X.threshold.best_f1)}, recall ${pc(X.threshold.r_at_best)}), slightly below 0.5. A team that would rather not miss a likely student can lower the threshold further and accept more wasted calls. The platform therefore exposes the threshold as a setting instead of fixing it in code.`));
add(figure("fig_calibration.png", "Calibration curves (ten quantile bins) for tuned XGBoost with and without post-contact columns.", 235));

add(figure("fig_threshold.png", "Precision, recall and F1 of the leakage-free XGBoost-T as the decision threshold varies.", 210));
add(H2("Error Analysis"));
add(P(`Errors are not spread evenly. Table X breaks down held-out performance of XGBoost-T by lead origin. For leads created through the lead add form, ${pc(X.error_by_origin.find((r) => r.origin === "Lead Add Form").conv)} convert, and the model simply predicts that all of them will; it never misses a converter but flags every non-converter in this group as well. API leads, mostly from the chat widget, are the opposite case: the model misses ${pc(X.error_by_origin.find((r) => r.origin === "API").fnr)} of the converters among them. Counsellors should therefore treat a low score on an API lead with some caution, and a dedicated model or extra features for chat enquiries would be worth testing.`));
add(table("Held-Out Errors by Lead Origin (XGBoost-T, Threshold 0.5)",
  ["Lead origin", "Leads", "Conv.", "Acc.", "FNR", "FPR"],
  X.error_by_origin.map((r) => [r.origin, String(r.n), pc(r.conv), pc(r.acc), pc(r.fnr), pc(r.fpr)]),
  [1621, 680, 680, 680, 680, 680]));
add(H2("Model Explanations"));
add(P(`Fig. 7 ranks features by mean absolute SHAP value for the leakage-free XGBoost-T. ${shapTop[0]} dominates, followed by ${shapTop[1]}, ${shapTop[2]} and ${shapTop[3]}. Time on the website and lead origin are signals a counsellor would recognise and that exist at enquiry time. The two activity fields need care. They record the most recent interaction, which can include something the college did, such as sending an SMS. In deployment, the platform should use the value as of the scoring moment and not a later update. The rest of the top ten are ${SHAP_TOP.slice(4).map((t) => t[0]).join(", ").replace("What is your current occupation", "current occupation")}. Taken together, the model relies mostly on how much a lead engaged with the website and how the lead first arrived, not on who the lead is.`));
add(figure("fig4_shap_leakage_free.png", "Mean absolute SHAP values for the ten most important source features (XGBoost-T, leakage-free).", 290));
add(P(`Fig. 8 looks more closely at the strongest feature. Below about ${Math.round(X.shap_time_crossover_s)} seconds, roughly ten minutes, time on the website lowers the predicted chance of conversion; above it, the contribution turns positive, rises steeply up to about 850 seconds and then levels off. In practice, a lead who has spent more than ten minutes on the website deserves an early call even when other signals are weak.`));
add(figure("fig_shap_time.png", "SHAP dependence of the predicted log-odds on total time spent on the website (XGBoost-T).", 245));

add(H2("Channels and Engagement Segments"));
add(P("Fig. 9 shows conversion by lead source for sources with at least 50 leads. Referrals (Reference, 91.8%) and the Welingak website (98.6%) convert far above the 38.5% average, while Olark Chat and Facebook sit near 24–26%. Google and direct traffic bring in the most leads; Google (40.0%) converts close to the average, while direct traffic (32.2%) is somewhat below it. A manager reading this chart might consider investing more in referral programmes, and the model scores make the same point at the level of individual leads."));
add(figure("fig_lead_source.png", "Conversion rate by lead source (sources with at least 50 leads). The dashed line marks the overall rate.", 250));
add(P(`Table XI profiles the four segments, named in order of engagement. The silhouette coefficient is ${f3(X.silhouette)} ${cite("rousseeuw")}, which indicates reasonably distinct groups. The High Intent segment has a median of ${SEG[3].visits} visits and ${SEG[3].pages} pages per visit, yet it converts at ${pc(SEG[3].conv)}, about the same as the ${pc(SEG[0].conv)} of the Low Engagement segment, whose members have almost no recorded website visits. The source mix explains this. Among leads with no recorded visits, 69% came through the chat widget, but 29% were entered through the lead add form, mostly referrals, and those converted at 92%. Engagement on its own is therefore a weak guide to conversion, which is why the platform shows each segment next to the model score instead of in place of it.`));
add(table("K-Means Engagement Segments (All 9,240 Leads)",
  ["Segment", "Leads", "Med. visits", "Med. pages", "Med. time (s)", "Conv."],
  SEG.map((x) => [x.name, x.leads.toLocaleString("en-US"), String(x.visits), String(x.pages), String(Math.round(x.time)), pc(x.conv)]),
  [1321, 700, 750, 750, 800, 700]));

add(H2("Budget Allocation Example"));
add(P(`To show the optimiser at work we used a separate multi-channel marketing file of ${X.budget.campaigns} campaigns as demonstration input; it does not come from an admission office. Instagram had the highest historical efficiency (${effSorted[0][1].toFixed(4)} conversions per unit spend) and Twitter the lowest (${effSorted[effSorted.length - 1][1].toFixed(4)}). Table XII compares four ways of splitting a budget of 100,000. With a 40% cap the linear program raises projected conversions from ${Math.round(eqS.conversions).toLocaleString("en-US")} to ${Math.round(lp40.conversions).toLocaleString("en-US")} and lowers cost per acquisition by ${pc(cpaGain)}. Without a cap it puts the entire budget into Instagram. That is the correct answer under a constant-efficiency assumption, but no sensible manager would accept it. The cap exists for this reason, and it also shows why a model of diminishing returns is the next step.`));
add(table("Projected Outcomes for a Budget of 100,000",
  ["Strategy", "Conversions", "CPA", "Channels used"],
  Object.entries(BUD).map(([k, v]) => [k, Math.round(v.conversions).toLocaleString("en-US"), v.cpa.toFixed(2),
    String(Object.values(v.alloc).filter((a) => a > 0).length)]),
  [1821, 1100, 1000, 1100]));

add(H2("Auxiliary Student-Outcome Experiment"));
add(P(`The student data ask a different question, namely which enrolled students may drop out, but the class imbalance problem is shared. Table XIII lists the best model under each strategy. Without balancing, the minority Enrolled class reaches an F1 of only ${f3s(sB.test.f1_per_class[ENR])}. With ${sBestName}, macro F1 rises from ${f4(sB.test.f1)} to ${f4(sBest.test.f1)} and Enrolled F1 to ${f3s(sBest.test.f1_per_class[ENR])} (Fig. 10). The gain is modest but consistent. An early-warning model that uses only enrolment and first-semester data still reaches macro F1 ${f4(sE.test.f1)} and ROC-AUC ${f4(sE.test.roc_auc)}, which would let a college reach out one semester earlier. These figures are not comparable with the lead results.`));
add(table("Student Outcome – Best Model per Strategy (Held-Out)",
  ["Strategy", "Model", "Acc.", "Macro F1", "AUC", "F1 Enr."],
  [["None", sB], ["Class weights", sC], ["SMOTE", sS], ["Early (1st sem)", sE]].map(([n, r]) =>
    [n, SHORT[r.model], f4(r.test.accuracy), f4(r.test.f1), f4(r.test.roc_auc), f3s(r.test.f1_per_class[ENR])]),
  [1080, 860, 760, 800, 760, 761]));
add(H2("Admission Assistant Evaluation"));
add(P(`Table XIV lists every check we ran on the assistant with no language-model API key configured, so all answers came from the grounded engine. For 25 randomly chosen leads, the probability, band, segment and SHAP values in its answers were identical to the existing prediction endpoint, and the two leads without a stored prediction received the live model's score from the existing endpoint. Sixteen questions about fees, eligibility, deadlines and admission chances were answered without a single invented figure, and all ten lead-level requests from student and administrator accounts were refused. The routing figure comes from the labelled questions we used while tuning the thresholds, so it is not an independent test.`));
add(figure("fig5_student_f1.png", "Per-class F1 of the best student-outcome model under each imbalance strategy.", 280));

add(table("Admission Assistant Verification (No Language-Model Key)",
  ["Check", "Passed"],
  AV.rows.map((r) => [r.check, `${r.passed}/${r.total}`]),
  [4021, 1000]));
add(H2("Discussion"));
add(P(`The leakage audit changed how we read every other number in this paper. With the sales team's notes included, the problem looks almost solved. Without them, a strong model still ranks leads well (ROC-AUC near ${f3(bL.test.roc_auc)}), but it makes mistakes on roughly one lead in five. An institution that deploys the full-feature model would see its real-world accuracy fall short of the reported figure and might lose trust in the tool. We would rather report the lower number and stand by it.`));
add(P("We expect the capacity view to matter most to admission staff. A counsellor rarely asks for ROC-AUC. They ask whether the first fifty calls of the day will be worth making. At 10% capacity, more than nine of every ten calls reach a lead who will convert. The choice of algorithm matters much less than this. A single tuned booster is nearly as good as a four-model stack, and it is easier to serve and to explain."));
add(P("The assistant trades fluency for reliability. Every figure it states comes from the database or the model files, so its answers can be checked against the existing pages, exactly as our tests did. The cost is coverage: it handles 18 topics plus lead, enquiry and statistics questions, and anything else receives an honest “I don't know” with suggested questions rather than a guess. For an admission office we consider this the right default, because a confident wrong answer about fees or eligibility does more harm than no answer."));
add(H2("Limitations"));
add(P("All lead results come from one public dataset of one company, with random rather than time-ordered splits, so performance on later campaigns or other institutions is untested. The data's provenance and licence should be confirmed before any operational use. Attributes such as city, country and occupation may act as proxies for protected characteristics, and subgroup error rates were not measured. The budget optimiser assumes constant returns and was demonstrated on non-admission data. No user study has yet measured whether the explanations change counsellor decisions, and the assistant's optional language-model layer was tested only against a simulated API."));

add(P("There is also an ethical side to ranking people. A low score should never mean that an applicant receives less information or a slower reply to a direct question. We recommend that scores decide only the order of proactive outreach, that every lead remains reachable through normal channels, and that counsellors can override any score. The lead model predicts a marketing outcome. It says nothing about a student's ability or suitability, and the platform keeps it apart from the student-outcome experiment for that reason."));
// VI. CONCLUSION
add(H1("Conclusion"));
add(P(`Decision-Intel puts lead scoring, SHAP explanations, engagement segments, channel analytics, capped budget optimisation and a grounded chatbot into one platform for admission teams. Across eight models, gradient-boosted trees performed best. Removing seven post-contact columns lowered ROC-AUC from about ${f3(xF.test.roc_auc)} to ${f3(bL.test.roc_auc)}, and we consider the lower figure the realistic one; the platform now serves this leakage-free model. Even so, the top tenth of ranked leads converted at ${pc(TK[0].precision)}, and the predicted probabilities were well calibrated. In short, a carefully validated, explainable model can make a counsellor's day more productive, provided its numbers are reported without leakage. The Admission Assistant shows that the same scores can be explained to staff in plain language without inventing anything: in our checks it reproduced every stored prediction it was asked about and refused every request outside its role rules.`));

// VII. FUTURE ENHANCEMENTS
add(P(`*Data and code availability.* The lead data are public ${cite("leads")}. Every number in this paper is produced by scripts in the project repository: the benchmark (train_improved_models.py), the calibration, capacity, segmentation and budget analyses (extra_paper_analysis.py), the leakage ablation and threshold sweep (ablation_threshold.py), and the error and SHAP analyses (paper_page8_analysis.py); the paper itself is generated from their outputs.`));
add(H1("Future Enhancements"));
add(P("We have already switched the deployed scorer to the leakage-free pipeline; retrained on all leads with the production settings, it reaches a held-out ROC-AUC of " + META.held_out_metrics.roc_auc.toFixed(4) + ". Next, we plan to validate on time-ordered splits and on enquiry data from our own and partner institutions, and to set the calling threshold from each team's actual capacity. We also intend to audit errors across student subgroups, to replace the constant-efficiency budget model with response curves that capture diminishing returns, to add programme intake data to the assistant's knowledge base, to evaluate its language-model layer with real users, and to run a user study with admission counsellors."));

// REFERENCES
add(new Paragraph({ alignment: AlignmentType.CENTER, keepNext: true, spacing: { before: 160, after: 80 },
  children: [new TextRun({ text: "References", font: FONT, size: 24, smallCaps: true, bold: true })] }));
order.forEach((k, i) => {
  const children = [new TextRun({ text: `[${i + 1}]`, font: FONT, size: 16 }), new TextRun({ children: [new Tab()], font: FONT, size: 16 }),
    new TextRun({ text: REFS[k], font: FONT, size: 16 })];
  add(new Paragraph({ alignment: AlignmentType.JUSTIFIED, spacing: { after: 20 },
    indent: { left: 400, hanging: 400 }, tabStops: [{ type: TabStopType.LEFT, position: 400 }], children }));
});
const unused = Object.keys(REFS).filter((k) => !order.includes(k));
if (unused.length) throw new Error("uncited refs: " + unused.join(", "));

// ------------------------------------------------------------------ document
const authors = [["Prof. A. Suhana Nafais", "suhana.nafais@sonatech.ac.in"], ["Priyadarsini K J", "priyadarsini.25cap@sonatech.ac.in"], ["Sahana S", "sahana.25cap@sonatech.ac.in"]];
const NB = { style: BorderStyle.NONE, size: 0, color: "FFFFFF" };
const authorCell = ([name, email]) => new TableCell({
  width: { size: 3427, type: WidthType.DXA }, borders: { top: NB, bottom: NB, left: NB, right: NB },
  children: [
    new Paragraph({ alignment: AlignmentType.CENTER, children: [
      new TextRun({ text: name, font: FONT, size: 22 })] }),
    new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ text: "Department of Computer Applications", font: FONT, size: 18, italics: true })] }),
    new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ text: "Sona College of Technology", font: FONT, size: 18, italics: true })] }),
    new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ text: "Salem 636005, TN, India", font: FONT, size: 18 })] }),
    new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ text: email, font: FONT, size: 18 })] }),
  ],
});
const page = { size: { width: 11906, height: 16838 }, margin: { top: 1077, bottom: 1440, left: 812, right: 812 } };
const doc = new Document({
  creator: "Decision-Intel authors",
  title: "Decision-Intel: Explainable, Leakage-Aware Lead-Conversion Prediction and Budget Allocation for Admission Marketing",
  styles: { default: { document: { run: { font: FONT, size: 20 } } } },
  numbering: { config: [{ reference: "bul", levels: [{ level: 0, format: LevelFormat.BULLET, text: "•",
    alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 288, hanging: 216 } } } }] }] },
  sections: [
    { properties: { page }, children: [
      new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 200 }, children: [
        new TextRun({ text: "Decision-Intel: Explainable, Leakage-Aware Lead-Conversion Prediction and Budget Allocation for Admission Marketing", font: FONT, size: 30, bold: true })] }),
      new Table({ width: { size: 10281, type: WidthType.DXA }, columnWidths: [3427, 3427, 3427], alignment: AlignmentType.CENTER,
        borders: { top: NB, bottom: NB, left: NB, right: NB, insideHorizontal: NB, insideVertical: NB },
        rows: [new TableRow({ children: authors.map(authorCell) })] }),
      new Paragraph({ spacing: { after: 160 }, children: [] }),
    ] },
    { properties: { page, type: SectionType.CONTINUOUS, column: { count: 2, space: 239, equalWidth: true } }, children: body },
    { properties: { page, type: SectionType.CONTINUOUS }, children: [new Paragraph({ children: [] })] },
  ],
});
Packer.toBuffer(doc).then((buf) => {
  fs.writeFileSync(OUT, buf);
  console.log("wrote", OUT, "| refs:", order.length, "| figs:", figNo, "| tables:", tabNo, "| eqs:", eqNo);
});
