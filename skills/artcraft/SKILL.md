---
name: artcraft
description: Choose and operate ArtCraft apps to create, edit, convert, or export files. Use for named Craft apps or projects, and for matching file tasks such as combining PDFs in order, editing a named vector shape, developing RAW photos, or rendering a slide deck. Honor the user's chosen editor.
---

# ArtCraft

Choose the app from the **requested change and deliverable**. Read the [app guide](references/apps.md) when choosing between apps or locating an interface. A PDF can be the input to a page reorder in PdfCraft or the output of a layout job in DesignCraft. For advice or draft copy, answer directly unless the user wants work in an app.

1. Identify the source file or open document and the requested result, including which parts must remain editable. If the user specified an app, use it. Clarify only if the choice changes the deliverable and the request or source cannot resolve it.
2. Inspect the selected app's available interface. For a file on disk, check its CLI on PATH and read its help or command catalog. For an open document, use its connected MCP tools or documented live control interface and confirm the document identity before editing. A headless session has its own document state. If the user required a specific interface and it is unavailable, identify the missing component. Otherwise, use another documented route only if it can access the same document state, including unsaved edits. If the requested app cannot run, link its official page. For an unnamed-app task, use an available tool that preserves the source state and requested result.
3. Use the command or tool schema from the running version. Keep state-dependent operations in the same session. Save the editable document when requested and export the delivery format separately when both are needed. Check import warnings before overwriting an original.
4. Verify the property the user asked to change, such as page sequence, object name and color, slide count, or audio duration. Inspect the connected document for live-only edits. For a file delivery, reopen or independently inspect the written file. For visual edits, inspect a render when appearance matters.

For an ordered PDF merge or an edit to a named vector object, follow the [worked procedures](references/workflows.md).
