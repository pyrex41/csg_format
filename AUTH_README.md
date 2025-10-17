# Authentication Setup

## Quick Start

Your permanent API key has been generated and added to `.env`:

```
API_KEY=Dk9JGiu1p1fJx5njWWEPxZ6bGB3y-BikII4hTJPqF0A
```

## For Your Frontend Deployment

Add this to your frontend `.env` file:

```bash
VITE_API_TOKEN=Dk9JGiu1p1fJx5njWWEPxZ6bGB3y-BikII4hTJPqF0A
```

Then in your frontend code:

```javascript
// Example fetch request
const response = await fetch('https://your-api.com/api/db/applications', {
  headers: {
    'Authorization': `Bearer ${import.meta.env.VITE_API_TOKEN}`
  }
});
```

## Two Authentication Methods

### 1. Static API Key (Recommended for Frontend)
✅ **NEVER expires**
✅ **Survives server restarts**
✅ **Perfect for production deployments**

```bash
Authorization: Bearer Dk9JGiu1p1fJx5njWWEPxZ6bGB3y-BikII4hTJPqF0A
```

### 2. Session Token (For Web UI)
- Login at `/login.html` with username/password
- Get a 24-hour token
- Stored in browser localStorage
- Good for interactive web use

## Testing Your API Key

```bash
# Test the applications endpoint
curl -H "Authorization: Bearer Dk9JGiu1p1fJx5njWWEPxZ6bGB3y-BikII4hTJPqF0A" \
  http://localhost:8001/api/db/applications?page=1&limit=10

# Test with search
curl -H "Authorization: Bearer Dk9JGiu1p1fJx5njWWEPxZ6bGB3y-BikII4hTJPqF0A" \
  "http://localhost:8001/api/db/applications?search=john"
```

## Security Notes

⚠️ **IMPORTANT:**
- Store API keys in environment variables, NOT in code
- Never commit `.env` to git
- Regenerate API key if compromised: `uv run python generate_api_key.py`
- Update both backend `.env` and frontend `.env` with the new key

## Regenerating the API Key

If you need a new API key:

```bash
# Generate a new key
uv run python generate_api_key.py

# Update backend .env
API_KEY=new_key_here

# Update frontend .env
VITE_API_TOKEN=new_key_here

# Restart your backend server
```

## Deployment Checklist

### Backend
- [ ] Set `API_KEY` in production environment variables
- [ ] Set `ADMIN_USERNAME` and `ADMIN_PASSWORD` for web UI
- [ ] Ensure `.env` is in `.gitignore`

### Frontend
- [ ] Set `VITE_API_TOKEN` in production environment variables
- [ ] Configure all API calls to include Authorization header
- [ ] Test endpoints before deploying

## API Endpoints That Require Auth

All endpoints under:
- `/api/db/*` - Database operations
- `/api/formatter/*` - Application formatting
- `/api/*` - CSG token operations

Public endpoints (no auth required):
- `/api/auth/login` - Login endpoint
- `/login.html` - Login page
- `/` - Applications browser (redirects to login if not authenticated)
