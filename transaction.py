import threading
import time
import database
from lock_manager import LockManager, LockType
from security import SecurityMonitor


class TxnState:
    CREATED = "CREATED"
    RUNNING = "RUNNING"
    WAITING = "WAITING"
    BLOCKED = "BLOCKED"
    COMMITTED = "COMMITTED"
    ABORTED = "ABORTED"


class Transaction:

    def __init__(self, txn_id, user_id, operations, lock_manager,
                 security_monitor, description=""):
        self.txn_id = txn_id
        self.user_id = user_id
        self.description = description

        self._operations = operations

        self._lock_manager = lock_manager
        self._security = security_monitor

        self.state = TxnState.CREATED
        self.start_time = time.time()
        self.end_time = None

        self.locks_held = set()
        self.current_operation = ""
        self.operations_log = []
        self.error = None

        self._undo_log = {}

        self.thread = None

        self._abort_flag = threading.Event()

    def start(self):
        self.state = TxnState.RUNNING
        self.start_time = time.time()

        self.thread = threading.Thread(
            target=self._run,
            name=f"Thread-{self.txn_id}",
            daemon=True
        )
        self.thread.start()
        print(f"[{self.txn_id}] Transaction started on {self.thread.name}")

    def _run(self):
        try:
            for i, operation in enumerate(self._operations):
                if self._abort_flag.is_set():
                    self._rollback("Aborted by deadlock detector")
                    return

                self.current_operation = f"Operation {i + 1}/{len(self._operations)}"

                success = operation(self)

                if not success:
                    self._rollback(f"Operation {i + 1} failed")
                    return

                if self._abort_flag.is_set():
                    self._rollback("Aborted by deadlock detector")
                    return

            self._commit()

        except Exception as e:
            self._rollback(f"Exception: {str(e)}")
    def acquire_lock(self, resource_id, lock_type=LockType.EXCLUSIVE, timeout=15):
        old_state = self.state
        self.state = TxnState.WAITING
        self.current_operation = f"Waiting for {lock_type.value} lock on {resource_id}"

        self.operations_log.append({
            "action": "LOCK_REQUEST",
            "resource": resource_id,
            "lock_type": lock_type.value,
            "time": time.strftime("%H:%M:%S")
        })

        granted = self._lock_manager.acquire_lock(
            self.txn_id, resource_id, lock_type, timeout=timeout
        )

        if granted:
            self.state = TxnState.RUNNING
            self.locks_held.add(resource_id)
            self.operations_log.append({
                "action": "LOCK_GRANTED",
                "resource": resource_id,
                "lock_type": lock_type.value,
                "time": time.strftime("%H:%M:%S")
            })
            return True
        else:
            self.state = TxnState.BLOCKED
            return False

    def read_account(self, account_id):
        resource_id = f"account_{account_id}"

        allowed, reason = self._security.check_operation(
            user_id=self.user_id, txn_id=self.txn_id,
            operation="READ", resource=resource_id
        )
        if not allowed:
            self.operations_log.append({
                "action": "READ_BLOCKED",
                "resource": resource_id,
                "reason": reason,
                "time": time.strftime("%H:%M:%S")
            })
            return None

        if not self.acquire_lock(resource_id, LockType.SHARED):
            return None

        balance = database.get_account_balance(account_id)
        self.current_operation = f"Read account {account_id}: Rs.{balance}"

        self.operations_log.append({
            "action": "READ",
            "resource": resource_id,
            "value": balance,
            "time": time.strftime("%H:%M:%S")
        })

        return balance

    def write_account(self, account_id, new_balance):
        resource_id = f"account_{account_id}"

        allowed, reason = self._security.check_operation(
            user_id=self.user_id, txn_id=self.txn_id,
            operation="WRITE", resource=resource_id
        )
        if not allowed:
            self.operations_log.append({
                "action": "WRITE_BLOCKED",
                "resource": resource_id,
                "reason": reason,
                "time": time.strftime("%H:%M:%S")
            })
            return False

        if not self.acquire_lock(resource_id, LockType.EXCLUSIVE):
            return False

        if resource_id not in self._undo_log:
            original = database.get_account_balance(account_id)
            self._undo_log[resource_id] = original

        success = database.update_account_balance(account_id, new_balance)

        self.current_operation = f"Write account {account_id}: Rs.{new_balance}"
        self.operations_log.append({
            "action": "WRITE",
            "resource": resource_id,
            "value": new_balance,
            "success": success,
            "time": time.strftime("%H:%M:%S")
        })

        return success
