from abc import ABC, abstractmethod
from typing import Any, Optional, Union

class CacheInterface(ABC):
    """
    Abstract Base Class defining the contract for caching providers.
    All implementations must be asynchronous to support FastAPI's concurrency.
    """

    @abstractmethod
    async def get(self, key: str) -> Optional[Any]:
        """
        Retrieve and deserialize data from the cache.

        Args:
            key (str): The unique identifier for the cached item.

        Returns:
            Optional[Any]: The deserialized data if found and not expired,
                          otherwise None.
        """
        pass

    @abstractmethod
    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None
    ) -> bool:
        """
        Serialize and store data in the cache.

        Args:
            key (str): The unique identifier for the cached item.
            value (Any): The data to store (dict, list, str, int, etc.).
            ttl (Optional[int]): Time To Live in seconds. If None, the key
                                 persists indefinitely (depending on provider).

        Returns:
            bool: True if the operation was successful, False otherwise.
        """
        pass

    @abstractmethod
    async def delete(self, key: str) -> bool:
        """
        Remove a specific key from the cache.

        Args:
            key (str): The key to be deleted.

        Returns:
            bool: True if the key existed and was deleted, False otherwise.
        """
        pass

    @abstractmethod
    async def exists(self, key: str) -> bool:
        """
        Check if a key exists in the cache without retrieving its value.

        Args:
            key (str): The key to check.

        Returns:
            bool: True if the key exists and is not expired, False otherwise.
        """
        pass

    @abstractmethod
    async def increment(self, key: str, amount: int = 1) -> int:
        """
        Atomically increment a counter. Useful for rate limiting.

        Args:
            key (str): The identifier for the counter.
            amount (int): The value to add to the current counter. Defaults to 1.

        Returns:
            int: The new value of the counter after incrementing.
        """
        pass

    @abstractmethod
    async def clear(self) -> bool:
        """
        Flush all keys from the current cache database/instance.

        Returns:
            bool: True if the cache was successfully cleared.
        """
        pass