"""Дизайн-система: токены и CSS. Один акцент (синий), нейтральная графитовая шкала."""

CSS = """
<style>
:root{
  --bg:#F7F7F8; --surface:#FFFFFF; --line:#E4E6EA; --line-soft:#EEF0F2;
  --text:#1B1D21; --muted:#6A7079; --faint:#9AA0A8;
  --accent:#2B5DD6; --accent-soft:#EDF2FD;
  --ok:#1E7A4C; --ok-bg:#EEF7F1; --ok-line:#CFE6D8;
  --bad:#B3392F; --bad-bg:#FCF1F0; --bad-line:#F0CFCB;
  --r:10px; --r-lg:14px;
  --font:-apple-system,BlinkMacSystemFont,"SF Pro Text","Segoe UI",Inter,Roboto,"Helvetica Neue",Arial,sans-serif;
}
html,body,.stApp,[data-testid="stAppViewContainer"]{background:var(--bg)!important;font-family:var(--font)!important;color:var(--text)}
header[data-testid="stHeader"],#MainMenu,footer,[data-testid="stToolbar"],[data-testid="stDecoration"],[data-testid="stStatusWidget"]{display:none!important}
[data-testid="stMainBlockContainer"]{max-width:880px;padding:20px 24px 72px}
*{box-sizing:border-box}
.stApp,.stApp p,.stApp label,.stApp button,.stApp h1,.stApp h2,.stApp h3,.stApp li,.stApp dd,.stApp dt,.stApp small,.stApp input,[data-baseweb] *:not([data-testid="stIconMaterial"]){font-family:var(--font)!important}

/* Шапка */
.topbar{display:flex;align-items:center;justify-content:space-between;gap:12px;padding:6px 0 14px}
.brand{display:flex;align-items:center;gap:10px;font-weight:650;font-size:15px;letter-spacing:-.01em;color:var(--text)}
.brand svg{flex:none}
.status{display:inline-flex;align-items:center;gap:8px;font-size:13px;color:var(--muted);background:var(--surface);
  border:1px solid var(--line);border-radius:999px;padding:5px 12px;white-space:nowrap}
.dot{width:7px;height:7px;border-radius:50%;background:var(--faint)}
.dot.ready{background:#2E9E64}.dot.warn{background:#C98A1B}.dot.off{background:#C4554B}
.st-key-nav{border-bottom:1px solid var(--line);margin-bottom:36px}
.st-key-nav [data-testid="stHorizontalBlock"]{flex-wrap:nowrap!important;gap:4px!important}
.st-key-nav [data-testid="stColumn"]{width:auto!important;flex:0 0 auto!important;min-width:0!important}
.st-key-nav button{border-radius:8px 8px 0 0!important;padding:6px 12px!important;min-height:38px!important;color:var(--muted)!important;font-weight:500!important}
.st-key-nav button p{font-size:14px!important}
.st-key-nav button.active,.st-key-nav [class*="st-key-nav_on"] button{color:var(--text)!important;box-shadow:inset 0 -2px 0 var(--accent)}

/* Типографика */
.hero h1{font-size:40px;line-height:1.12;letter-spacing:-.028em;font-weight:680;margin:0 0 12px;color:var(--text);padding:0}
.hero p{font-size:17px;line-height:1.5;color:var(--muted);margin:0 0 32px;max-width:560px}
.label{font-size:13px;font-weight:600;color:var(--text);margin:0 0 6px}
.hint{font-size:13px;color:var(--muted);line-height:1.5;margin-top:8px}
.section-title{font-size:15px;font-weight:650;letter-spacing:-.01em;margin:36px 0 12px}

/* Поля */
[data-testid="stSelectbox"] label{display:none}
[data-baseweb="select"]>div{background:var(--surface)!important;border:1px solid var(--line)!important;border-radius:var(--r)!important;min-height:46px;box-shadow:none!important}
[data-baseweb="select"]>div:focus-within{border-color:var(--accent)!important;box-shadow:0 0 0 3px var(--accent-soft)!important}
.rubric-meta{font-size:13px;color:var(--muted);margin:8px 2px 28px}

/* Загрузка */
[data-testid="stFileUploader"] label{display:none}
[data-testid="stFileUploaderDropzone"]{background:var(--surface)!important;border:1.5px dashed #C9CDD3!important;border-radius:var(--r-lg)!important;
  padding:36px 20px!important;justify-content:center;transition:border-color .15s,background .15s}
[data-testid="stFileUploaderDropzone"]:hover{border-color:var(--accent)!important;background:#FBFCFF!important}
[data-testid="stFileUploaderDropzoneInstructions"] span{color:var(--text)!important;font-size:15px!important}
[data-testid="stFileUploaderDropzoneInstructions"] small{color:var(--muted)!important}
[data-testid="stFileUploader"] section button{border-radius:8px!important;border:1px solid var(--line)!important;background:var(--surface)!important;color:var(--text)!important}
[data-testid="stFileUploaderFile"],[data-testid="stFileUploaderPagination"]{display:none!important}
/* после выбора файла показываем собственную карточку, а зону загрузки сворачиваем */
[data-testid="stFileUploader"]:has([data-testid="stFileChip"]),[data-testid="stFileUploader"]:has([data-testid="stUploadedFile"]){display:none!important}
.filecard{display:flex;align-items:center;gap:14px;background:var(--surface);border:1px solid var(--line);border-radius:var(--r-lg);padding:14px 16px;margin-top:12px}
.filecard .ico{flex:none;width:40px;height:40px;border-radius:10px;background:var(--accent-soft);color:var(--accent);display:flex;align-items:center;justify-content:center}
.filecard .name{font-weight:600;font-size:15px;overflow-wrap:anywhere;line-height:1.3}
.filecard .sub{font-size:13px;color:var(--muted);margin-top:2px}
.st-key-file_row{margin-top:12px}
.st-key-file_row [data-testid="stHorizontalBlock"]{align-items:center;flex-wrap:nowrap!important;gap:8px!important}
.st-key-file_row .filecard{margin-top:0}

/* Кнопки */
.stButton>button,[data-testid="stBaseButton-secondary"],[data-testid="stBaseButton-primary"]{border-radius:var(--r)!important;min-height:46px;font-weight:600;font-family:var(--font)!important;transition:background .15s,border-color .15s}
[data-testid="stBaseButton-primary"]{background:var(--accent)!important;border:1px solid var(--accent)!important;color:#fff!important}
[data-testid="stBaseButton-primary"]:hover{background:#244FBA!important;border-color:#244FBA!important}
[data-testid="stBaseButton-primary"]:disabled{background:#CBD3E6!important;border-color:#CBD3E6!important;color:#fff!important;opacity:1}
[data-testid="stBaseButton-secondary"]{background:var(--surface)!important;border:1px solid var(--line)!important;color:var(--text)!important}
[data-testid="stBaseButton-secondary"]:hover{border-color:#C9CDD3!important}
button:focus-visible{outline:2px solid var(--accent)!important;outline-offset:2px}
.st-key-go{margin-top:20px}
.st-key-go button{width:100%}

/* Процесс */
.steps{background:var(--surface);border:1px solid var(--line);border-radius:var(--r-lg);padding:8px 20px;margin-top:8px}
.step{display:flex;align-items:flex-start;gap:14px;padding:14px 0;border-bottom:1px solid var(--line-soft);font-size:15px;color:var(--faint)}
.step:last-child{border-bottom:0}
.step .mark{flex:none;width:22px;height:22px;display:flex;align-items:center;justify-content:center;margin-top:1px}
.step.done{color:var(--text)}.step.done .mark{color:var(--ok)}
.step.active{color:var(--text);font-weight:600}
.step.skip{color:var(--faint)}
.step .sub{display:block;font-weight:400;font-size:13px;color:var(--muted);margin-top:2px}
.spin{width:16px;height:16px;border-radius:50%;border:2px solid #D5DBE8;border-top-color:var(--accent);animation:sp .8s linear infinite}
.pend{width:8px;height:8px;border-radius:50%;background:#D5D8DD}
@keyframes sp{to{transform:rotate(360deg)}}
.queue{display:flex;gap:10px;align-items:center;background:var(--accent-soft);color:#1F46A8;border-radius:var(--r);padding:12px 14px;font-size:14px;margin-top:14px}

/* Результат */
.result{animation:rise .22s ease-out}
@keyframes rise{from{opacity:0;transform:translateY(4px)}to{opacity:1;transform:none}}
.verdict{display:flex;align-items:center;gap:14px;border-radius:var(--r-lg);padding:16px 18px;border:1px solid}
.verdict.ready{background:var(--ok-bg);border-color:var(--ok-line);color:var(--ok)}
.verdict.fix{background:var(--bad-bg);border-color:var(--bad-line);color:var(--bad)}
.verdict .t{font-size:20px;font-weight:680;letter-spacing:-.015em}
.verdict .s{font-size:13px;opacity:.85;margin-top:2px;color:var(--text)}
.stats{display:flex;gap:10px;margin:12px 0 0}
.stat{flex:1;background:var(--surface);border:1px solid var(--line);border-radius:var(--r);padding:12px 16px}
.stat b{display:block;font-size:24px;font-weight:660;letter-spacing:-.02em;line-height:1.2}
.stat span{font-size:13px;color:var(--muted)}
.crit{background:var(--surface);border:1px solid var(--line);border-radius:var(--r-lg);overflow:hidden}
.row{display:flex;gap:14px;padding:16px 18px;border-bottom:1px solid var(--line-soft);align-items:flex-start}
.row:last-child{border-bottom:0}
.row .num{flex:none;width:24px;font-size:14px;color:var(--faint);font-variant-numeric:tabular-nums;padding-top:1px}
.row .body{flex:1;min-width:0}
.row .head{display:flex;gap:10px;align-items:flex-start;justify-content:space-between}
.row .name{font-weight:600;font-size:15px;line-height:1.35;overflow-wrap:anywhere}
.row .why{font-size:14px;color:var(--muted);margin-top:4px;line-height:1.5;overflow-wrap:anywhere}
.row.bad{background:linear-gradient(90deg,var(--bad-bg),var(--surface) 60%)}
.pill{flex:none;display:inline-flex;align-items:center;gap:5px;font-size:12.5px;font-weight:600;border-radius:999px;padding:3px 10px;white-space:nowrap}
.pill.ok{background:var(--ok-bg);color:var(--ok)}.pill.no{background:var(--bad-bg);color:var(--bad)}
.tag{display:inline-block;font-size:12px;color:var(--muted);border:1px solid var(--line);border-radius:6px;padding:0 6px;margin-left:8px;font-weight:500;vertical-align:1px}
.recs{background:var(--surface);border:1px solid var(--line);border-radius:var(--r-lg);padding:6px 18px}
.rec{display:flex;gap:12px;padding:12px 0;border-bottom:1px solid var(--line-soft);font-size:15px;line-height:1.5}
.rec:last-child{border-bottom:0}
.rec .n{flex:none;color:var(--accent);font-weight:650;width:18px}
.meta{background:var(--surface);border:1px solid var(--line);border-radius:var(--r-lg);padding:6px 18px;font-size:14px}
.meta div{display:flex;gap:16px;justify-content:space-between;padding:10px 0;border-bottom:1px solid var(--line-soft)}
.meta div:last-child{border-bottom:0}
.meta dt{color:var(--muted);flex:none}.meta dd{margin:0;text-align:right;overflow-wrap:anywhere}
.note{font-size:13px;color:var(--muted);margin-top:10px;line-height:1.5}

/* Ошибки */
.err{background:var(--surface);border:1px solid var(--line);border-radius:var(--r-lg);padding:28px;margin-top:8px}
.err .ic{width:44px;height:44px;border-radius:12px;background:var(--bad-bg);color:var(--bad);display:flex;align-items:center;justify-content:center;margin-bottom:16px}
.err h2{font-size:22px;letter-spacing:-.02em;margin:0 0 8px;font-weight:660;padding:0}
.err p{color:var(--muted);font-size:15px;line-height:1.55;margin:0 0 6px}
.err .todo{color:var(--text);margin-top:12px}

/* Страница рубрик */
.lab{background:var(--surface);border:1px solid var(--line);border-radius:var(--r-lg);padding:18px 20px;margin-bottom:12px}
.lab h3{margin:0 0 4px;font-size:17px;font-weight:650;letter-spacing:-.01em;padding:0}
.lab .d{color:var(--muted);font-size:14px;margin-bottom:10px}
.lab ol{margin:0;padding-left:20px;font-size:14px;line-height:1.7}

/* Адаптив */
@media (max-width:640px){
  [data-testid="stMainBlockContainer"]{padding:12px 16px 56px}
  .hero h1{font-size:30px}.hero p{font-size:16px;margin-bottom:24px}
  .status span.long{display:none}
  .stats{gap:8px}.stat{padding:10px 12px}.stat b{font-size:21px}
  .row{padding:14px;gap:10px}.row .head{flex-direction:column;gap:6px}
  .err{padding:20px}
  [data-testid="stFileUploaderDropzone"]{padding:26px 14px!important}
  .st-key-actions [data-testid="stHorizontalBlock"]{flex-direction:column}
  .st-key-actions [data-testid="stColumn"]{width:100%!important}
  .st-key-actions button{width:100%}
  .verdict .t{font-size:18px}
}
@media (min-width:1400px){[data-testid="stMainBlockContainer"]{max-width:920px}}
@media (prefers-reduced-motion:reduce){*{animation:none!important;transition:none!important}}
</style>
"""
