# Database Schema Improvement Documentation

## 1. Audit System Implementation

### 1.1 Base Audit Columns
Every table now includes standard audit columns:
```python
created_at: DateTime  # Record creation timestamp
updated_at: DateTime  # Last modification timestamp
is_active: Boolean   # Soft delete flag
```

### 1.2 Audit Trail Table
```sql
CREATE TABLE audit_log (
    id INTEGER PRIMARY KEY,
    table_name VARCHAR(50) NOT NULL,
    record_id VARCHAR NOT NULL,
    action VARCHAR(10) NOT NULL,
    old_values JSON,
    new_values JSON,
    user_id VARCHAR REFERENCES user_info(user_id),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### Implementation Notes:
- Captures all CRUD operations
- Stores both old and new values for change tracking
- Links changes to specific users
- JSON format allows flexible storage of changed values

## 2. Security Enhancements

### 2.1 User Authentication Improvements
```python
# New fields in user_info
failed_login_attempts: Integer
account_locked_until: DateTime
last_login: DateTime

# Enhanced user_auth
token_expiry: DateTime
```

#### Security Features:
- Account lockout after failed attempts
- Token-based authentication with expiry
- Login attempt tracking
- Session management

### 2.2 Role-Based Access Control
```python
roles = Enum('student', 'instructor', 'admin', name='user_roles')
```

#### Access Control Matrix:
| Role       | Section Access | Assignment Access | Submission Access |
|------------|---------------|-------------------|-------------------|
| student    | Read          | Read              | Read/Write Own    |
| instructor | Read/Write    | Read/Write        | Read/Write All    |
| admin      | Full Access   | Full Access       | Full Access       |

## 3. Data Validation Implementation

### 3.1 Check Constraints
```sql
-- Score validation
CHECK (score >= 0)
CHECK (max_score >= 0)

-- Date validation
CHECK (end_epoch > start_epoch)

-- Email validation
CHECK (email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$')

-- Attempt validation
CHECK (num_attempts >= 0)
```

### 3.2 Unique Constraints
```sql
-- Section uniqueness
UNIQUE (section_code, academic_year, semester)

-- User uniqueness
UNIQUE (email)
UNIQUE (username)
```

## 4. Performance Optimizations

### 4.1 Index Strategy
```sql
-- Composite indexes for common queries
CREATE INDEX idx_submission_user_assn ON subm(user_id, assn_id);
CREATE INDEX idx_assn_date_range ON assn(start_epoch, end_epoch);
CREATE INDEX idx_user_section ON sec_acc(user_id, section_id);
```

### 4.2 Cascading Operations
```sql
-- Example of cascade delete
FOREIGN KEY (user_id) REFERENCES user_info(user_id) ON DELETE CASCADE
```

## 5. Feature Enhancements

### 5.1 Assignment Management
```python
# New assignment fields
assn_type: Enum('homework', 'quiz', 'exam', 'project')
max_score: Float
weight: Float
max_attempts: Integer
```

### 5.2 Submission Tracking
```python
# Enhanced submission tracking
grader_id: ForeignKey
feedback: Text
final_score: Float
```

## 6. Migration Strategy

### 6.1 Pre-Migration Tasks
1. Backup existing database
2. Create temporary tables for data preservation
3. Verify application compatibility

### 6.2 Migration Steps
```sql
-- Step 1: Add new columns with NULL constraint
ALTER TABLE user_info ADD COLUMN role user_roles NULL;

-- Step 2: Add audit columns
ALTER TABLE user_info 
ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
ADD COLUMN is_active BOOLEAN DEFAULT TRUE;

-- Step 3: Create new tables
CREATE TABLE audit_log (...);

-- Step 4: Migrate existing data
UPDATE user_info SET role = 'student' WHERE role IS NULL;

-- Step 5: Add NOT NULL constraints
ALTER TABLE user_info ALTER COLUMN role SET NOT NULL;
```

### 6.3 Post-Migration Tasks
1. Verify data integrity
2. Update application code
3. Create new indexes
4. Test performance
5. Update documentation

## 7. Maintenance Procedures

### 7.1 Regular Maintenance
```sql
-- Vacuum dead tuples
VACUUM ANALYZE table_name;

-- Update statistics
ANALYZE table_name;

-- Check index usage
SELECT schemaname, tablename, indexname, idx_scan, idx_tup_read, idx_tup_fetch 
FROM pg_stat_user_indexes;
```

### 7.2 Monitoring Queries
```sql
-- Monitor table size
SELECT pg_size_pretty(pg_total_relation_size('table_name'));

-- Check index usage
SELECT * FROM pg_stat_user_indexes 
WHERE idx_scan = 0 
AND idx_tup_read = 0;
```

## 8. Application Integration

### 8.1 Connection Management
```python
# Example connection pool configuration
engine = create_engine(
    'postgresql://user:pass@localhost/dbname',
    pool_size=5,
    max_overflow=10,
    pool_timeout=30
)
```

### 8.2 Transaction Management
```python
# Example transaction handling
from sqlalchemy.orm import Session

with Session(engine) as session:
    try:
        session.add(new_record)
        session.commit()
    except:
        session.rollback()
        raise
```

## 9. Backup and Recovery

### 9.1 Backup Strategy
```bash
# Daily backup script
pg_dump dbname > backup_$(date +%Y%m%d).sql

# Automated backup retention
find /backup -name "backup_*.sql" -mtime +30 -delete
```

### 9.2 Recovery Procedures
```bash
# Restore from backup
psql dbname < backup_20240320.sql
```

## 10. Testing Strategy

### 10.1 Unit Tests
```python
def test_user_creation():
    user = User(
        username="test_user",
        email="test@example.com",
        role="student"
    )
    assert user.is_active == True
    assert user.role == "student"
```

### 10.2 Integration Tests
```python
def test_submission_workflow():
    # Create assignment
    assignment = create_assignment()
    
    # Submit solution
    submission = submit_solution(assignment.id)
    
    # Verify constraints
    assert submission.score >= 0
    assert submission.num_attempts >= 0
```
