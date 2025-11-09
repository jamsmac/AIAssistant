# Bundle Analysis Guide

To inspect the client bundle size and identify heavy dependencies, run the analyzer:

```bash
cd web-ui
npm install
npm run analyze
```

This command wraps the production build with `ANALYZE=true` and opens the interactive bundle report (via `@next/bundle-analyzer`).

## Tips

- Use the left sidebar of the report to find the largest chunks (`reactflow`, `recharts`, `tiptap`, etc.).
- Drill down to individual modules to see what is contributing to bundle size.
- Close other tabs before generating the report; Next stores the static report under `.next/analyze`.
- Re-run after changes to confirm improvements.
