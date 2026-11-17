# File workflows

## Combine PDFs in the supplied order

For saved inputs, pass the paths in the requested order. A shell glob can silently put an appendix first. If the user wants pending edits from an open PDF, use a live operation that includes those edits or export a current copy from the connected app before combining. If neither is available, identify which input needs a current copy. Write a new output and reopen it with PdfCraft.

```sh
pdfcraft-cli combine "summary.pdf" "appendix.pdf" --out "packet.pdf"
pdfcraft-cli info "packet.pdf"
pdfcraft-cli text "packet.pdf" --page 1
```

Compare the output page count with the sum of the inputs. Compare the output page texts in sequence with the concatenated input page texts. For scanned pages or pages with identical text but different graphics, render the corresponding pages at the same resolution and compare their images. Page numbers start at 1. See the [PdfCraft CLI and downloads](https://getartcraft.com/apps/pdfcraft).

## Edit a named VectorCraft shape and keep it editable

Use the connected VectorCraft MCP tools for an open document. For files on disk, a fresh stdio session can run `vectorcraft-cli mcp --headless --automation-read-root DIR --automation-write-root DIR` with the relevant input and output directories. Discover the tool schemas with MCP `tools/list`. The following tool names and parameters were exercised with VectorCraft 0.24.1.

1. For a file on disk, call `open_file` with its absolute `path`. Run `command_run` with `{"id":"document.find","params":{"name":"Status badge"}}`. Inspect the matches, identify the requested object by name, kind, and layer, then use its returned ID. Resolve multiple plausible matches before editing.
2. Call `doc_inspect` with `{"ids":[ID]}` and capture properties that should survive. For a fill change, call `set_paint` with `{"ids":[ID],"fill":"#45a167"}`, substituting the actual ID and requested color.
3. For an edit confined to the open document, inspect the changed shape in that session and leave saving to the user. For a requested native save, call `save_file` with the destination path. To deliver a separate native copy while preserving the open document’s path, use `export` with `format: "vectorcraft"` and the copy’s path.
4. For a file delivery, reopen the result through an allowed interface with read access to the output. In a fresh headless session, set the read root to the output directory. If using the connected app, record the original active document, open the saved copy in a separate tab, and restore the original after inspection. Look up the shape again and check its fill, dimensions and kind. For a parametric shape, `command_run` with `{"id":"document.node","params":{"id":ID}}` exposes its live shape parameters. If the saved file cannot be read through the required interface, report which properties you verified in the live document and which file checks remain open.

See the [VectorCraft MCP guide](https://github.com/storytold/vectorcraft/blob/v0.24.1/docs/mcp.md).
