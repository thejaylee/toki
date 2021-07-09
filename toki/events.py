from abc import ABC
from contextlib import suppress
from threading import Thread
from typing import Any, Callable, Optional
from queue import Queue

class Event:
    def __init__(self, name: str, data: Optional[Any] = None):
        self.name = name
        self.data = data

class EventSystem:
    def __init__(self):
        self.subscribers = {}
        self._queue = Queue()
        self._thread = Thread(None, self._consumer_thread, daemon=True)
        self._running = True
        self._thread.start()

    def _consumer_thread(self):
        while self._running:
            event = self._queue.get()
            #print('consuming', event)
            for func in self.subscribers.get(event.name, []):
                func(event.data)
            self._queue.task_done()


    def subscribe(self, name: str, consumer: Callable) -> None:
        if name not in self.subscribers:
            self.subscribers[name] = []
        self.subscribers[name].append(consumer)

    def unsubscribe(self, name: str, consumer: Callable) -> None:
        if name not in self.subscribers:
            return

        for func in self.subscribers[name]:
            if consumer is func:
                del self.subscribers[name]

    def publish(self, name: str, data: Optional[Any] = None) -> bool:
        if self._queue.full():
            return False

        #print('publish', name, data)
        self._queue.put_nowait(Event(name, data))
        return True

    def stop(self) -> None:
        self._running = False
        self.publish('', None)

class GlobalEvents(ABC):
    event_system = None

    @property
    def events(self):
        return __class__.event_system

    @events.setter
    def events(self, event_system: EventSystem) -> None:
        if isinstance(event_system, EventSystem):
            __class__.event_system = event_system

    def event_publish(self, *args, **kwargs) -> None:
        with suppress(AttributeError):
            return __class__.event_system.publish(*args, **kwargs)

    def event_subscribe(self, *args, **kwargs) -> None:
        with suppress(AttributeError):
            return __class__.event_system.subscribe(*args, **kwargs)

    def event_unsubscribe(self, *args, **kwargs) -> None:
        with suppress(AttributeError):
            return __class__.event_system.unsubscribe(*args, **kwargs)

#class GlobalEvents:
#   event_system = None
#
#   @classmethod
#   def init(cls):
#       if not isinstance(cls.event_system, EventSystem):
#           cls.event_system = EventSystem()
#
#   @classmethod
#   def subscribe(cls, *args, **kwargs) -> None:
#       return cls.event_system.subscribe(*args, **kwargs)
#
#   @classmethod
#   def unsubscribe(cls, *args, **kwargs) -> None:
#       return cls.event_system.unsubscribe(*args, **kwargs)
#
#   @classmethod
#   def publish(cls, *args, **kwargs) -> bool:
#       return cls.event_system.publish(*args, **kwargs)
#
#   @classmethod
#   def stop(cls, *args, **kwargs) -> None:
#       return cls.event_system.stop(*args, **kwargs)
