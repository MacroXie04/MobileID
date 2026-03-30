from index.services.transaction_queries import TransactionQueryMixin
from index.services.transaction_writes import CreatedTransaction, TransactionWriteMixin


class TransactionService(TransactionWriteMixin, TransactionQueryMixin):
    """
    Service layer for Transaction-related reads/writes.
    Keeps your views thin and reusable for Celery tasks, management commands,
    etc.
    """

    pass


__all__ = ["TransactionService", "CreatedTransaction"]
