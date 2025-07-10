# Database Cleanup Scripts

## clean_dev_db.py

A script to clean all collections in the Swayami development database for fresh user testing.

### Usage

1. **Navigate to the backend directory:**
   ```bash
   cd swayami-backend
   ```

2. **Run the cleanup script:**
   ```bash
   python scripts/clean_dev_db.py
   ```

3. **Follow the prompts:**
   - Confirm that you want to delete all data
   - Type 'DELETE' to finalize the operation

### What it cleans

The script will delete all documents from these collections:
- `users` - User accounts and profiles
- `goals` - User goals and objectives
- `tasks` - User tasks and action items
- `journals` - Journal entries and reflections
- `ai_logs` - AI interaction logs
- `sessions` - User session data
- `quotes` - Motivational quotes

### Safety Features

- **Double confirmation** required before deletion
- **Document count** displayed before and after
- **Error handling** for each collection
- **Summary report** of total documents deleted

### ⚠️ Warning

This script will **permanently delete all data** from the database. Use only in development/testing environments.

### Requirements

- Python 3.7+
- MongoDB connection (configured in `.env`)
- Required packages: `motor`, `python-dotenv`

### Example Output

```
==================================================
🧹 SWAYAMI DATABASE CLEANUP SCRIPT
==================================================

⚠️  This will DELETE ALL DATA from the database. Are you sure? (yes/no): yes
🔴 Type 'DELETE' to confirm: DELETE

🧹 Starting database cleanup...
📊 Database: swayami_dev
🔗 Connection: mongodb://localhost:27017

✅ users: Deleted 5 documents
✅ goals: Deleted 12 documents
✅ tasks: Deleted 45 documents
✅ journals: Deleted 8 documents
ℹ️  ai_logs: No documents to delete
ℹ️  sessions: No documents to delete
ℹ️  quotes: No documents to delete

🎉 Database cleanup completed!
📈 Total documents deleted: 70
🗄️  Collections cleaned: 7

✅ Successfully cleaned 70 documents from the database
🆕 The database is now ready for fresh user testing
``` 