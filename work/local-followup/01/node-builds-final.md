# Pi and frontend build checks

All checks below used this worktree's installed dependencies. Product source under `runtime/pi/` and `frontend/` is unchanged from baseline commit `170fac0bc75fcc855897b073337ba218abeb5b7d` (`git diff --quiet` exit 0). No product files were edited for these checks.

## Results

- Node: `/home/amax/.nvm/versions/node/v22.19.0/bin/node`, v22.19.0; npm 10.9.3.
- `cd runtime/pi && npm run typecheck`: passed (`tsc --noEmit`), raw log [`pi-typecheck-final.log`](pi-typecheck-final.log), SHA-256 `19d478f3266cca87481ac6dbc12e9133169f2b34891a02eec2135c458c77a8f9`.
- `cd runtime/pi && npm run build`: passed (`tsc`), raw log [`pi-build-final.log`](pi-build-final.log), SHA-256 `ff4729a2f80025d558533d513d301eb8c500ce7778aad436b926aef4a8ec6d42`.
- `cd frontend && ./node_modules/.bin/tsc --noEmit`: passed with strict TypeScript enabled in `tsconfig.json`; raw log [`frontend-typecheck-final.log`](frontend-typecheck-final.log), SHA-256 `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` (empty stdout/stderr).
- `cd frontend && npm run build`: passed with Vite 8.3.0 in 337 ms; raw log [`frontend-build-final.log`](frontend-build-final.log), SHA-256 `330777250c7c5b6aa977736223ff036010806646ad450c22183637b6aa49f2ef`. Vite emitted its existing forward-compatibility warnings for `__dirname` and a JSON import without import attributes; build completed successfully.

The first Pi typecheck attempt failed because its clean-environment `PATH` omitted `/bin` (`spawn sh ENOENT`). That environment-only attempt is retained in `pi-typecheck-env-attempt-1.log`; the final command included `/usr/bin:/bin` and passed. This is not counted as a source failure.

## Inputs and generated outputs

| Input | SHA-256 |
|---|---|
| `runtime/pi/package.json` | `e10332fe16be1faae439e716dee277b0ade28f81145d41a1ccc8f755f504d9be` |
| `runtime/pi/package-lock.json` | `2700a4b3ac0ea31611e6a9b2bcb58bb9fda53766474aa8b3382f7d5523aad9cd` |
| `frontend/package.json` | `2e6f3ba99dbd8a4d567d2f058699451326aa73e3d95fb6a9e555654a99d4f7f2` |
| `frontend/package-lock.json` | `9b31e7427564ebb34499cf9adddb5eac2986a6913db66d24d868e644d496e7b7` |
| `frontend/tsconfig.json` | `9a1e96d63eaccd5416b2f78ecaccf2b3a27ca71e213fa5859cf5349c66123bf9` |

Build outputs are ignored local artifacts. Final generated bundles included `runtime/pi/dist/general-claim.js` SHA-256 `95b8d7fbcafd4ee179bab17efb446ca73544f4d4fdb8d85a283baa38ffc0eb68` and frontend `dist/assets/index-Dts8QdVP.js` SHA-256 `3c49e724bfad7a3439837887a262ca94e1837abe9081845259c07bd8493e24d4`. The full set of generated output files was hashed during verification; no bundles are tracked as source changes.
