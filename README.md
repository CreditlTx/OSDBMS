# Secure Database Transaction System with Deadlock and Attack Detection

## 1. Project Title

**Secure Database Transaction System with Deadlock and Attack Detection**

An educational project demonstrating the intersection of Operating Systems, Database Management Systems, and Security concepts through a unified, interactive system.

---

## 2. Problem Statement

Modern database systems must handle multiple concurrent transactions safely while protecting against both system-level issues (deadlocks) and security threats (unauthorized access, SQL injection). This project builds a simplified but functional system that demonstrates these challenges and their solutions.

---

## 3. Objectives

1. Execute concurrent database transactions using Python threads
2. Implement resource locking with Strict Two-Phase Locking (Strict 2PL)
3. Detect deadlocks using a Wait-For Graph with DFS cycle detection
4. Recover from deadlocks via victim selection and transaction rollback
5. Detect suspicious/unauthorized activity using rule-based security checks
6. Maintain a comprehensive security audit log
7. Visualize everything through an interactive web dashboard

---

## 4. Why OS and DBMS are Connected

Operating Systems and Database Management Systems share fundamental concepts:

| OS Concept | DBMS Equivalent | This Project |
|---|---|---|
| Threads | Concurrent transactions | Each transaction = 1 thread |
| Mutex/Lock | Database locks | Lock Manager with SHARED/EXCLUSIVE locks |
| Critical section | Serializable access | Protected lock table and transaction registry |
| Deadlock | Transaction deadlock | Wait-For Graph cycle detection |
| Process state (Ready/Running/Blocked) | Transaction state | RUNNING/WAITING/BLOCKED/COMMITTED/ABORTED |
| Semaphore | Concurrency control | Limits max concurrent transactions |
| Wait/Signal | Lock wait/release | Condition variables for lock availability |

A DBMS is essentially a specialized application that uses OS primitives (threads, locks, conditions) to provide safe concurrent access to shared data.

---

## 5. System Architecture

```
Flask Dashboard (app.py)
        |
    Simulator (simulator.py) ---- 3 Scenarios
        |
    Transaction Manager (transaction.py)
        |           |              |
   Lock Manager   Security     Deadlock Detector
(lock_manager.py) (security.py) (deadlock_detector.py)
        |
    SQLite Database (database.py)
        |
    database/database.db
```

---

## 6. Technologies Used

| Technology | Purpose |
|---|---|
| Python 3.x | Core programming language |
| `threading` module | OS concurrency (Thread, Lock, Condition, Semaphore) |
| `sqlite3` module | Lightweight relational database |
| Flask | Web dashboard framework |
| HTML/CSS/JavaScript | Dashboard UI (no frameworks) |

**No** React, Node.js, SocketIO, ML libraries, or cloud services are used.

---

## 7. Database Schema

### ERD (Entity-Relationship)

```
users (1) -----> (*) accounts
  |                    |
  |                    |
  (*) security_logs   (*) transactions
```

### Tables

**users**
| Column | Type | Constraints |
|---|---|---|
| id | INTEGER | PRIMARY KEY AUTOINCREMENT |
| name | TEXT | NOT NULL |
| role | TEXT | CHECK(IN 'customer','admin','system') |
| created_at | TEXT | DEFAULT datetime('now') |

**accounts**
| Column | Type | Constraints |
|---|---|---|
| id | INTEGER | PRIMARY KEY AUTOINCREMENT |
| user_id | INTEGER | FOREIGN KEY -> users(id) |
| account_type | TEXT | CHECK(IN 'savings','current','system') |
| balance | REAL | CHECK(balance >= 0) |

**transactions**
| Column | Type | Constraints |
|---|---|---|
| id | INTEGER | PRIMARY KEY AUTOINCREMENT |
| txn_id | TEXT | NOT NULL |
| operation | TEXT | NOT NULL |
| source_acc_id | INTEGER | FOREIGN KEY -> accounts(id) |
| dest_acc_id | INTEGER | FOREIGN KEY -> accounts(id) |
| amount | REAL | |
| status | TEXT | CHECK(IN 'PENDING','COMMITTED','ABORTED','ROLLED_BACK') |
| timestamp | TEXT | DEFAULT datetime('now') |

**security_logs**
| Column | Type | Constraints |
|---|---|---|
| id | INTEGER | PRIMARY KEY AUTOINCREMENT |
| timestamp | TEXT | DEFAULT datetime('now') |
| user_id | INTEGER | |
| txn_id | TEXT | |
| operation | TEXT | NOT NULL |
| resource | TEXT | |
| result | TEXT | CHECK(IN 'ALLOWED','BLOCKED','FLAGGED','REJECTED') |
| event_type | TEXT | CHECK(IN multiple security event types) |
| reason | TEXT | |

