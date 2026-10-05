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
