# Database Architecture

## Production Setup (Railway)

This application uses **PostgreSQL only** for production deployment on Railway.

### Files:
- **`database_postgres.py`** ✅ - PostgreSQL implementation (ACTIVE)
- **`db_wrapper.py`** - Factory that returns PostgreSQL instance
- **`database.py`** ⚠️ - SQLite implementation (DEPRECATED - NOT USED)

### Important Rules:

1. ✅ **ALL database changes must be made in `database_postgres.py`**
2. ❌ **Do NOT update `database.py` - it is not used in production**
3. ✅ **Railway requires `DATABASE_URL` environment variable**
4. ✅ **PostgreSQL service must be added to Railway project**

### When Making Database Changes:

#### ✅ DO:
- Update schema in `database_postgres.py` (CREATE TABLE statements)
- Add methods to `PostgreSQLDatabase` class in `database_postgres.py`
- Use PostgreSQL-specific SQL syntax (`SERIAL`, `RETURNING`, `%s` placeholders)
- Test on Railway after deploying

#### ❌ DON'T:
- Update `database.py` - it's deprecated
- Use SQLite-specific syntax (`AUTOINCREMENT`, `?` placeholders)
- Assume changes will work without testing on Railway

### Example: Adding a New Table

```python
# In database_postgres.py, in the _init_schema() method:

cursor.execute('''
    CREATE TABLE IF NOT EXISTS my_new_table (
        id SERIAL PRIMARY KEY,
        name TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
''')
```

### Example: Adding a New Method

```python
# In database_postgres.py, in the PostgreSQLDatabase class:

def get_my_data(self) -> List[Dict]:
    """Get data from my_new_table"""
    with self.get_connection() as conn:
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cursor.execute('SELECT * FROM my_new_table ORDER BY created_at DESC')
        return [dict(row) for row in cursor.fetchall()]
```

### Environment Variables:

**Required:**
- `DATABASE_URL` - PostgreSQL connection string (auto-set by Railway)

**Not Used:**
- `DATABASE_PATH` - SQLite path (deprecated)

### Railway Setup:

1. Go to Railway project dashboard
2. Click "New" → "Database" → "PostgreSQL"
3. Railway automatically sets `DATABASE_URL`
4. Application will use PostgreSQL on next deploy

### Local Testing with PostgreSQL:

If you want to test locally with PostgreSQL:

```bash
# Install PostgreSQL locally
# Create a database
# Set environment variable
export DATABASE_URL=postgresql://user:password@localhost/yad2_monitor

# Run the application
python app.py
```

### Why This Architecture?

- **Single source of truth**: Only one database implementation to maintain
- **Production-ready**: PostgreSQL is required for Railway persistence
- **No confusion**: Clear which file to update
- **Better performance**: PostgreSQL handles concurrent connections better
- **Railway integration**: Seamless integration with Railway's PostgreSQL service
