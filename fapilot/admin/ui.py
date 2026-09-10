# Embedded HTML keeps complete tags together.
# ruff: noqa: E501
"""Self-contained admin UI; no CDN, frontend build or template dependency."""

from html import escape

from fapilot.admin.icons import icon


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
CSS += """
:root{--bg:#f7f8fc;--surface:#fff;--text:#202b41;--muted:#69758b;--line:#e7eaf1;--accent:#4263eb;--soft:#eef2ff;--subtle:#fafbfe;--shadow:0 2px 6px #243b6503,0 8px 24px #243b6503;--brand:#4263eb}

:root[data-theme=dark]{--bg:#10141e;--surface:#181e2b;--text:#e9edf7;--muted:#9ba8bd;--line:#2b3447;--accent:#a5b6ff;--soft:#26324e;--subtle:#1c2433;--shadow:0 8px 24px #00000012;--brand:#6584ff}

[hidden]{display:none!important}
body{font-size:14px;-webkit-font-smoothing:antialiased}
.icon{width:19px;height:19px;flex-shrink:0;vertical-align:middle;stroke-width:1.8}
.sr-only{position:absolute;width:1px;height:1px;padding:0;margin:-1px;overflow:hidden;clip:rect(0,0,0,0);white-space:nowrap;border:0}
button,.button{display:inline-flex;align-items:center;justify-content:center;gap:8px;font-size:13px;font-weight:550;min-height:38px;border-radius:8px;transition:background .15s,border-color .15s,box-shadow .15s}
button:hover,.button:hover{background:var(--soft);text-decoration:none;border-color:var(--accent)}
button.primary,.button.primary{background:var(--brand);color:#fff;border-color:var(--brand);box-shadow:0 3px 8px #4263eb24}
.primary:hover{filter:brightness(1.08)}
button.danger{color:var(--bg)}
.shell{grid-template-columns:246px minmax(0,1fr)}
.sidebar{position:sticky;top:0;height:100svh;display:flex;flex-direction:column;padding:30px 17px 16px;z-index:20}
.brand{display:flex;gap:10px;align-items:center;letter-spacing:-.5px;font-size:18px;padding:0 6px;margin-bottom:27px}
.brand:hover{text-decoration:none}
.brand-mark{display:flex;align-items:center;justify-content:center;width:34px;height:37px;border-radius:10px;background:var(--brand);color:#fff;box-shadow:0 3px 7px #4263eb30;flex-shrink:0}
.brand-mark .icon{width:23px;height:23px}
.brand-name{overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.brand-name small{display:block;font-size:9px;font-weight:600;letter-spacing:1.7px;margin-top:1px;color:var(--muted)}
.nav-search{display:flex;align-items:center;gap:7px;padding:8px 10px;margin:0 4px 12px;border:1px solid var(--line);border-radius:8px;color:var(--muted);font-weight:400;min-width:0}
.nav-search input{padding:0!important;border:0!important;background:transparent!important;min-width:0;font-size:12px;outline-offset:5px}
.nav-search .icon{width:15px;height:15px}
kbd{font:10px/1.5 system-ui,sans-serif;border:1px solid var(--line);border-radius:4px;padding:1px 4px;background:var(--surface);color:var(--muted);white-space:nowrap}
.sidebar nav{flex:1;overflow-y:auto;overflow-x:hidden}
.caption{font-size:10px;letter-spacing:1.3px;font-weight:650;margin:24px 12px 10px;color:var(--muted)}
nav a{display:flex;align-items:center;gap:11px;padding:10px 12px;margin:4px 0;font-size:13px;font-weight:500;border-radius:8px}
nav a .icon{color:var(--muted);width:18px;height:18px}
nav a:hover{text-decoration:none}
nav a[aria-current=page]{background:var(--soft);color:var(--accent);font-weight:650}
nav a[aria-current=page] .icon{color:var(--accent)}
.nav-label{overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.sidebar-profile{display:flex;align-items:center;gap:10px;border-top:1px solid var(--line);padding:18px 6px 2px;margin-top:20px}
.avatar{width:34px;height:34px;border-radius:50%;display:flex;align-items:center;justify-content:center;background:var(--soft);color:var(--accent);font-weight:700;flex-shrink:0}
.profile-label{min-width:0}
.profile-label strong{font-size:12px;display:block;overflow:hidden;text-overflow:ellipsis}
.profile-label span{font-size:10px;color:var(--muted)}
header{height:74px;padding:0 34px;background:var(--surface)}
.header-location{display:flex;align-items:center;gap:14px;min-width:0;font-size:12px}
.header-location>.icon{width:13px;color:var(--muted)}
.breadcrumb-root{color:var(--muted)}
.breadcrumb-current{font-weight:600;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.icon-button{width:34px;height:34px;min-height:34px;padding:7px;background:transparent;border:1px solid transparent;color:var(--muted);border-radius:7px;display:inline-flex;align-items:center;justify-content:center}
.icon-button:hover{background:var(--soft);color:var(--accent);text-decoration:none;border-color:var(--line)}
.sidebar-toggle{margin-left:-8px}
.tools{gap:15px}
.theme-toggle{background:transparent;border:0;padding:5px 2px;color:var(--muted);font-size:12px;min-height:34px}
.theme-toggle .icon{width:17px;height:17px}
.theme-sun{display:none!important}
[data-theme=dark] .theme-moon{display:none!important}
[data-theme=dark] .theme-sun{display:inline-flex!important}
.header-divider{height:20px;width:1px;background:var(--line)}
.signout-button{border:0;background:transparent;color:var(--muted);font-size:12px;padding:5px 0;min-height:34px}
.signout-button .icon{width:16px}
.signout-button:hover,.theme-toggle:hover{background:transparent;color:var(--accent)}
main{max-width:1510px;padding:34px 34px 24px}
h1{font-size:29px;line-height:1.25;letter-spacing:-.9px;font-weight:750}
h2{font-size:15px;letter-spacing:-.25px}
h3{font-size:14px;margin:0 0 6px}
.card{box-shadow:var(--shadow);border-radius:12px}
.heading{margin-bottom:24px}
.heading p{margin:8px 0 0}
.dashboard-intro{display:flex;justify-content:space-between;align-items:center;gap:20px;margin:6px 0 27px}
.eyebrow{display:block;font-size:9px;font-weight:700;letter-spacing:1.5px;color:var(--muted);margin-bottom:8px}
.dashboard-intro h1{margin:0}
.heading-dot{color:var(--brand)}
.dashboard-intro p{margin:10px 0 0;font-size:12px}
.intro-actions{display:flex;flex-direction:column;align-items:flex-end;gap:12px;flex-shrink:0}
.date-pill{display:flex;align-items:center;gap:6px;font-size:11px;color:var(--muted)}
.date-pill .icon{width:14px;height:14px}
.quick-add{position:relative}
.quick-add summary{list-style:none;cursor:pointer}
.quick-add summary::-webkit-details-marker{display:none}
.quick-menu{position:absolute;right:0;top:46px;width:250px;z-index:10;background:var(--surface);box-shadow:0 12px 38px #00000020;border:1px solid var(--line);padding:6px;border-radius:10px}
.quick-menu a{display:flex;align-items:center;gap:10px;padding:11px 10px;color:var(--text);font-size:12px;border-radius:6px}
.quick-menu a span{flex:1}
.quick-menu a:hover{background:var(--soft);text-decoration:none}
.stats-grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:16px;margin-bottom:26px}
.stat-card{padding:18px 20px;background:var(--surface);border:1px solid var(--line);border-radius:11px;box-shadow:var(--shadow)}
.stat-top{display:flex;align-items:center;justify-content:space-between;gap:8px;font-size:11px;font-weight:550;color:var(--muted)}
.icon-tile{width:31px;height:31px;border-radius:8px;display:flex;align-items:center;justify-content:center}
.icon-tile .icon{width:16px;height:16px}
.blue{background:#edf2ff;color:#4664e5}
.violet{background:#f2edff;color:#9268d7}
.teal{background:#e8f8f3;color:#279b83}
.amber{background:#fff5e7;color:#bd852f}
[data-theme=dark] .blue{background:#273558;color:#adc0ff}
[data-theme=dark] .violet{background:#382d50;color:#c9aff6}
[data-theme=dark] .teal{background:#1d3c39;color:#85d7c6}
[data-theme=dark] .amber{background:#3d3429;color:#ebc18b}
.stat-value{font-size:32px;line-height:1.2;letter-spacing:-.8px;font-weight:700;margin:10px 0 11px;font-variant-numeric:tabular-nums}
.stat-caption{font-size:10px;color:var(--muted)}
.dashboard-columns{display:grid;grid-template-columns:minmax(0,1fr) 282px;gap:22px;align-items:start}
.dashboard-main,.dashboard-side{min-width:0}
.panel{background:var(--surface);border:1px solid var(--line);border-radius:12px;box-shadow:var(--shadow);overflow:hidden;margin-bottom:22px}
.panel-heading{padding:21px 22px 17px;display:flex;align-items:center;justify-content:space-between;gap:12px}
.panel-heading h2{display:flex;align-items:center;gap:9px;margin:0}
.panel-heading h2 .icon{color:var(--muted);width:17px;height:17px}
.panel-heading p{font-size:11px;color:var(--muted);margin:7px 0 0}
.count-badge,.subtle-badge{background:var(--subtle);border:1px solid var(--line);border-radius:5px;padding:1px 6px;color:var(--muted);font-size:10px;font-weight:500}
.directory-toolbar{padding:0 22px 18px;display:flex;gap:10px}
.search-control{display:flex;align-items:center;gap:9px;border:1px solid var(--line);background:var(--subtle);padding:8px 11px;border-radius:7px;flex:1;min-width:0;font-weight:400;color:var(--muted)}
.search-control input{padding:0!important;border:0!important;background:transparent!important;font-size:12px;min-width:0}
.search-control .icon{width:15px;height:15px}
.pin-filter{padding:7px 11px;min-height:34px;font-size:11px;color:var(--muted)}
.pin-filter .icon{width:14px;height:14px}
.pin-filter[aria-pressed=true]{color:var(--accent);background:var(--soft);border-color:var(--accent)}
.model-row{display:flex;align-items:center;gap:13px;padding:17px 22px;border-top:1px solid var(--line);transition:background .15s}
.model-row:hover{background:var(--subtle)}
.model-symbol{width:37px;height:37px;background:var(--soft);border:1px solid var(--line);color:var(--accent);border-radius:9px;display:flex;align-items:center;justify-content:center;flex-shrink:0}
.model-symbol .icon{width:19px;height:19px}
.model-info{flex:1;min-width:0}
.model-name{font-size:12px;font-weight:650;color:var(--text)}
.model-info p{font-size:10px;color:var(--muted);margin:3px 0 0;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.record-count{font-size:12px;text-align:right;color:var(--text);font-weight:600;min-width:44px;line-height:1.4;font-variant-numeric:tabular-nums}
.record-count small{display:block;font-size:9px;font-weight:400}
.model-actions{display:flex;align-items:center;gap:2px;margin-left:4px}
.model-actions .icon{width:16px;height:16px}
.pin-button[aria-pressed=true]{color:#bc8429}
.pin-button[aria-pressed=true] .icon{fill:#edba5330}
.panel-footer{display:flex;align-items:center;justify-content:space-between;gap:10px;font-size:9px;color:var(--muted);padding:12px 22px;background:var(--subtle);border-top:1px solid var(--line)}
.workspace-note{padding:25px 23px;background:linear-gradient(135deg,#eef2ff,#f4f0fc);border:1px solid #e0e6ff;border-radius:12px;margin-bottom:22px;overflow:hidden}
.note-icon{width:38px;height:38px;display:flex;align-items:center;justify-content:center;color:#5573dd;background:#ffffff90;border:1px solid #dbe2ff;border-radius:10px;margin-bottom:22px}
.note-icon .icon{width:21px;height:21px}
.workspace-note .eyebrow{font-size:8px;color:#6476a4}
.workspace-note h2{font-size:20px;line-height:1.35;margin:9px 0 12px;letter-spacing:-.5px;color:#31477c}
.workspace-note p{font-size:11px;line-height:1.8;margin:0;color:#6d7c9c}
.shortcut-hint{display:flex;align-items:center;gap:4px;margin-top:24px}
.shortcut-hint span{font-size:9px;color:#6d7c9c;margin-left:5px}
.shortcut-hint kbd{border-color:#d8dff2;background:#ffffff70;color:#667497}
[data-theme=dark] .workspace-note{background:linear-gradient(135deg,#202e4d,#2a2643);border-color:#344363}
[data-theme=dark] .note-icon{background:#354264;border-color:#4a5980;color:#b4c5ff}
[data-theme=dark] .workspace-note h2{color:#d9e1ff}
[data-theme=dark] .workspace-note p,[data-theme=dark] .workspace-note .eyebrow,[data-theme=dark] .shortcut-hint span{color:#a6b6d4}
[data-theme=dark] .shortcut-hint kbd{background:#344363;border-color:#4a5980;color:#d9e1ff}
.distribution-panel .panel-heading{padding-bottom:10px}
.distribution-list{padding:0 22px 22px}
.distribution-item{margin-top:17px}
.distribution-item>div{display:flex;justify-content:space-between;gap:10px;font-size:10px;margin-bottom:7px}
.distribution-item a{color:var(--muted)}
.distribution-item span{font-weight:650;font-variant-numeric:tabular-nums}
meter{width:100%;height:6px;display:block;background:var(--soft);border:0;border-radius:6px;appearance:none}
meter::-webkit-meter-bar{background:var(--soft);border:0;border-radius:6px;height:6px}
meter::-webkit-meter-optimum-value{background:var(--brand);border-radius:6px}
meter::-moz-meter-bar{background:var(--brand);border-radius:6px}
.dashboard-footnote{display:flex;align-items:center;gap:6px;justify-content:center;font-size:9px;color:var(--muted)}
.dashboard-footnote .icon{width:12px;height:12px}
.activity-list{list-style:none;margin:0;padding:0 22px}
.activity-item{display:flex;align-items:center;gap:12px;padding:16px 0;border-top:1px solid var(--line)}
.activity-symbol{display:flex;align-items:center;justify-content:center;width:30px;height:30px;border:1px solid var(--line);background:var(--subtle);border-radius:50%;color:var(--accent);flex-shrink:0}
.activity-symbol .icon{width:13px;height:13px}
.activity-item>div{flex:1;min-width:0}
.activity-item p{font-size:11px;margin:0;overflow-wrap:anywhere}
.activity-item a{font-size:10px}
.activity-item time{font-size:9px;white-space:nowrap;color:var(--muted)}
.activity-empty{display:flex;align-items:center;gap:14px;padding:12px 22px 27px}
.empty-icon{display:flex;align-items:center;justify-content:center;width:42px;height:42px;border-radius:50%;background:var(--subtle);border:1px dashed var(--line);color:var(--muted)}
.activity-empty h3{font-size:12px;margin:0 0 5px}
.activity-empty p{font-size:11px;color:var(--muted);margin:0}
footer{display:flex;justify-content:space-between;gap:15px;font-size:10px;margin-top:12px;padding-top:14px}
.footer-dot{margin:0 5px}
.field input,.field textarea,.field select{background:var(--subtle);font-size:13px}
.field label{font-size:12px}
.field small{font-size:10px}
th{background:var(--subtle);font-size:10px;color:var(--muted)}
td{font-size:12px;padding:16px 22px}
.filters label{font-size:11px}
.filters input{font-size:12px}
.table-wrap{box-shadow:var(--shadow)}
.login{max-width:460px}
.login .card{border-radius:16px;box-shadow:0 18px 60px #243b650d}
.sidebar-backdrop{display:none}
html:not(.js) .directory-toolbar,html:not(.js) .pin-button,html:not(.js) .sidebar-toggle,html:not(.js) .nav-search{display:none}

@media(min-width:761px){[data-collapsed=true] .shell{grid-template-columns:78px minmax(0,1fr)}
[data-collapsed=true] .sidebar{padding:30px 12px 16px}
[data-collapsed=true] .brand{padding:0 9px}
[data-collapsed=true] .brand-name,[data-collapsed=true] .caption,[data-collapsed=true] .nav-label,[data-collapsed=true] .nav-search,[data-collapsed=true] .profile-label{display:none}
[data-collapsed=true] nav a{justify-content:center;padding:12px;margin:8px 0}
[data-collapsed=true] .nav-group{margin:12px 0 24px}
[data-collapsed=true] .sidebar-profile{justify-content:center;padding-left:0;padding-right:0}
[data-collapsed=true] .sidebar-toggle .icon{transform:rotate(180deg)}
}

@media(max-width:1250px){.dashboard-columns{grid-template-columns:minmax(0,1fr) 250px;gap:16px}
.stats-grid{gap:12px}
.stat-card{padding:16px}
.model-row{padding:16px;gap:10px}
.model-actions{gap:0}
.model-actions .icon-button{width:29px}
.model-info p{max-width:180px}
.panel-footer span:last-child{display:none}
}

@media(max-width:1080px){.dashboard-columns{grid-template-columns:1fr}
.dashboard-side{display:grid;grid-template-columns:1fr 1fr;gap:20px}
.dashboard-footnote{grid-column:1/-1}
.stats-grid{grid-template-columns:repeat(2,minmax(0,1fr))}
.model-info p{max-width:none}
.dashboard-intro{align-items:flex-start}
.date-pill{display:none}
.workspace-note,.distribution-panel{margin-bottom:0}
}

@media(max-width:760px){.shell{grid-template-columns:minmax(0,1fr)}
.sidebar{position:relative;height:auto;padding:18px}
.brand{margin-bottom:12px}
.sidebar nav{display:block;overflow:visible}
.sidebar .caption{display:block}
.sidebar-profile{display:none}
.js .sidebar{position:fixed;inset:0 auto 0 0;width:260px;height:100svh;transform:translateX(-100%);transition:transform .2s;box-shadow:10px 0 35px #0002;border-right:1px solid var(--line)}
.js .sidebar nav{overflow:auto}
.js .sidebar-profile{display:flex}
.js[data-sidebar-open=true] .sidebar{transform:translateX(0)}
.js[data-sidebar-open=true] .sidebar-backdrop{display:block;position:fixed;inset:0;width:100%;height:100%;border:0;border-radius:0;background:#080f244d;backdrop-filter:blur(2px);z-index:19}
.js[data-sidebar-open=true]{overflow:hidden}
header{height:64px;flex-wrap:nowrap;padding:0 20px}
.header-location{gap:9px}
.breadcrumb-root,.header-location>.icon{display:none}
.tools{gap:12px}
.tools span{display:initial}
.theme-toggle>span:last-child,.signout-button span,.header-divider{display:none}
.tools button{min-width:30px}
.header-location .icon-button{margin-right:1px}
.tools .icon{width:18px;height:18px}
.theme-toggle .theme-sun{display:none}
.dashboard-intro{display:block;margin-top:0}
.intro-actions{align-items:flex-start;margin-top:18px}
main{padding:25px 18px 20px}
h1{font-size:26px}
.dashboard-intro p{font-size:11px;max-width:300px;line-height:1.7}
.stats-grid{gap:10px;margin-bottom:20px}
.stat-card{padding:14px}
.stat-top{font-size:10px;gap:5px}
.icon-tile{width:27px;height:27px}
.stat-value{font-size:27px;margin:9px 0}
.stat-caption{font-size:9px;line-height:1.6}
.dashboard-side{grid-template-columns:1fr}
.panel-heading{padding:18px 16px 15px}
.directory-toolbar{padding:0 16px 15px;gap:7px}
.model-row{padding:16px 12px;gap:9px;flex-wrap:wrap}
.model-symbol{width:30px;height:32px;border-radius:8px}
.model-info{flex-basis:calc(100% - 108px)}
.model-name{font-size:12px}
.model-info p{font-size:9px;max-width:210px}
.record-count{min-width:38px}
.model-actions{margin-left:39px}
.model-actions .icon-button{width:32px;height:28px;min-height:28px}
.model-row{row-gap:4px}
.panel-footer{padding:12px 16px;font-size:9px}
.activity-list{padding:0 16px}
.activity-item{flex-wrap:wrap;gap:9px}
.activity-item time{margin-left:39px}
.activity-item>div{flex-basis:calc(100% - 40px)}
.activity-empty{padding:10px 16px 22px}
.activity-empty p{font-size:10px}
footer>span:last-child{display:none}
.workspace-note{padding:24px}
.quick-menu{left:0;right:auto}
.heading{flex-wrap:wrap}
.actions{gap:9px}
.actions button{font-size:11px}
.card{padding:20px}
.card.table-wrap{padding:0}
}

@media(prefers-reduced-motion:reduce){*,*::before,*::after{scroll-behavior:auto!important;transition:none!important}
}


.quick-action-list{margin-top:16px;display:grid;gap:7px}
.quick-action-link{display:flex;align-items:center;gap:8px;padding:10px;background:var(--surface);border:1px solid var(--line);border-radius:7px;font-size:11px;color:var(--text)}
.quick-action-link span{flex:1}
.quick-action-link .icon{width:14px;height:14px;color:var(--accent)}
.quick-action-link:hover{text-decoration:none;background:var(--soft)}

"""