### Seed Data (Initial State)

| Account | Owner | Type | Balance |
|---|---|---|---|
| 1 | Alice | savings | Rs.10,000 |
| 2 | Bob | savings | Rs.10,000 |
| 3 | Charlie | current | Rs.10,000 |
| 4 | Admin | system | Rs.50,000 (restricted) |

**Total: Rs.80,000** (conserved across all operations)

---

## 8. OS Concepts Used

### 8.1 Threads
Each transaction runs in its own `threading.Thread`. This simulates concurrent database access by multiple users.

### 8.2 Mutex (threading.Lock)
The transaction registry and lock table are shared data structures. A mutex protects them from race conditions when multiple threads access them simultaneously.

### 8.3 Condition Variables (threading.Condition)
When a transaction can't get a lock, it uses `Condition.wait()` to sleep efficiently. When a lock is released, `Condition.notify_all()` wakes waiting threads.

### 8.4 Semaphore (threading.Semaphore)
A counting semaphore limits the maximum number of concurrent transactions (MAX_CONCURRENT = 5).

### 8.5 Critical Section
Code regions where shared data (lock table, transaction registry) is modified are clearly marked as critical sections, protected by mutexes.

### 8.6 Deadlock
Demonstrated via Scenario 2: two transactions each hold a resource the other needs, creating a circular wait.

---

## 9. DBMS Concepts Used

### 9.1 Transactions
Each Transaction object represents a database transaction with BEGIN, operations, COMMIT/ROLLBACK lifecycle.

### 9.2 ACID Properties

| Property | How Demonstrated |
|---|---|
| **Atomicity** | Transfer = debit + credit. If either fails, both are rolled back using the undo log. |
| **Consistency** | CHECK constraint prevents negative balances. Total money conserved. |
| **Isolation** | Strict 2PL ensures transactions don't see uncommitted changes. |
| **Durability** | After COMMIT, changes persist in SQLite database file. |

### 9.3 Concurrency Control
Strict 2PL ensures serializability of concurrent transactions.

### 9.4 Recovery
Undo-log based rollback restores original values when a transaction is aborted.

---

## 10. Security Concepts Used

### Rule-Based Detection

| Rule | Trigger | Action |
|---|---|---|
| Repeated failures | 3+ failures in 60 seconds | Block user + log |
| Unauthorized access | Accessing another user's account | Block + log |
| Rate limiting | 10+ requests in 30 seconds | Block + log |
| SQL injection | Detects common injection patterns | Reject + log |
| Restricted records | Modifying system/admin accounts | Block + log |

### Defense in Depth
- **Primary defense**: Parameterized SQL queries (? placeholders)
- **Additional layer**: Input pattern detection
- **Monitoring**: Audit logging of all security events

---

## 11. Strict 2PL Explanation

**Two-Phase Locking** has two phases:

1. **Growing Phase**: Transaction acquires locks as needed. No locks released.
2. **Shrinking Phase**: Transaction releases locks. No new locks acquired.

**Strict 2PL** modifies this: the shrinking phase is delayed until COMMIT or ROLLBACK. This prevents:
- **Dirty reads**: T2 reading T1's uncommitted changes
- **Cascading rollbacks**: T2 depending on T1's data that gets rolled back

### Lock Compatibility Matrix

| | SHARED | EXCLUSIVE |
|---|---|---|
| **SHARED** | GRANT | WAIT |
| **EXCLUSIVE** | WAIT | WAIT |

---

## 12. Wait-For Graph Explanation

A **Wait-For Graph** is a directed graph where:
- **Nodes** = Transaction IDs
- **Edges** = "waits for" relationships

If T1 is waiting for a resource held by T2:
```
T1 --> T2  ("T1 waits for T2")
```

A **cycle** in this graph indicates a **deadlock**:
```
T1 --> T2 --> T1  (circular wait = DEADLOCK)
```

---

## 13. Deadlock Detection Algorithm

**DFS-based cycle detection:**

```
function detectCycle(graph):
    for each unvisited node:
        run DFS from node
        if we visit a node already in current DFS path:
            CYCLE FOUND → return cycle path
    return NO CYCLE
```

Time complexity: O(V + E) where V = transactions, E = wait-for edges.

---

