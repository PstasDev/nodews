# Quick Fix: Static Files 404 Error

## What Was Wrong

**Symptom**: Intermittent 404 errors on `/static/css/bufe.css` and other static files in production (ws.szlg.info)

**Root Cause**: Using `CompressedManifestStaticFilesStorage` which requires a manifest file that wasn't being consistently generated/maintained during deployments.

## What Was Changed

### 1. settings.py - Changed Storage Backend
```python
# OLD (caused 404s):
"staticfiles": {
    "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
}

# NEW (reliable):
"staticfiles": {
    "BACKEND": "whitenoise.storage.CompressedStaticFilesStorage",
}
```

**Benefits**:
- ✅ No manifest file dependency
- ✅ Still compresses files (gzip/brotli)
- ✅ No more intermittent 404s
- ✅ Simpler deployment

### 2. base.html - Removed Workaround Script
Removed the `reloadStaticOn404()` JavaScript function that was constantly checking for and trying to reload 404'd files. This was a band-aid for the root cause.

### 3. Added Deployment Scripts
- **deploy.sh** - Linux/production deployment
- **deploy.bat** - Windows testing
- **DEPLOYMENT_STATIC_FILES.md** - Complete guide

## How to Deploy (Production)

```bash
# On your production server (ws.szlg.info)
cd /path/to/nodews
bash deploy.sh
```

Or manually:
```bash
git pull origin main
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --noinput --clear  # ← CRITICAL!
sudo systemctl restart daphne  # or your service
```

## How to Test Locally (Windows)

```cmd
deploy.bat
```

Or manually:
```cmd
git pull origin main
venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --noinput --clear
python manage.py runserver
```

## Verify It Works

1. **Check collected files exist**:
   ```bash
   ls staticfiles/css/bufe.css
   ls staticfiles/js/bufe.js
   ```

2. **Check in browser** (F12 → Network):
   - Request: `https://ws.szlg.info/static/css/bufe.css`
   - Response: `200 OK` (not 404!)
   - Header: `Content-Encoding: gzip` (compression working)

3. **Check logs** (production):
   ```bash
   sudo journalctl -u daphne -n 50
   ```

## Why collectstatic is Required

- Django dev server (`runserver`) serves static files automatically from `static/` folders
- **Production servers** (Daphne, Gunicorn, etc.) do NOT serve static files automatically
- `collectstatic` copies all static files → `staticfiles/` directory
- WhiteNoise middleware serves files from `staticfiles/` with compression/caching
- **Without collectstatic**: 404 errors!

## Key Files Modified

1. `nodews_project/settings.py` - Changed storage backend
2. `bufe/templates/bufe/base.html` - Removed workaround script
3. `.gitignore` - Added `staticfiles/` (generated directory)
4. `deploy.sh` & `deploy.bat` - New deployment scripts
5. `DEPLOYMENT_STATIC_FILES.md` - Detailed documentation

## Need Help?

See `DEPLOYMENT_STATIC_FILES.md` for comprehensive troubleshooting guide.

## Status: ✅ FIXED

The intermittent static file 404 errors should now be resolved. Remember to run `collectstatic` on every deployment!