JS = """
(() => {
  const root = document.documentElement;
  root.classList.add('js');
  try {
    root.dataset.theme = localStorage.getItem('fapilot-theme') ||
      (matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light');
  } catch (error) { root.dataset.theme = 'light'; }
  document.addEventListener('DOMContentLoaded', () => {
    const scope = document.body.dataset.scope || '';
    const pinKey = 'fapilot-pins:' + scope;
    const layoutKey = 'fapilot-sidebar:' + scope;
    let pins = new Set();
    let onlyPinned = false;
    try {
      const saved = JSON.parse(localStorage.getItem(pinKey) || '[]');
      if (Array.isArray(saved)) pins = new Set(saved.filter(v => typeof v === 'string'));
      root.dataset.collapsed = localStorage.getItem(layoutKey) || 'false';
    } catch (error) {}
    const modelSearch = document.querySelector('[data-model-search]');
    const navSearch = document.querySelector('[data-nav-search]');
    function filterModels() {
      let count = 0;
      const query = (modelSearch?.value || '').toLowerCase();
      document.querySelectorAll('[data-model]').forEach(row => {
        row.hidden = !row.dataset.search.includes(query) || (onlyPinned && !pins.has(row.dataset.model));
        if (!row.hidden) count++;
      });
      document.querySelectorAll('[data-pin]').forEach(button => {
        const pinned = pins.has(button.dataset.pin);
        button.setAttribute('aria-pressed', String(pinned));
        const name = button.closest('[data-model]').querySelector('.model-name').textContent;
        button.setAttribute('aria-label', (pinned ? 'Unpin ' : 'Pin ') + name);
        button.title = (pinned ? 'Unpin ' : 'Pin ') + name;
      });
      const empty = document.querySelector('.directory-empty');
      if (empty) empty.hidden = count > 0 || !document.querySelector('[data-model]');
      const label = document.querySelector('[data-model-count]');
      if (label) label.textContent = count + ' models shown' + (onlyPinned ? ' · pinned' : '');
    }
    modelSearch?.addEventListener('input', filterModels);
    navSearch?.addEventListener('input', () => {
      const query = navSearch.value.toLowerCase();
      document.querySelectorAll('.nav-group').forEach(group => {
        let visible = false;
        group.querySelectorAll('a').forEach(link => {
          link.hidden = !link.textContent.toLowerCase().includes(query);
          visible ||= !link.hidden;
        });
        group.hidden = !visible;
      });
    });
    const sidebar = document.querySelector('.sidebar');
    function syncSidebar() {
      const mobile = matchMedia('(max-width: 760px)').matches;
      if (sidebar) sidebar.inert = mobile && root.dataset.sidebarOpen !== 'true';
      const expanded = matchMedia('(max-width: 760px)').matches ? root.dataset.sidebarOpen === 'true' : root.dataset.collapsed !== 'true';
      document.querySelectorAll('[data-sidebar-toggle]').forEach(b => b.setAttribute('aria-expanded', String(expanded)));
    }
    window.addEventListener('resize', syncSidebar);
    document.addEventListener('click', event => {
      if (event.target.matches('[data-select-all]')) {
        document.querySelectorAll('[name=selected]').forEach(c => c.checked = event.target.checked);
      }
      if (event.target.closest('[data-theme-toggle]')) {
        root.dataset.theme = root.dataset.theme === 'dark' ? 'light' : 'dark';
        try {localStorage.setItem('fapilot-theme', root.dataset.theme)} catch (error) {}
      }
      const pin = event.target.closest('[data-pin]');
      if (pin) {
        if (pins.has(pin.dataset.pin)) pins.delete(pin.dataset.pin); else pins.add(pin.dataset.pin);
        try {localStorage.setItem(pinKey, JSON.stringify([...pins]))} catch (error) {}
        filterModels();
      }
      const filter = event.target.closest('[data-pin-filter]');
      if (filter) {
        onlyPinned = !onlyPinned;
        filter.setAttribute('aria-pressed', String(onlyPinned));
        filterModels();
      }
      if (event.target.closest('[data-sidebar-toggle]')) {
        if (matchMedia('(max-width: 760px)').matches) {
          root.dataset.sidebarOpen = root.dataset.sidebarOpen === 'true' ? 'false' : 'true';
        } else {
          root.dataset.collapsed = root.dataset.collapsed === 'true' ? 'false' : 'true';
          try {localStorage.setItem(layoutKey, root.dataset.collapsed)} catch (error) {}
        }
        syncSidebar();
        if (matchMedia('(max-width: 760px)').matches && root.dataset.sidebarOpen === 'true') navSearch?.focus();
      }
      if (event.target.closest('[data-close-sidebar]')) {
        root.dataset.sidebarOpen = 'false'; syncSidebar();
        document.querySelector('[data-sidebar-toggle]')?.focus();
      }
    });
    document.addEventListener('keydown', event => {
      if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === 'k') {
        if (!navSearch) return;
        event.preventDefault(); root.dataset.collapsed = 'false'; root.dataset.sidebarOpen = 'true';
        syncSidebar(); navSearch.focus();
      }
      if (event.key === '/' && !event.target.closest('input, textarea, select, [contenteditable]')) {
        if (modelSearch) { event.preventDefault(); modelSearch.focus(); }
      }
      if (event.key === 'Escape' && root.dataset.sidebarOpen === 'true') {
        root.dataset.sidebarOpen = 'false'; syncSidebar();
        document.querySelector('[data-sidebar-toggle]')?.focus();
      }
      if (event.key === 'Tab' && matchMedia('(max-width: 760px)').matches && root.dataset.sidebarOpen === 'true' && sidebar) {
        const targets = [...sidebar.querySelectorAll('a, input, button')].filter(el => el.getClientRects().length && !el.closest('[hidden]'));
        const first = targets[0], last = targets[targets.length - 1];
        if (event.shiftKey && document.activeElement === first) {event.preventDefault();last?.focus();}
        else if (!event.shiftKey && document.activeElement === last) {event.preventDefault();first?.focus();}
      }
    });
    filterModels(); syncSidebar();
  });
})();
"""


