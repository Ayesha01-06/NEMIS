# Quick Start Guide for Windows

If you're having issues with `setup.py`, use these simpler steps:

## Step 1: Create the Database

Open **Command Prompt** or **PowerShell** as Administrator and run:

```bash
psql -U postgres
```

Then in the PostgreSQL prompt, type:

```sql
CREATE DATABASE NEMIS;
\q
```

## Step 2: Load the Schema

**Option A - Using the fix script (Recommended):**
```bash
python fix_database.py
```

**Option B - Manual method:**
```bash
psql -U postgres -d NEMIS -f schema.sql
```

If you get an error about psql not being found, add PostgreSQL to your PATH:
1. Find your PostgreSQL bin folder (usually `C:\Program Files\PostgreSQL\15\bin`)
2. Add it to Windows PATH environment variable
3. Restart Command Prompt

## Step 3: Start the Application

```bash
python nemis.py
```

## Step 4: Access the Interface

Open your browser to:
```
http://127.0.0.1:5000
```

**Login credentials:**
- Admin: `AD123456`
- Election Officer: `EO123456`

---

## Troubleshooting Common Errors

### "psql: command not found"
- PostgreSQL bin folder is not in your PATH
- Solution: Use full path like `"C:\Program Files\PostgreSQL\15\bin\psql.exe"`

### "Connection refused"
- PostgreSQL is not running
- Solution: Start it from Windows Services (search for "Services" → PostgreSQL)

### "database NEMIS already exists"
- Drop and recreate it:
  ```sql
  psql -U postgres
  DROP DATABASE NEMIS;
  CREATE DATABASE NEMIS;
  \q
  ```

### "permission denied" or "authentication failed"
- Check your PostgreSQL password
- Edit `db.py` and update the password on line 16

### Exit status 2 when loading schema
- Use `fix_database.py` instead of psql command
- Or check if the file path has spaces (use quotes)

---

## Need Help?

If none of these work, share the exact error message you're getting.
