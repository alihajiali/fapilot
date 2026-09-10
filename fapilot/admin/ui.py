# Embedded HTML keeps complete tags together.
# ruff: noqa: E501
"""Self-contained admin UI; no CDN, frontend build or template dependency."""

from html import escape


def e(value: object) -> str:
    return escape(str(value), quote=True)


CSS = """
.shell > *, aside {min-width:0}

:root{
  color-scheme:light;
  --bg:#f4f6fa;
  --surface:#fff;
  --text:#17243b;
  --muted:#617087;
  --line:#dee4ed;
  --accent:#345ee8;
  --soft:#eef2ff;
  --danger:#b52640
}

:root[data-theme=dark]{
  color-scheme:dark;
  --bg:#101521;
  --surface:#192131;
  --text:#edf2fc;
  --muted:#a5b3c9;
  --line:#303d52;
  --accent:#9ab1ff;
  --soft:#263450;
  --danger:#ff9aab
}

*{
  box-sizing:border-box
}
body{
  margin:0;
  background:var(--bg);
  color:var(--text);
  font:15px/1.55 system-ui,sans-serif
}
a{
  color:var(--accent);
  text-decoration:none
}
a:hover{
  text-decoration:underline
}
button,input,select,textarea{
  font:inherit
}
button,.button{
  border:1px solid var(--line);
  border-radius:9px;
  padding:10px 16px;
  background:var(--surface);
  color:var(--text);
  cursor:pointer;
  display:inline-block
}
button.primary,.button.primary{
  background:var(--accent);
  color:var(--bg);
  border-color:var(--accent);
  font-weight:650
}
button.danger{
  background:var(--danger);
  color:var(--bg)
}
a:focus-visible,button:focus-visible,input:focus-visible,select:focus-visible,textarea:focus-visible{
  outline:3px solid var(--accent);
  outline-offset:3px
}
.shell{
  display:grid;
  grid-template-columns:240px minmax(0,1fr);
  min-height:100vh
}
aside{
  background:var(--surface);
  border-right:1px solid var(--line);
  padding:28px 20px
}
.brand{
  font-size:22px;
  font-weight:800;
  color:var(--text);
  letter-spacing:-1px
}
.brand b{
  color:var(--accent)
}
.caption{
  color:var(--muted);
  font-size:12px;
  text-transform:uppercase;
  letter-spacing:1.4px;
  margin:32px 10px 10px
}
nav a{
  display:block;
  padding:10px 12px;
  border-radius:8px;
  margin:4px 0;
  color:var(--text)
}
nav a:hover{
  background:var(--soft)
}
header{
  display:flex;
  justify-content:space-between;
  align-items:center;
  padding:18px 36px;
  border-bottom:1px solid var(--line);
  background:var(--surface);
  gap:16px
}
.tools,.actions{
  display:flex;
  gap:12px;
  align-items:center;
  flex-wrap:wrap
}
.tools form{
  margin:0
}
main{
  max-width:1250px;
  margin:auto;
  padding:36px
}
h1{
  font-size:30px;
  letter-spacing:-1px;
  margin:12px 0 4px
}
h2{
  font-size:18px;
  margin:0 0 16px
}
.muted,small{
  color:var(--muted)
}
.heading{
  display:flex;
  justify-content:space-between;
  align-items:center;
  gap:16px;
  margin-bottom:28px
}
.card{
  background:var(--surface);
  border:1px solid var(--line);
  border-radius:14px;
  padding:24px;
  margin:20px 0;
  box-shadow:0 3px 10px #00000003
}
.grid{
  display:grid;
  grid-template-columns:repeat(auto-fit,minmax(220px,1fr));
  gap:20px
}
.grid .card{
  margin:0
}
.metric{
  font-size:36px;
  font-weight:750;
  margin:16px 0
}
.table-wrap{
  overflow:auto;
  padding:0
}
table{
  border-collapse:collapse;
  width:100%;
  white-space:nowrap
}
th,td{
  text-align:left;
  padding:15px 22px;
  border-bottom:1px solid var(--line)
}
th{
  background:var(--soft);
  font-size:12px;
  text-transform:uppercase;
  letter-spacing:.6px
}
tr:last-child td{
  border-bottom:0
}
.filters{
  display:flex;
  align-items:end;
  gap:14px;
  flex-wrap:wrap
}
.filters label{
  flex:1;
  min-width:140px
}
.filters input,.filters select{
  margin-top:6px
}
.field{
  margin-bottom:24px;
  max-width:760px
}
label{
  display:block;
  font-weight:600
}
input:not([type=checkbox]),select,textarea{
  width:100%;
  padding:10px 12px;
  border:1px solid var(--line);
  border-radius:8px;
  background:var(--bg);
  color:var(--text)
}
textarea{
  min-height:130px
}
input[type=checkbox]{
  width:20px;
  height:20px;
  accent-color:var(--accent)
}
.field input,.field select,.field textarea{
  margin-top:8px
}
.error{
  background:var(--soft);
  border-left:4px solid var(--danger);
  padding:16px;
  border-radius:6px;
  color:var(--danger)
}
.empty{
  text-align:center;
  padding:50px 20px
}
.login{
  max-width:440px;
  margin:10vh auto;
  padding:0 20px
}
.login .card{
  padding:32px
}
.login h1{
  font-size:26px
}
.pagination{
  display:flex;
  justify-content:space-between;
  margin-top:24px
}
.skip{
  position:absolute;
  left:-9999px
}
.skip:focus{
  left:12px;
  top:12px;
  background:var(--surface);
  padding:10px;
  z-index:2
}
code{
  overflow-wrap:anywhere
}
footer{
  color:var(--muted);
  font-size:12px;
  margin-top:32px
}
@media(max-width:760px){
  .shell{
  grid-template-columns:minmax(0,1fr)
}
aside{
  padding:16px;
  border-right:0;
  border-bottom:1px solid var(--line)
}
aside .caption{
  display:none
}
nav{
  display:flex;
  overflow:auto;
  gap:8px
}
nav a{
  white-space:nowrap
}
header{
  flex-wrap:wrap;
  padding:14px 20px
}
main{
  padding:20px
}
.heading{
  align-items:start
}
.tools{
  gap:8px
}
.tools span{
  display:none
}

}


.notice{padding:14px 18px;background:var(--soft);border-radius:9px;color:var(--accent)}
.actions select{width:auto;max-width:100%}
"""
JS = """
(()=>{let t;
try{t=localStorage.getItem('fapilot-theme')}catch(e){}document.documentElement.dataset.theme=t||(matchMedia('(prefers-color-scheme: dark)').matches?'dark':'light');
document.addEventListener('click',e=>{if(e.target.matches('[data-select-all]')){document.querySelectorAll('[name=selected]').forEach(c=>c.checked=e.target.checked)}if(e.target.closest('[data-theme-toggle]')){let t=document.documentElement.dataset.theme==='dark'?'light':'dark';
document.documentElement.dataset.theme=t;
try{localStorage.setItem('fapilot-theme',t)}catch(e){}}})})();

"""