def nav_link(url: str, label: str, symbol: str, active: bool = False) -> str:
    current = ' aria-current="page"' if active else ""
    return (
        f'<a href="{e(url)}" title="{e(label)}"{current}>{icon(symbol)}'
        f'<span class="nav-label">{e(label)}</span></a>'
    )


def page(
    title: str,
    body: str,
    base: str,
    csrf: str,
    *,
    nav: str = "",
    user: str = "",
    site_title: str = "Fapilot administration",
    current_path: str = "",
    storage_scope: str = "",
) -> str:
    head = (
        f'<!doctype html><html lang="en"><head><meta charset="utf-8">'
        f'<meta name="viewport" content="width=device-width, initial-scale=1">'
        f"<title>{e(title)} · {e(site_title)}</title>"
        f'<link rel="stylesheet" href="{base}/assets/admin.css">'
        f'<script src="{base}/assets/admin.js"></script></head><body data-scope="{e(storage_scope)}">'
    )
    toggle = (
        f'<button type="button" class="theme-toggle" data-theme-toggle aria-label="Toggle light or dark theme">'
        f'<span class="theme-moon">{icon("moon")}</span><span class="theme-sun">{icon("sun")}</span>'
        "<span>Theme</span></button>"
    )
    if not user:
        return head + f'<div class="login">{toggle}{body}</div></body></html>'
    overview_link = nav_link(base + "/", "Overview", "layout-dashboard", current_path == base + "/")
    return (
        head
        + f'''<a class="skip" href="#content">Skip to content</a>
<button class="sidebar-backdrop" data-close-sidebar aria-label="Close navigation" tabindex="-1"></button>
<div class="shell"><aside class="sidebar" id="admin-navigation">
<a class="brand" href="{base}/"><span class="brand-mark">{icon("layers")}</span><span class="brand-name">{e(site_title)}<small>ADMINISTRATION</small></span></a>
<label class="nav-search">{icon("search")}<span class="sr-only">Search navigation</span><input data-nav-search aria-label="Search navigation" type="search" placeholder="Find a page…"><kbd>⌘ K</kbd></label>
<nav aria-label="Main navigation"><div class="nav-group"><div class="caption">Workspace</div>{overview_link}</div>{nav}</nav>
<div class="sidebar-profile"><span class="avatar">{e(user[:1].upper())}</span><div class="profile-label"><strong>{e(user)}</strong><span>Administration account</span></div></div>
</aside><div class="workspace"><header><div class="header-location">
<button class="icon-button sidebar-toggle" type="button" data-sidebar-toggle aria-controls="admin-navigation" aria-label="Toggle navigation">{icon("panel-left-close")}</button>
<span class="breadcrumb-root">Workspace</span>{icon("chevron-right")}<span class="breadcrumb-current">{e(title)}</span></div>
<div class="tools">{toggle}<span class="header-divider"></span><form method="post" action="{base}/logout">{token(csrf)}
<button class="signout-button">{icon("log-out")}<span>Sign out</span></button></form></div></header>
<main id="content">{body}<footer><span>Fapilot <span class="footer-dot">·</span> Administration workspace</span><span>Built for your everyday work</span></footer></main></div></div></body></html>'''
    )


def token(csrf: str) -> str:
    return f'<input type="hidden" name="_csrf" value="{e(csrf)}">'
