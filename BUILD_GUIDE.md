# Production Build Guide

## Quick Start

### Build for Production

```bash
# Option 1: Using PowerShell script (recommended)
.\scripts\build-frontend.ps1

# Option 2: Using npm directly
cd frontend
npm run build
```

### Serve Production Build

```bash
# Option 1: Via FastAPI (backend serves frontend)
cd backend
uvicorn app.main:app --host 0.0.0.0 --port 8000

# Option 2: Standalone server (testing only)
cd frontend
npm run serve
```

---

## Build Scripts

| Command | Description |
|---------|-------------|
| `npm start` | Development server with hot reload |
| `npm run build` | Standard production build |
| `npm run build:prod` | Optimized build (no source maps) |
| `npm run build:analyze` | Build + bundle size analysis |
| `npm run serve` | Serve production build locally |
| `npm run analyze` | Analyze bundle composition |

---

## Frontend Optimization Features

### 1. Code Splitting
- Vendor code separated from application code
- Library-specific chunks (Radix UI, Recharts)
- Common code extracted automatically
- Runtime chunk isolated for better caching

### 2. Minification
- JavaScript: Terser (production default)
- CSS: CSSNano
- HTML: Built-in minification

### 3. Tree Shaking
- Unused code automatically removed
- `usedExports` optimization
- Side-effects respected

### 4. Compression
- Gzip pre-compression of all JS/CSS
- 30-40% size reduction
- Server can serve `.gz` files directly

---

## Expected Build Sizes

### Development Build
- Total: ~5-10 MB
- Single bundle
- No optimization

### Production Build
- Total: ~800 KB - 1.5 MB (before gzip)
- Main bundle: ~150-250 KB
- Vendor chunk: ~400-600 KB
- Gzipped total: ~250-400 KB

---

## Deployment Checklist

- [ ] Run `npm run build` or `.\scripts\build-frontend.ps1`
- [ ] Verify `frontend/build` directory exists
- [ ] Check bundle sizes (< 500KB per chunk)
- [ ] Test locally with `npm run serve`
- [ ] Verify all routes work
- [ ] Test API integration
- [ ] Check browser console for errors
- [ ] Run Lighthouse audit (target: 90+ score)

---

## Serving Options

### Option 1: FastAPI (Recommended for Demo)

The backend automatically serves the production build:

```bash
cd backend
uvicorn app.main:app --reload
# Frontend available at http://localhost:8000
```

**Features:**
- Single server for API + frontend
- SPA routing support
- Gzip compression
- Production-ready

### Option 2: Standalone (Testing)

```bash
cd frontend
npm run serve
# Available at http://localhost:3000
```

**Use for:**
- Quick local testing
- Frontend-only development

### Option 3: Nginx (Production Deployment)

See `docs/ProductionBuildOptimization.md` for Nginx configuration.

---

## Troubleshooting

### Build Fails

```bash
# Clear cache and reinstall
cd frontend
rm -rf node_modules build
npm install
npm run build
```

### Memory Error

```bash
# Increase Node memory
$env:NODE_OPTIONS="--max-old-space-size=4096"
npm run build
```

### Bundle Too Large

```bash
# Analyze what's taking space
npm run build:analyze
```

Then optimize by:
- Removing unused dependencies
- Implementing lazy loading
- Using lighter alternatives

---

## Performance Targets

| Metric | Target |
|--------|--------|
| Time to Interactive | < 2s |
| First Contentful Paint | < 1s |
| Total Bundle Size | < 1.5 MB |
| Gzipped Size | < 400 KB |
| Lighthouse Score | 90+ |

---

## Next Steps

1. Build the frontend: `npm run build`
2. Test locally: `npm run serve`
3. Deploy via FastAPI or Nginx
4. Monitor performance with Lighthouse
5. Iterate and optimize as needed

---

For detailed documentation, see:
- `docs/ProductionBuildOptimization.md` - Complete guide
- `scripts/build-frontend.ps1` - Build script
- `craco.config.js` - Webpack configuration
