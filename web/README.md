# DMO Web UI

Streamlit-based web interface for the Daily Methods of Operation (DMO) tracking system.

## Overview

This package provides a simple, Python-based web UI for managing and tracking your DMOs. It connects to the DMO FastAPI backend and provides an intuitive interface for:

- Daily completion tracking
- DMO and activity management
- Monthly reports and statistics

## Prerequisites

The web UI requires the **DMO API** to be running. Make sure you start it first:

```bash
# In a separate terminal, from workspace root
uv run uvicorn dmo_api.main:app --reload --host 0.0.0.0 --port 8000
```

## Installation

From the workspace root:

```bash
# Install all workspace dependencies
uv sync --all-packages
```

## Running the Web UI

From the workspace root:

```bash
uv run streamlit run web/src/dmo_web/app.py
```

The app will automatically open in your browser at:
- **http://localhost:8501**

## Features

### 📅 Today's Dashboard

The main page showing all your active DMOs for today:

- **Quick completion tracking** - Toggle checkboxes to mark DMOs complete/incomplete
- **Activity lists** - View activities for each DMO as a reference checklist
- **Auto-save** - Changes are saved immediately when you toggle completion
- **Clean layout** - Simple, distraction-free interface

### 📋 Manage DMOs

Complete DMO and activity management:

**DMO Management:**
- View all DMOs (active and inactive)
- Create new DMOs with description and timezone
- Activate/deactivate DMOs
- Delete DMOs (with all associated data)

**Activity Management:**
- View activities for each DMO
- Add new activities to any DMO
- Delete activities
- Activities are displayed as an ordered checklist

### 📊 Reports & Statistics

Visualize your progress and consistency:

- **Monthly reports** - Select any month to view completion data
- **Summary statistics** - Total days, completed days, completion rate
- **Streak tracking** - Current streak and longest streak
- **Calendar view** - Day-by-day completion status
- **Trend charts** - Visual representation of completion patterns

## Configuration

### API URL

By default, the web UI connects to `http://localhost:8000`. To use a different API server:

```bash
export DMO_API_URL=http://your-server:8000
uv run streamlit run web/src/dmo_web/app.py
```

## Usage Examples

### Daily Workflow

1. **Start your day:**
   - Open the "Today" page
   - Review your active DMOs
   - Check the activities for each DMO

2. **Track completion:**
   - Toggle the checkbox next to each DMO as you complete it
   - Add notes if needed (future feature)

3. **Review progress:**
   - Check the "Reports" page to see your monthly stats
   - Monitor your streaks and completion rates

### Managing DMOs

1. **Create a new DMO:**
   ```
   Go to "Manage DMOs" → "Create New" tab
   - Name: "Morning Routine"
   - Description: "Daily morning habits"
   - Activities: "Meditation", "Exercise", "Journaling"
   → Click "Create DMO"
   ```

2. **Add activities to existing DMO:**
   ```
   Go to "Manage DMOs" → "All DMOs" tab
   → Expand a DMO
   → Enter activity name
   → Click "Add"
   ```

3. **Deactivate a DMO:**
   ```
   Go to "Manage DMOs" → "All DMOs" tab
   → Click "Deactivate" next to the DMO
   ```

### Viewing Reports

1. **Current month report:**
   ```
   Go to "Reports" page
   → View statistics for all active DMOs
   → Check completion calendar and trends
   ```

2. **Previous month report:**
   ```
   Go to "Reports" page
   → Use the date picker to select a past month
   → View historical data and trends
   ```

## Screenshots

### Today's Dashboard
```
📅 Today's DMOs
Wednesday, January 03, 2026

✅ Morning Routine
   Activities: Meditation, Exercise, Journaling

⬜ Evening Review
   Activities: Reflect, Plan Tomorrow
```

### Reports Page
```
📊 Reports & Statistics

Morning Routine
━━━━━━━━━━━━━━━━━━━━━
Total Days: 31    Completed: 28 (90.3%)    Current Streak: 5    Longest: 12

Completion Calendar:
Date       | Completed | Note
2026-01-01 | ✅        | Great start!
2026-01-02 | ✅        |
...
```

## Troubleshooting

### "Failed to load DMOs: Connection error"

The API server is not running. Start it first:

```bash
uv run uvicorn dmo_api.main:app --reload
```

### "No active DMOs found"

You haven't created any DMOs yet. Go to "Manage DMOs" → "Create New" to add your first DMO.

### Port 8501 already in use

Kill the existing Streamlit process or use a different port:

```bash
uv run streamlit run web/src/dmo_web/app.py --server.port 8502
```

## Development

### Running with auto-reload

Streamlit automatically reloads when you save changes to the code:

```bash
uv run streamlit run web/src/dmo_web/app.py
```

### Project Structure

```
web/
├── src/
│   └── dmo_web/
│       ├── __init__.py
│       ├── app.py          # Main Streamlit application
│       └── api_client.py   # API wrapper functions
├── pyproject.toml          # Dependencies
└── README.md
```

### Key Technologies

- **Streamlit** - Web framework
- **httpx** - HTTP client for API calls
- **pandas** - Data manipulation for reports

## Customization

### Styling

Edit the CSS in `app.py` (around line 18) to customize colors, fonts, and spacing:

```python
st.markdown(
    """
    <style>
    .main-header {
        font-size: 2.5rem;  /* Adjust header size */
        color: #your-color; /* Change color */
    }
    </style>
    """,
    unsafe_allow_html=True,
)
```

### Adding Features

The modular structure makes it easy to add new pages or features:

1. Add a new function in `app.py` (e.g., `show_custom_page()`)
2. Add it to the sidebar navigation
3. Call it from the main router

## Performance Tips

- The app caches API responses automatically
- Use the "Show inactive DMOs" checkbox sparingly (reduces API calls)
- For large date ranges, reports may take a few seconds to load

## Integration with CLI

The web UI and CLI both use the same database (`~/.dmo/dmo.db`), so:

- ✅ Changes in the web UI are immediately visible in the CLI
- ✅ DMOs created via CLI appear in the web UI
- ✅ Completion tracking is synchronized

Example workflow:
```bash
# Create a DMO via CLI
uv run dmo create "Morning Routine" -a "Meditation"

# Mark it complete via web UI
# (Open http://localhost:8501 and toggle checkbox)

# View report via CLI
uv run dmo report --year 2026 --month 1
```

## License

Same as DMO-Core
