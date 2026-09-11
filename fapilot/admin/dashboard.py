# Embedded HTML keeps complete tags together.
# ruff: noqa: E501
"""Permission-aware dashboard built from live model counts and audit metadata."""

from datetime import UTC, datetime
from urllib.parse import quote

from tortoise.exceptions import ValidationError

from fapilot.admin.icons import icon
from fapilot.admin.models import AdminLogEntry
from fapilot.admin.ui import e


async def overview(request, registry, base: str) -> str:
    models = []
    editable = 0
    for key, admin in registry.items():
        if not await admin.has_view_permission(request):
            continue
        count = await (await admin.get_queryset(request)).count()
        add = await admin.has_add_permission(request)
        change = await admin.has_change_permission(request)
        editable += bool(change)
        models.append((key, admin, count, add))
    models.sort(key=lambda item: item[1].menu_group == "Access management")
    total = sum(item[2] for item in models)
    user = str(getattr(request.state, "admin_staff", request.state.admin_user))
    date = datetime.now(UTC).strftime("%A, %B %d")
    shortcuts = "".join(
        f'<a href="{base}/{key}/add">{icon(admin.icon)}<span>{e(admin.verbose_name or admin.model.__name__)}</span>{icon("plus")}</a>'
        for key, admin, _, add in models
        if add
    )
    quick_add = (
        f'<details class="quick-add"><summary class="button primary">{icon("plus")}Create new</summary>'
        f'<div class="quick-menu">{shortcuts}</div></details>'
        if shortcuts
        else ""
    )
    body = (
        '<div class="dashboard-intro"><div><div class="eyebrow">YOUR WORKSPACE, AT A GLANCE</div>'
        f'<h1>Workspace overview<span class="heading-dot">.</span></h1>'
        f'<p class="muted">Welcome back, {e(user)}. Here is what is happening in your workspace.</p>'
        f'</div><div class="intro-actions"><span class="date-pill">{icon("calendar-days")}{date}</span>{quick_add}</div></div>'
    )
    stats = (
        ("database", "Managed records", f"{total:,}", "Across the models you can access", "blue"),
        ("layers", "Available models", str(len(models)), "Your workspace collections", "violet"),
        ("pencil", "Editable models", str(editable), "Model-level editing access", "teal"),
        (
            "lock-keyhole",
            "Read-only models",
            str(len(models) - editable),
            "Model-level view access",
            "amber",
        ),
    )
    body += '<div class="stats-grid">'
    for symbol, title, value, caption, tone in stats:
        body += (
            f'<section class="stat-card"><div class="stat-top"><span>{title}</span>'
            f'<span class="icon-tile {tone}">{icon(symbol)}</span></div><div class="stat-value">{value}</div>'
            f'<div class="stat-caption">{caption}</div></section>'
        )
    body += '</div><div class="dashboard-columns"><div class="dashboard-main">'
    body += (
        '<section class="panel model-panel"><div class="panel-heading"><div>'
        f'<h2>{icon("folders")}Model directory <span class="count-badge">{len(models)}</span></h2>'
        "<p>Browse, organize, and manage your data.</p></div></div>"
        '<div class="directory-toolbar"><label class="search-control">'
        f'{icon("search")}<span class="sr-only">Find a model</span>'
        '<input type="search" data-model-search aria-label="Find a model" placeholder="Find a model…" autocomplete="off">'
        '<kbd>/</kbd></label><button type="button" class="pin-filter" data-pin-filter aria-pressed="false">'
        f'{icon("star")}Pinned</button></div><div class="model-directory">'
    )
    for key, admin, count, add in models:
        name = admin.verbose_name or admin.model.__name__
        description = admin.description or f"Manage {name.lower()} records and details."
        body += (
            f'<article class="model-row" data-model="{e(key)}" data-search="{e(name.lower() + " " + description.lower())}">'
            f'<div class="model-symbol">{icon(admin.icon)}</div><div class="model-info">'
            f'<a class="model-name" href="{base}/{key}/">{e(name)}</a><p>{e(description)}</p></div>'
            f'<span class="record-count">{count:,}<small>records</small></span><div class="model-actions">'
            f'<button type="button" class="icon-button pin-button" data-pin="{e(key)}" aria-pressed="false" aria-label="Pin {e(name)}" title="Pin {e(name)}">{icon("star")}</button>'
        )
        if add:
            body += f'<a class="icon-button add-model" href="{base}/{key}/add" aria-label="Add {e(name)}" title="Add {e(name)}">{icon("plus")}</a>'
        body += f'<a class="icon-button open-model" href="{base}/{key}/" aria-label="Open {e(name)}">{icon("arrow-up-right")}</a></div></article>'
    if not models:
        body += '<div class="empty"><h2>No models available</h2><p>Register a model or request access from an administrator.</p></div>'
    body += (
        '</div><div class="empty directory-empty" hidden><h3>No matching models</h3>'
        "<p>Try another search or turn off the pinned filter.</p></div>"
        '<div class="panel-footer"><span data-model-count>'
        f"{len(models)} models available</span><span>Only models you can access are shown</span></div></section>"
    )
    # Resolve current objects through the same scoped queryset used by change views.
    # Deleted or newly inaccessible records are deliberately omitted from the dashboard.
    keys = [key for key, *_ in models]
    entries = (
        await AdminLogEntry.filter(site=base, actor=request.state.admin_user, model__in=keys).limit(
            100
        )
        if keys
        else []
    )
    objects = {}
    for key, admin, _, _ in models:
        ids = {entry.object_id for entry in entries if entry.model == key}
        if not ids:
            continue
        try:
            found = await (await admin.get_queryset(request)).filter(pk__in=list(ids))
        except (ValueError, TypeError, ValidationError):
            continue
        for obj in found:
            if await admin.has_view_permission(request, obj):
                objects[key, str(obj.pk)] = obj
    activity = ""
    visible_entries = 0
    for entry in entries:
        obj = objects.get((entry.model, entry.object_id))
        if obj is None:
            continue
        admin = registry[entry.model]
        symbol = {"add": "plus", "change": "pencil", "delete": "trash-2"}.get(
            entry.action, "activity"
        )
        action = {"add": "Created", "change": "Updated"}.get(
            entry.action, entry.action.replace("_", " ").title()
        )
        stamp = entry.created_at.astimezone(UTC)
        activity += (
            f'<li class="activity-item"><span class="activity-symbol">{icon(symbol)}</span><div>'
            f"<p><strong>{e(action)}</strong> in {e(admin.verbose_name or admin.model.__name__)}</p>"
            f'<a href="{base}/{entry.model}/{quote(entry.object_id, safe="")}/history">Record #{e(entry.object_id)}</a>'
            f'</div><time datetime="{stamp.isoformat()}" title="{stamp.strftime("%Y-%m-%d %H:%M UTC")}">{stamp.strftime("%b %d · %H:%M")}</time></li>'
        )
        visible_entries += 1
        if visible_entries == 6:
            break
    body += (
        '<section class="panel activity-panel"><div class="panel-heading"><div>'
        f"<h2>{icon('activity')}Your recent activity</h2><p>Your latest changes to accessible records.</p>"
        '</div><span class="subtle-badge">Latest 6</span></div>'
    )
    body += (
        f'<ol class="activity-list">{activity}</ol>'
        if activity
        else (
            f'<div class="activity-empty"><span class="empty-icon">{icon("clock-3")}</span>'
            "<div><h3>A fresh start</h3><p>Your recent additions and edits will appear here.</p></div></div>"
        )
    )
    body += '</section></div><div class="dashboard-side">'
    quick_links = "".join(
        f'<a class="quick-action-link" href="{base}/{key}/add">{icon("plus")}<span>Create {e(admin.verbose_name or admin.model.__name__)}</span>{icon("arrow-up-right")}</a>'
        for key, admin, _, add in [item for item in models if item[3]][:3]
    )
    if not quick_links:
        quick_links = "<p>Use the model directory to explore the records you can access.</p>"
    body += (
        '<section class="workspace-note"><div class="note-icon">'
        f'{icon("plus")}</div><span class="eyebrow">SKIP THE EXTRA CLICKS</span>'
        "<h2>Quick actions</h2><p>Start a new record in your workspace.</p>"
        f'<div class="quick-action-list">{quick_links}</div>'
        '<div class="shortcut-hint"><kbd>⌘ / Ctrl</kbd><kbd>K</kbd><span>Find navigation</span></div></section>'
    )
    body += (
        '<section class="panel distribution-panel"><div class="panel-heading"><div>'
        f"<h2>{icon('database')}Record distribution</h2><p>Largest accessible collections</p></div></div>"
        '<div class="distribution-list">'
    )
    for key, admin, count, _ in sorted(models, key=lambda item: item[2], reverse=True)[:5]:
        percent = round(count / total * 100) if total else 0
        body += (
            f'<div class="distribution-item"><div><a href="{base}/{key}/">{e(admin.verbose_name or admin.model.__name__)}</a>'
            f'<span>{count:,}</span></div><meter min="0" max="{max(total, 1)}" value="{count}" aria-label="{e(admin.verbose_name or admin.model.__name__)}: {percent}% of records">{percent}%</meter></div>'
        )
    if not models:
        body += '<p class="muted">No records to summarize yet.</p>'
    body += '</div></section><div class="dashboard-footnote">'
    body += f"{icon('clock-3')}Updated on page load. All times are UTC.</div></div></div>"
    return body
