import asyncio
import hashlib
import json
import logging
import pickle
from datetime import datetime
from typing import TypeVar, Type, List, Optional, Any, Dict
from contextvars import ContextVar

from redis import asyncio as aioredis

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.config import environ

from ZewSFS.Types import SFSObject, Long, SFSArray
from database import Base, Session as SessionLocal, RedisSession

T = TypeVar('T', bound='BaseAdapter')

current_transaction = ContextVar('current_transaction', default=None)

model_adapter_map: Dict[Type[Base ], Type['BaseAdapter']] = {}

def register_adapter(model_class: Type[Base ]):
    def decorator(adapter_class: Type['BaseAdapter']):
        model_adapter_map[model_class] = adapter_class
        adapter_class._db_model = model_class
        return adapter_class
    return decorator

def get_adapter_class_for_model(model_class: Type[Base ]):
    return model_adapter_map.get(model_class)


def generate_cache_key(table_name: str, method_name: str, params: dict) -> str:
    sorted_params = json.dumps(params, sort_keys=True)
    hash_digest = hashlib.md5(sorted_params.encode('utf-8')).hexdigest()
    return f"{table_name}_{method_name}_{hash_digest}"

CACHE_TTL = 300

class Transaction:
    def __init__(self):
        self._session: Optional[AsyncSession] = None
        self._redis_pipeline: Optional[aioredis.client.Pipeline] = None
        self._token: Optional[ContextVar] = None

    async def __aenter__(self):
        # Create a new database session
        self._session = SessionLocal()
        # Begin a transaction
        await self._session.begin()
        # Create a Redis pipeline
        self._redis_pipeline = RedisSession.pipeline(transaction=True)
        # Set the current transaction in the context variable
        self._token = current_transaction.set(self)
        return self

    async def __aexit__(self, exc_type, exc, tb):
        try:
            if exc_type is None:
                # No exceptions, commit the transaction
                await self._session.commit()
                await self._redis_pipeline.execute()
            else:
                # Exception occurred, rollback the transaction
                await self._session.rollback()
                await self._redis_pipeline.reset()
        finally:
            current_transaction.reset(self._token)
            await self._session.close()

class BaseAdapterMeta(type):
    def __new__(mcs, name, bases, dct):
        cls = super().__new__(mcs, name, bases, dct)
        cls._db_model = dct.get('_db_model')
        if cls._db_model:
            model_adapter_map[cls._db_model] = cls
        return cls

