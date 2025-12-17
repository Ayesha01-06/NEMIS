# 🚀 NEMIS Quick Start Guide - COMPLETE SETUP

## ⚡ FASTEST SETUP (3 Steps)

### **Step 1: Set Your PostgreSQL Password**

Create a `.env` file in the NEMIS folder:

**Windows PowerShell:**
```powershell
echo DB_PASSWORD=your_postgresql_password > .env
```

**Replace `your_postgresql_password` with your actual PostgreSQL password!**

### **Step 2: Run Setup**

```bash
python setup.py
```

When asked questions:
- "Drop and recreate?" → **yes**
- "Load sample data?" → **yes** (optional)
- "Continue anyway?" → **yes**

### **Step 3: Start Application**

```bash
python nemis.py
```

Open browser: **http://127.0.0.1:5000**

Login: **AD123456** or **EO123456**

---

## 🔧 TROUBLESHOOTING

### ❌ "Password authentication failed"

**PROBLEM:** PostgreSQL password is wrong

**FIX:** Edit `.env` file with correct password:
```
DB_PASSWORD=your_real_password
```

Or edit `db.py` line 18 directly.

**Don't know your password?** Reset it:
```bash
psql -U postgres
ALTER USER postgres PASSWORD 'newpassword';
\q
```

---

### ❌ "Database NEMIS does not exist"

**FIX:**
```bash
psql -U postgres -c "CREATE DATABASE \"NEMIS\";"
psql -U postgres -d NEMIS -f schema.sql
```

---

### ❌ "Connection refused" (Port 5432)

**PROBLEM:** PostgreSQL is not running

**FIX:**
- **Windows:** Open Services → Start "postgresql-x64-18"
- **Linux:** `sudo systemctl start postgresql`
- **Mac:** `brew services start postgresql`

---

### ❌ "Port 5000 already in use"

**FIX:** Use different port:
```bash
set PORT=8000
python nemis.py
```
Then use: http://127.0.0.1:8000

---

### ❌ "No module named 'flask'"

**FIX:**
```bash
pip install flask werkzeug psycopg2-binary flask-wtf
```

---

### ❌ Duplicate NEMIS-FINAL folder

**FIX:**
```bash
Remove-Item -Recurse -Force NEMIS-FINAL
```

---

## 📁 CORRECT FILE STRUCTURE

```
NEMIS/
├── .env (your password - create this!)
├── .env.example
├── .gitignore
├── controllers/
│   ├── admin.py
│   ├── auth.py
│   └── voter.py
├── static/
│   ├── css/
│   ├── js/
│   └── images/
├── templates/
│   └── (all .html files)
├── db.py
├── nemis.py
├── schema.sql
├── setup.py
└── requirements.txt
```

**NO** NEMIS-FINAL subdirectory!

---

## ✅ VERIFY EVERYTHING WORKS

### Test Database Connection:
```bash
python db.py
```

Should show: ✓ Database connection successful!

### Test Application:
```bash
python nemis.py
```

Should show:
```
============================================================
NEMIS - National Election Management Information System
============================================================
Running in DEBUG mode
Server: http://127.0.0.1:5000
```

### Test Login:
1. Open: http://127.0.0.1:5000
2. Enter CNIE: **AD123456**
3. Click Login
4. Should see: Admin Dashboard

---

## 🎯 DEFAULT CREDENTIALS

| Role | CNIE | Description |
|------|------|-------------|
| Admin | AD123456 | Full system access |
| Election Officer | EO123456 | Full system access |

---

## 🆘 STILL HAVING ISSUES?

1. **Check PostgreSQL is running:**
   ```bash
   psql -U postgres -c "SELECT version();"
   ```

2. **Verify database exists:**
   ```bash
   psql -U postgres -c "\l" | findstr NEMIS
   ```

3. **Test connection manually:**
   ```bash
   python db.py
   ```

4. **Check Python version (need 3.8+):**
   ```bash
   python --version
   ```

5. **Share the error message** if none of these help!

---

## 🎉 QUICK COMMANDS REFERENCE

```bash
# Complete setup from scratch
python setup.py

# Just start the app
python nemis.py

# Test database only
python db.py

# Install dependencies only
pip install -r requirements.txt

# Reset database
psql -U postgres -c "DROP DATABASE \"NEMIS\";"
psql -U postgres -c "CREATE DATABASE \"NEMIS\";"
psql -U postgres -d NEMIS -f schema.sql
```

---

**That's it! Your NEMIS system should be running now.** 🚀