def page(
    title: str,
    body: str,
    base: str,
    csrf: str,
    *,
    nav: str = "",
    user: str = "",
    site_title: str = "Fapilot administration",
) -> str:
    head = (
        f'<!doctype html><html lang="en"><head><meta charset="utf-8">'
        f'<meta name="viewport" content="width=device-width, initial-scale=1">'
        f"<title>{e(title)} · {e(site_title)}</title>"
        f'<link rel="stylesheet" href="{base}/assets/admin.css">'
        f'<script src="{base}/assets/admin.js"></script></head><body>'
    )
    toggle = '<button type="button" data-theme-toggle aria-label="Toggle light or dark theme">◐ Theme</button>'
    if not user:
        return head + f'<div class="login">{toggle}{body}</div></body></html>'
    return (
        head
        + f'''<a class="skip" href="#content">Skip to content</a><div class="shell">
<aside><a class="brand" href="{base}/"><b>◈</b> {e(site_title)}</a>
<div class="caption">Workspace</div><nav><a href="{base}/">Overview</a>{nav}</nav></aside>
<div><header><span class="muted">Administration / {e(title)}</span><div class="tools">
<span>{e(user)}</span>{toggle}<form method="post" action="{base}/logout">{token(csrf)}
<button>Sign out</button></form></div></header><main id="content">{body}
<footer>Fapilot · Administration workspace</footer></main></div></div></body></html>'''
    )


def token(csrf: str) -> str:
    return f'<input type="hidden" name="_csrf" value="{e(csrf)}">'