class BaseAdapter(metaclass=BaseAdapterMeta):
    _db_model: Type[Base ]
    _enable_caching: bool = environ.get('ENABLE_REDIS', '0') == '1'

    _game_id_key = 'id'
    _specific_sfs_datatypes = {}

    id: int = None
    created_at: datetime = datetime.now()
    changed_at: datetime = datetime.now()
    _db_instance: Optional[Base ] = None

    async def save(self):
        await self.before_save()
        self.changed_at = datetime.now()

        transaction = current_transaction.get()
        if transaction is not None:
            session = transaction._session
            redis_pipe = transaction._redis_pipeline
        else:
            session = SessionLocal()
            await session.__aenter__()
            redis_pipe = RedisSession

        try:
            if self.id is not None:
                db_instance = await session.get(self._db_model, self.id)
            else:
                db_instance = None

            if db_instance is None:
                db_instance = self._db_model()
                db_instance.id = self.id
                session.add(db_instance)

            for field in self._db_model.__table__.columns.keys():
                setattr(db_instance, field, getattr(self, field))

            # Save related objects
            for rel in self._db_model.__mapper__.relationships:
                related_adapter = getattr(self, rel.key, None)
                if related_adapter is not None:
                    if isinstance(related_adapter, list):
                        for adapter in related_adapter:
                            await adapter.save()
                        setattr(db_instance, rel.key, [adapter._db_instance for adapter in related_adapter])
                    else:
                        await related_adapter.save()
                        setattr(db_instance, rel.key, related_adapter._db_instance)

            await session.flush()
            await session.refresh(db_instance)
            self.id = db_instance.id
            self._db_instance = db_instance  # Store reference to the model instance

            await self.after_save()

            if transaction is None:
                await session.commit()
        except Exception as e:
            if transaction is None:
                await session.rollback()
            raise e
        finally:
            if transaction is None:
                await session.close()

        # Caching
        if self._enable_caching:
            cache_key = f"{self._db_model.__tablename__}_id_{self.id}"
            cache_value = pickle.dumps(self.to_dict())
            if transaction is not None:
                redis_pipe.set(cache_key, cache_value, ex=CACHE_TTL)
            else:
                await RedisSession.set(cache_key, cache_value, ex=CACHE_TTL)

    @classmethod
    async def load_by_id(cls: Type[T], id: int, use_cache: bool = True) -> T:
        transaction = current_transaction.get()
        cache_key = None

        if use_cache and cls._enable_caching and transaction is None:
            cache_key = f"{cls._db_model.__tablename__}_id_{id}"
            cached_data = await RedisSession.get(cache_key)
            if cached_data is not None:
                return await cls.from_dict(pickle.loads(cached_data))

        if transaction is not None:
            session = transaction._session
        else:
            session = SessionLocal()
            await session.__aenter__()

        try:
            db_instance = await session.get(cls._db_model, id)
            if db_instance:
                instance = await cls.from_db_instance(db_instance, session=session)
                if cache_key:
                    await RedisSession.set(cache_key, pickle.dumps(instance.to_dict()), ex=CACHE_TTL)
                return instance
            else:
                return None
        finally:
            if transaction is None:
                await session.close()

    @classmethod
    async def load_one_by(cls: Type[T], use_cache: bool = False, **query_params) -> T:
        transaction = current_transaction.get()
        cache_key = None

        if use_cache and cls._enable_caching and transaction is None:
            cache_key = generate_cache_key(cls._db_model.__tablename__, 'load_one_by', query_params)
            cached_data = await RedisSession.get(cache_key)
            if cached_data is not None:
                return await cls.from_dict(pickle.loads(cached_data))

        if transaction is not None:
            session = transaction._session
        else:
            session = SessionLocal()
            await session.__aenter__()

        try:
            conditions = [getattr(cls._db_model, key) == value for key, value in query_params.items()]
            stmt = select(cls._db_model).where(and_(*conditions))
            result = await session.execute(stmt)
            db_instance = result.scalar_one_or_none()
            if db_instance:
                instance = await cls.from_db_instance(db_instance, session=session)
                if cache_key:
                    await RedisSession.set(cache_key, pickle.dumps(instance.to_dict()), ex=CACHE_TTL)
                return instance
            else:
                return None
        finally:
            if transaction is None:
                await session.close()

    @classmethod
    async def load_all_by(cls: Type[T], use_cache: bool = False, **query_params) -> List[T]:
        transaction = current_transaction.get()
        cache_key = None

        if use_cache and cls._enable_caching and transaction is None:
            cache_key = generate_cache_key(cls._db_model.__tablename__, 'load_all_by', query_params)
            cached_data = await RedisSession.get(cache_key)
            if cached_data is not None:
                data_list = pickle.loads(cached_data)
                return await asyncio.gather(*[cls.from_dict(data) for data in data_list])

        if transaction is not None:
            session = transaction._session
        else:
            session = SessionLocal()
            await session.__aenter__()

        try:
            conditions = [getattr(cls._db_model, key) == value for key, value in query_params.items()]
            stmt = select(cls._db_model).where(and_(*conditions))
            result = await session.execute(stmt)
            db_instances = result.scalars().all()
            instances = await asyncio.gather(*[cls.from_db_instance(db_instance, session=session) for db_instance in db_instances])
            if cache_key:
                data_list = [instance.to_dict() for instance in instances]
                await RedisSession.set(cache_key, pickle.dumps(data_list), ex=CACHE_TTL)
            return instances
        finally:
            if transaction is None:
                await session.close()

    @classmethod
    async def load_all(cls: Type[T], use_cache: bool = False) -> List[T]:
        transaction = current_transaction.get()
        cache_key = None

        if use_cache and cls._enable_caching and transaction is None:
            cache_key = generate_cache_key(cls._db_model.__tablename__, 'load_all', {})
            cached_data = await RedisSession.get(cache_key)
            if cached_data is not None:
                data_list = pickle.loads(cached_data)
                return await asyncio.gather(*[cls.from_dict(data) for data in data_list])

        if transaction is not None:
            session = transaction._session
        else:
            session = SessionLocal()
            await session.__aenter__()

        try:
            result = await session.execute(select(cls._db_model))
            db_instances = result.scalars().all()
            instances = await asyncio.gather(*[cls.from_db_instance(db_instance, session=session) for db_instance in db_instances])
            if cache_key:
                data_list = [instance.to_dict() for instance in instances]
                await RedisSession.set(cache_key, pickle.dumps(data_list), ex=CACHE_TTL)
            return instances
        finally:
            if transaction is None:
                await session.close()

    @classmethod
    async def from_db_instance(cls: Type[T], db_instance, session: Optional[AsyncSession] = None, visited=None) -> T:
        if visited is None:
            visited = {}

        instance_id = (cls._db_model, db_instance.id)
        if instance_id in visited:
            return visited[instance_id]

        instance = cls()
        instance._db_instance = db_instance
        visited[instance_id] = instance  # Mark as visited

        for field in cls._db_model.__table__.columns.keys():
            setattr(instance, field, getattr(db_instance, field))

        # Get the current session
        if session is None:
            transaction = current_transaction.get()
            if transaction is not None:
                session = transaction._session
            else:
                session = SessionLocal()
                await session.__aenter__()
                created_session = True
        else:
            created_session = False

        # Handle relationships
        try:
            for rel in cls._db_model.__mapper__.relationships:
                # Check if the related attribute is already loaded
                if rel.key in db_instance.__dict__:
                    related_obj = getattr(db_instance, rel.key)
                else:
                    # Asynchronously load the related attribute
                    await session.refresh(db_instance, [rel.key])
                    related_obj = getattr(db_instance, rel.key)

                if related_obj is not None:
                    adapter_class = get_adapter_class_for_model(rel.mapper.class_)
                    if adapter_class:
                        if rel.uselist:
                            related_adapters = []
                            for obj in related_obj:
                                related_adapter = await adapter_class.from_db_instance(obj, session=session,
                                                                                       visited=visited)
                                related_adapters.append(related_adapter)
                            setattr(instance, rel.key, related_adapters)
                        else:
                            related_adapter = await adapter_class.from_db_instance(related_obj, session=session,
                                                                                   visited=visited)
                            setattr(instance, rel.key, related_adapter)
                    else:
                        setattr(instance, rel.key, related_obj)  # If no adapter found, set the raw object
        finally:
            if created_session:
                await session.__aexit__(None, None, None)

        await instance.on_load_complete()

        # Caching
        if cls._enable_caching:
            cache_key = f"{cls._db_model.__tablename__}_id_{instance.id}"
            cache_value = pickle.dumps(instance.to_dict())
            transaction = current_transaction.get()
            if transaction is not None:
                transaction._redis_pipeline.set(cache_key, cache_value, ex=CACHE_TTL)
            else:
                await RedisSession.set(cache_key, cache_value, ex=CACHE_TTL)

        return instance

    def to_dict(self, visited=None, enforce_datatypes: bool = False):
        if visited is None:
            visited = set()

        instance_id = (self._db_model, self.id)
        if instance_id in visited:
            return 'REMOVE'

        visited.add(instance_id)

        data = {field: getattr(self, field) for field in self._db_model.__table__.columns.keys()}

        # Include related objects
        for rel in self._db_model.__mapper__.relationships:
            related_adapter = getattr(self, rel.key, None)
            if related_adapter is not None:
                if isinstance(related_adapter, list):
                    data[rel.key] = []
                    for adapter in related_adapter:
                        if (dict_data := adapter.to_dict(visited=visited, enforce_datatypes=enforce_datatypes)) != 'REMOVE':
                            data[rel.key].append(dict_data)
                else:
                    if (dict_data := related_adapter.to_dict(visited=visited, enforce_datatypes=enforce_datatypes)) != 'REMOVE':
                        data[rel.key] = dict_data

        if enforce_datatypes:
            for k, v in data.items():
                if type(v) is datetime:
                    data[k] = int(v.timestamp())
            return self.enforce_dict(data)

        return data

    @classmethod
    async def from_dict(cls: Type[T], params: dict):
        instance = cls()
        for field, value in params.items():
            if field in cls._db_model.__table__.columns.keys():
                setattr(instance, field, value)
            else:
                # This is a related object
                rel = cls._db_model.__mapper__.relationships.get(field)
                if rel:
                    adapter_class = get_adapter_class_for_model(rel.mapper.class_)
                    if adapter_class:
                        if isinstance(value, list):
                            related_adapters = []
                            for item in value:
                                related_adapter = await adapter_class.from_dict(item)
                                related_adapters.append(related_adapter)
                            setattr(instance, field, related_adapters)
                        else:
                            related_adapter = await adapter_class.from_dict(value)
                            setattr(instance, field, related_adapter)
                    else:
                        setattr(instance, field, value)  # If no adapter found, set the raw value
        await instance.on_load_complete()
        return instance

    async def remove(self):
        transaction = current_transaction.get()
        if transaction is not None:
            session = transaction._session
            redis_pipe = transaction._redis_pipeline
        else:
            session = SessionLocal()
            await session.__aenter__()
            redis_pipe = RedisSession

        try:
            db_instance = await session.get(self._db_model, self.id)
            if db_instance:
                # Remove related objects if necessary
                for rel in self._db_model.__mapper__.relationships:
                    related_adapter = getattr(self, rel.key, None)
                    if related_adapter is not None:
                        if isinstance(related_adapter, list):
                            for adapter in related_adapter:
                                await adapter.remove()
                        else:
                            await related_adapter.remove()
                await session.delete(db_instance)
                if transaction is None:
                    await session.commit()
        except Exception as e:
            if transaction is None:
                await session.rollback()
            raise e
        finally:
            if transaction is None:
                await session.close()

        # Remove from cache
        if self._enable_caching:
            cache_key = f"{self._db_model.__tablename__}_id_{self.id}"
            if transaction is not None:
                redis_pipe.delete(cache_key)
            else:
                try:
                    await RedisSession.delete(cache_key)
                except Exception:
                    pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            await self.save()

    def __repr__(self):
        fvars = ', '.join([f'{k}={repr(v)}' for k, v in vars(self).items()])
        return f"{self.__class__.__name__}({fvars})"

    def __str__(self):
        fvars = ', '.join([f'{k}={repr(v)}' for k, v in self.to_dict().items()])
        return f"{self.__class__.__name__}({fvars})"

    async def on_load_complete(self):
        return

    async def after_save(self):
        return

    async def before_save(self):
        return

    def enforce_dict(self, data: dict):
        return data

    async def to_sfs_object(self) -> SFSObject:
        obj = SFSObject()
        for field in self._db_model.__table__.columns.keys():
            key = self._game_id_key if field == 'id' else field
            val = getattr(self, field)
            if val is None:
                continue
            sds = {'id': Long, 'date_created': Long, 'last_updated': Long} | self._specific_sfs_datatypes
            if field in sds:
                obj.set_item(key, sds.get(field)(name=key, value=val))
            else:
                obj.putAny(key, val)
        return await self.update_sfs(obj)

    @classmethod
    async def from_sfs_object(cls: Type[T], obj: SFSObject) -> T:
        instance = cls()
        values = obj.get_value()
        for field, val_container in values.items():
            if isinstance(val_container, (SFSObject, SFSArray)):
                val = val_container.to_json()
            else:
                val = val_container.get_value()

            if field == cls._game_id_key:
                setattr(instance, 'id', val)
            else:
                setattr(instance, field, val)

        await instance.on_sfs_load_complete()
        await instance.on_load_complete()
        return instance

    async def on_sfs_load_complete(self):
        return

    async def update_sfs(self, params: SFSObject):
        return params

    async def on_remove(self):
        ...