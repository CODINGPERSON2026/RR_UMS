# Database Tables Schema Directory (`database_tables/`)

This directory contains the SQL table definition files for the UMS system.

## 🚀 How Auto-Creation Works

Whenever anyone runs the project (`python app.py` or `python database_schema.py`):
1. The system connects to MySQL and creates the `hrms` database if it doesn't exist yet.
2. It queries `SHOW TABLES` to get existing tables in the database.
3. For any table in this directory that does not yet exist in the database, it automatically executes the `CREATE TABLE IF NOT EXISTS` statement.
4. Foreign key checks are temporarily disabled during execution so tables can be created safely regardless of dependencies.

---

## 🛠️ Adding a New Table (For Developers)

Whenever you create a new table, choose **one** of the methods below:

### Method 1: Drop a `.sql` file here (Recommended)
Create a new file `database_tables/<your_table_name>.sql` with your `CREATE TABLE` query:
```sql
CREATE TABLE IF NOT EXISTS `canteen_inventory` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `item_name` VARCHAR(150) NOT NULL,
  `quantity` INT DEFAULT 0,
  `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```
Commit and push this file to git. When any other team member pulls the code and runs the project, their database will automatically create `canteen_inventory`!

---

### Method 2: Created a table in MySQL Workbench? Auto-export it!
If you created or modified tables directly in MySQL or Workbench, simply run from the terminal:
```bash
python database_schema.py --export
```
This inspects your MySQL database and generates/updates the `.sql` files in this directory automatically. Then just commit and push!

---

### Method 3: Programmatically in Python
In any blueprint or module:
```python
from database_schema import register_table

register_table('canteen_inventory', '''
CREATE TABLE IF NOT EXISTS `canteen_inventory` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `item_name` VARCHAR(150) NOT NULL,
    `quantity` INT DEFAULT 0
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
''')
```

---

## 🔍 Verification Command
To check the status of all tables without starting the web server:
```bash
python database_schema.py
```