## 14. Deadlock Recovery Process

1. **Detect** the cycle in the Wait-For Graph
2. **Select victim**: youngest transaction (latest start_time)
3. **Abort** the victim (set abort flag)
4. **Rollback** the victim's changes using undo log
5. **Release** the victim's locks
6. **Signal** waiting threads via `Condition.notify_all()`
7. **Log** the deadlock event in security logs
8. Surviving transaction **continues** and commits

---

## 15. Attack Detection Rules

1. **SQL Injection Detection**: Regex patterns for `OR 1=1`, `; DROP TABLE`, `UNION SELECT`, etc.
2. **Unauthorized Access**: User attempting to modify another user's resources
3. **Rate Limiting**: Sliding window counter per user (10 requests / 30 seconds)
4. **Restricted Records**: System/admin accounts (Account 4) are protected
5. **Repeated Failures**: 3+ failures in 60 seconds triggers auto-block

---

## 16. Example Scenarios

### Scenario 1: Normal Execution
- T1: Transfer Rs.1000 (Alice → Charlie)
- T2: Transfer Rs.500 (Bob → Charlie)
- **Result**: Both COMMIT. Balances: 9000, 9500, 11500, 50000. Total: 80000.

### Scenario 2: Deadlock
- T1: Lock Account 1 → Request Account 2
- T2: Lock Account 2 → Request Account 1
- **Result**: Cycle detected. T2 (younger) aborted. T1 commits.

### Scenario 3: Attack Detection
- SQL injection attempts → BLOCKED
- Unauthorized access → BLOCKED
- Restricted account modification → BLOCKED
- Rate limit exceeded → BLOCKED
- Legitimate transaction → ALLOWED

---

## 17. Dashboard

The web dashboard has 4 main panels:

1. **Transaction Panel**: Shows all transactions with ID, thread, state (color-coded), current operation, and locks held
2. **Deadlock Panel**: Wait-For Graph visualization, cycle detection status, victim info
3. **Database Panel**: Live account balances, recent transaction log
4. **Security Panel**: Alert statistics, blocked users, security event log

Plus scenario control buttons and a console log.

---

## 18. How to Install

### Prerequisites
- Python 3.8 or higher
- pip (Python package manager)

### Steps

```bash
# 1. Navigate to the project directory
cd OSDBMS

# 2. (Recommended) Create a virtual environment
python -m venv venv
venv\Scripts\activate      # Windows
# source venv/bin/activate  # macOS/Linux

# 3. Install dependencies
pip install -r requirements.txt
```

---

## 19. How to Run

```bash
# Start the Flask dashboard
python app.py
```

Then open your browser and go to: **http://127.0.0.1:5000**

### Running Individual Scenarios (CLI)

```bash
python simulator.py 1    # Normal execution
python simulator.py 2    # Deadlock scenario
python simulator.py 3    # Attack detection
```

### Testing Individual Modules

```bash
python database.py           # Test database creation
python lock_manager.py       # Test lock manager
python deadlock_detector.py  # Test cycle detection
python security.py           # Test security rules
python transaction.py        # Test transaction system
```

---

## 20. Future Improvements

If time permits, the following could be added:

1. **Multi-Granularity Locking**: Table-level and row-level locks
2. **Wound-Wait / Wait-Die**: Alternative deadlock prevention schemes
3. **MVCC**: Multi-Version Concurrency Control for better read performance
4. **Real-time WebSocket updates**: Instead of polling
5. **More attack patterns**: Brute force detection, session hijacking
6. **Transaction priority levels**: Based on user roles
7. **Visualization**: Animated Wait-For Graph with D3.js
8. **Logging to file**: Persistent log files alongside database logging

---

## Project Structure

```
OSDBMS/
|
|-- app.py                  # Flask web application
|-- database.py             # SQLite schema + helpers
|-- transaction.py          # Transaction class + manager
|-- lock_manager.py         # Lock Manager (Strict 2PL)
|-- deadlock_detector.py    # Wait-For Graph + DFS
|-- security.py             # Attack detection rules
|-- simulator.py            # 3 demonstration scenarios
|-- requirements.txt        # Dependencies (Flask only)
|-- README.md               # This file
|
|-- database/
|   |-- database.db         # SQLite database (auto-created)
|
|-- templates/
|   |-- index.html          # Dashboard HTML
|
|-- static/
    |-- style.css           # Dashboard styling
    |-- script.js           # Dashboard JavaScript
```

---

## License

This is an academic project created for educational purposes.
