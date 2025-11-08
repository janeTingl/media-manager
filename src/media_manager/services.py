"""Dependency injection and service registry for the media manager application."""

from typing import Any, Dict, Optional, Type, TypeVar, Union, Callable

from PySide6.QtCore import QObject

T = TypeVar("T")


class ServiceRegistry(QObject):
    """Simple dependency injection container for application services."""

    def __init__(self, parent: Optional[QObject] = None) -> None:
        super().__init__(parent)
        self._services: Dict[str, Any] = {}
        self._factories: Dict[str, Callable[[], Any]] = {}
        self._singletons: Dict[str, Any] = {}

    def register(
        self,
        service_type: Union[str, Type],
        implementation: Any,
        singleton: bool = True,
    ) -> None:
        """Register a service implementation."""
        key = service_type if isinstance(service_type, str) else service_type.__name__

        if singleton:
            if callable(implementation):
                self._factories[key] = implementation
            else:
                self._singletons[key] = implementation
        else:
            self._services[key] = implementation

    def get(self, service_type: Union[str, Type]) -> Any:
        """Get a service instance."""
        key = service_type if isinstance(service_type, str) else service_type.__name__

        # Check singletons first
        if key in self._singletons:
            return self._singletons[key]

        # Check factories
        if key in self._factories:
            instance = self._factories[key]()
            self._singletons[key] = instance
            return instance

        # Check regular services
        if key in self._services:
            service = self._services[key]
            if callable(service):
                return service()
            return service

        raise KeyError(f"Service '{key}' not found in registry")

    def has(self, service_type: Union[str, Type]) -> bool:
        """Check if a service is registered."""
        key = service_type if isinstance(service_type, str) else service_type.__name__
        return (
            key in self._services or key in self._factories or key in self._singletons
        )

    def clear(self) -> None:
        """Clear all registered services."""
        self._services.clear()
        self._factories.clear()
        self._singletons.clear()


# Global service registry instance
_service_registry: Optional[ServiceRegistry] = None


def get_service_registry() -> ServiceRegistry:
    """Get the global service registry instance."""
    global _service_registry
    if _service_registry is None:
        _service_registry = ServiceRegistry()
    return _service_registry


def inject(service_type: Union[str, Type]) -> Callable:
    """Dependency injection decorator."""

    def decorator(func: Callable) -> Callable:
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            service = get_service_registry().get(service_type)
            return func(service, *args, **kwargs)

        return wrapper

    return decorator
