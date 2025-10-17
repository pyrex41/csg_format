# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a FastAPI-based Medicare Supplement insurance application formatting service. It retrieves insurance applications from a Turso database, formats them according to different carrier specifications (UnitedHealthcare, Aetna, Allstate, Chubb/ACE), and provides REST APIs for accessing formatted data.

## Development Commands

### Running the Application
```bash
# Start the FastAPI server with auto-reload
uvicorn main:app --reload

# Start on specific port
uvicorn main:app --reload --port 8000
```

### Python Environment
```bash
# Activate virtual environment
source .venv/bin/activate

# Install dependencies (using uv)
uv pip install -r pyproject.toml
```

## Architecture

### Core Components

**main.py**: FastAPI application entry point that registers three router groups:
- `/api/*` - CSG routes (token management)
- `/api/db/*` - Database CRUD operations
- `/api/formatter/*` - Application formatting endpoints

**application_formatter.py**: The heart of the application. Contains carrier-specific formatting functions:
- `format_uhc_application()` - UnitedHealthcare formatting
- `format_aetna_application()` - Aetna formatting
- `format_allstate_application()` - Allstate formatting
- `format_ace_application()` - Chubb/ACE formatting
- `format_application()` - Main dispatcher that routes to correct formatter based on carrier

Each formatter transforms raw application data into carrier-specific JSON schemas with sections for:
- Applicant information
- Medicare information
- Producer (agent) information
- Payment details
- Existing coverage
- Health history/medication information (carrier-dependent)

**routes/formatter_routes.py**: Primary API endpoint at `/api/applications/{application_id}/formatted` that:
1. Retrieves application from database
2. Decodes URL-encoded values
3. Maps NAIC codes to carrier names
4. Calls the appropriate formatter
5. Optionally skips medication or producer sections via query params

**database.py**: Turso (libSQL) database connection using environment variables:
- `TURSO_DATABASE_URL`
- `TURSO_AUTH_TOKEN`

**models.py**: SQLAlchemy ORM models:
- `Application` - Main application data with JSON fields for `data`, `schema`, `originalSchema`
- `User` - User accounts (temporary/anonymous flags)
- `CSGApplication` - CSG submission tracking
- `Onboarding` - User onboarding data (contains medicare_status)
- `CSGToken` - Token management
- `Broker` - Broker authentication

### Key Data Flows

1. **Application Retrieval**: Database query joins `applications`, `user`, and `onboarding` tables to get complete context
2. **NAIC to Carrier Mapping**: Maps insurance company NAIC codes to carrier names (defined in `formatter_routes.py:54-66`)
3. **Medicare Date Calculations**: `calculate_medicare_dates()` determines eligibility windows based on turning 65 and Part A/B enrollment
4. **Plan Switch Reasoning**: `get_plan_switch_reason()` determines why applicant is switching plans based on old vs new plan types
5. **ZIP Code Lookup**: Uses `zipData.json` (5MB+ file) to resolve city/state from ZIP codes
6. **Company NAIC Lookup**: `get_naic_code()` uses fuzzy matching (rapidfuzz) against `supp_companies_full.json` to find company NAIC codes
7. **Routing Number Lookup**: `routing_number.py` calls external API to resolve bank names from routing numbers

### Producer Configuration

Producer (insurance agent) data is stored in `producer_config.json`. Currently configured for two producers (Josh and Garrett). The formatter loads Garrett's data by default. Each producer has:
- Contact information
- NPN (National Producer Number)
- Writing numbers for each carrier

## Important Implementation Details

### Date Handling
- All dates are converted from ISO format (with time) to date-only format (YYYY-MM-DD)
- `format_date()` strips time components from ISO strings
- Medicare eligibility windows are calculated relative to the applicant's 65th birthday

### URL Decoding
The `decode_values()` function recursively decodes URL-encoded strings (containing `%` characters) throughout the application data structure.

### Medication Formatting
Medication data is parsed differently per carrier:
- **Aetna**: Splits drug names into name + diagnosis, stores in `prescribed_medications` dict
- **Allstate**: Additionally extracts dosage and frequency, handles "/" to ";" conversion in dosage

### Empty Value Handling
- The formatter removes `None` and empty dict values recursively via `remove_empty_values()`
- The API endpoint replaces empty strings and `None` with `"NA"` via `replace_empty_values()`

### Existing Coverage Logic
Based on `onboarding_data.medicare_status`:
- `"advantage-plan"`: Sets up Medicare Advantage replacement fields
- `"supplemental-plan"`: Sets up Medicare Supplement replacement with NAIC lookup
- `"no-plan"`: Sets up other health insurance replacement

## Authentication System

The application supports **two authentication methods**:

### 1. Session-Based Auth (Web UI)
For interactive web browser usage:
- **Login Flow**: Users authenticate at `/login.html` with username/password
- **Token Storage**: Session tokens stored in browser localStorage
- **Expiration**: Tokens expire after 24 hours
- **Storage**: In-memory (not persisted across server restarts)

**Default Credentials** (CHANGE IN PRODUCTION):
- Username: `admin`
- Password: `changeme`

### 2. Static API Key (Frontend/Production)
For programmatic API access and frontend deployments:
- **Permanent**: Never expires
- **Survives**: Server restarts
- **Usage**: Include in `Authorization: Bearer {API_KEY}` header
- **Generation**: Run `uv run python generate_api_key.py`

**Configuration** (`.env`):
```bash
# Session-based auth
ADMIN_USERNAME=your_username
ADMIN_PASSWORD=your_password

# Static API key (permanent)
API_KEY=your_generated_api_key_here
```

**Frontend Setup**:
```bash
# In your frontend .env
VITE_API_TOKEN=Dk9JGiu1p1fJx5njWWEPxZ6bGB3y-BikII4hTJPqF0A
```

**API Usage**:
```bash
curl -H "Authorization: Bearer Dk9JGiu1p1fJx5njWWEPxZ6bGB3y-BikII4hTJPqF0A" \
  http://localhost:8001/api/db/applications
```

## Environment Variables Required

```
# Turso Database
TURSO_DATABASE_URL=
TURSO_AUTH_TOKEN=

# CSG API Authentication
CSG_API_URL=
CSG_EMAIL=
CSG_PASSWORD=
CSG_API_KEY=

# Application Authentication
ADMIN_USERNAME=admin
ADMIN_PASSWORD=changeme
API_KEY=  # Static API key for permanent frontend access
```

## Data Files

- `zipData.json` - ZIP code to city/state mapping (5.3MB)
- `supp_companies_full.json` - Insurance company name to NAIC mapping
- `producer_config.json` - Producer/agent information and writing numbers

## Testing Considerations

- `grid.py` is a standalone performance testing script (flood fill algorithm) - not part of the main application
- When testing formatters, note that each carrier has different required fields and validation rules
- The `/api/applications/{id}/formatted` endpoint accepts `skip_medication` and `skip_producer` query parameters for flexibility
