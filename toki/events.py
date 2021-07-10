from abc import ABC
from contextlib import suppress
from functools import wraps
from threading import Thread
from traceback import print_exc
from typing import Any, Callable, Optional, Union
from queue import Queue

class Event:
    PASSWORD = '<<PASSWORD>>'
    TOTP_LIST = '<<TOTP_LIST>>'
    TOTP_SELECTED = '<<TOTP_SELECTED>>'
    TOTP_UPDATE = '<<TOTP_UPDATE>>'
    TIMER_UPDATE = '<<TIMER_UPDATE>>'
    ADD_TOTP = '<<ADD_TOTP>>'
    SHOW_TOTP = '<<SHOW_TOTP>>'
    REMOVE_TOTP = '<<REMOVE_TOTP>>'
    COPY_TOTP = '<<COPY_TOTP>>'
    MENU_ADD_TOTP = '<<MENU_ADD_TOTP>>'
    MENU_SHOW_TOTP = '<<MENU_SHOW_TOTP>>'
    MENU_REMOVE_TOTP = '<<MENU_REMOVE_TOTP>>'
    MENU_CHANGE_PASSWORD = '<<MENU_CHANGE_PASSWORD>>'
    MENU_EXIT = '<<MENU_EXIT>>'
    SHOW_TOTP_FRAME = '<<SHOW_TOTP_FRAME>>'


class EventSystem:
    class Event:
        def __init__(self, name: str, data: Optional[Any] = None):
            self.name = name
            self.data = data

    def __init__(self):
        self.subscribers = {}
        self._queue = Queue()
        self._thread = Thread(None, self._consumer_thread, daemon=True)
        self._running = True
        self._thread.start()

    def _consumer_thread(self):
        while self._running:
            try:
                event = self._queue.get()
                #print('consuming', event)
                for func in self.subscribers.get(event.name, []):
                    func(event.data)
            except Exception as ex:
                print("Exception in EventSystem consumer")
                print_exc()
            finally:
                self._queue.task_done()


    def subscribe(self, name: str, consumer: Callable) -> None:
        #print(f'subscribing {name} to {consumer}')
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
        self._queue.put_nowait(self.Event(name, data))
        return True

    def stop(self) -> None:
        self._running = False
        self.publish('', None)


class AbstractGlobalEvents(ABC):
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


class GlobalEvents:
    event_system = EventSystem()

    @classmethod
    def get_event_system(cls) -> Union[EventSystem, None]:
        return cls.event_system

    @classmethod
    def subscribes_to(cls, event_name: str) -> Callable:
        def decorator(func: Callable) -> Any:
            cls.subscribe(event_name, func)

            @wraps(func)
            def wrapper(*args, **kwargs):
                return func(*args, **kwargs)

            return wrapper
        return decorator

    @classmethod
    def publishes(cls, event_name: str) -> Callable:
        def decorator(func: Callable):
            @wraps(func)
            def wrapper(*args, **kwargs):
                r = func(*args, **kwargs)
                cls.event

    @classmethod
    def subscribe(cls, *args, **kwargs) -> None:
        with suppress(AttributeError):
            return cls.event_system.subscribe(*args, **kwargs)

    @classmethod
    def publish(cls, *args, **kwargs) -> bool:
        try:
            return cls.event_system.publish(*args, **kwargs)
        except AttributeError:
            return False
