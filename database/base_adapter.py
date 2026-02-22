import asyncio
from contextlib import asynccontextmanager
from datetime import datetime
from typing import TypeVar, Type, List, Optional, Dict

from sqlalchemy import func, select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ZewSFS.Types import SFSObject, Long, SFSArray
from database import Base, Session as SessionLocal

T = TypeVar('T', bound='BaseAdapter')

current_transaction = __import__('contextvars').ContextVar('current_transaction', default=None)

model_adapter_map: Dict[Type[Base], Type['BaseAdapter']] = {}


def register_adapter(model_class: Type[Base]):
    def decorator(adapter_class: Type['BaseAdapter']):
        model_adapter_map[model_class] = adapter_class
        adapter_class._db_model = model_class
        return adapter_class
    return decorator


def get_adapter_class_for_model(model_class: Type[Base]):
    return model_adapter_map.get(model_class)


class Transaction:
    def __init__(self):
        self._session: Optional[AsyncSession] = None
        self._token = None

    async def __aenter__(self):
        self._session = SessionLocal()
        await self._session.begin()
        self._token = current_transaction.set(self)
        return self

    async def __aexit__(self, exc_type, exc, tb):
        try:
            if exc_type is None:
                await self._session.commit()
            else:
                await self._session.rollback()
        finally:
            current_transaction.reset(self._token)
            await self._session.close()


@asynccontextmanager
async def _session_ctx():
    """Возвращает текущую транзакционную сессию или создаёт новую на один запрос."""
    transaction = current_transaction.get()
    if transaction is not None:
        yield transaction._session
        return

    async with SessionLocal() as session:
        yield session


class BaseAdapterMeta(type):
    def __new__(mcs, name, bases, dct):
        cls = super().__new__(mcs, name, bases, dct)
        db_model = dct.get('_db_model')
        if db_model:
            model_adapter_map[db_model] = cls
        return cls


class BaseAdapter(metaclass=BaseAdapterMeta):
    _db_model: Type[Base]

    _game_id_key = 'id'
    _specific_sfs_datatypes = {}

    id: int = None
    _db_instance: Optional[Base] = None

    def __init__(self):
        self.created_at: datetime = datetime.now()
        self.changed_at: datetime = datetime.now()

    async def save(self):
        await self.before_save()
        self.changed_at = datetime.now()

        transaction = current_transaction.get()
        owned_session = transaction is None

        async with _session_ctx() as session:
            try:
                if self.id is not None:
                    db_instance = await session.get(self._db_model, self.id)
                else:
                    db_instance = None

                if db_instance is None:
                    if self.id is None:
                        r = await session.execute(select(func.max(self._db_model.id)))
                        self.id = (r.scalar() or 0) + 1
                    db_instance = self._db_model()
                    db_instance.id = self.id
                    session.add(db_instance)

                for field in self._db_model.__table__.columns.keys():
                    setattr(db_instance, field, getattr(self, field, None))

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
                for field in self._db_model.__table__.columns.keys():
                    setattr(self, field, getattr(db_instance, field))
                self._db_instance = db_instance

                await self.after_save()

                if owned_session:
                    await session.commit()
            except Exception:
                if owned_session:
                    await session.rollback()
                raise

    @classmethod
    def _eager_options(cls):
        """Опции для подгрузки связей в одном запросе, чтобы не дергать lazy load в async."""
        rels = cls._db_model.__mapper__.relationships
        return [selectinload(getattr(cls._db_model, r.key)) for r in rels] if rels else []

    @classmethod
    async def load_by_id(cls: Type[T], id: int, use_cache: bool = True) -> Optional[T]:
        async with _session_ctx() as session:
            stmt = select(cls._db_model).where(cls._db_model.id == id)
            opts = cls._eager_options()
            if opts:
                stmt = stmt.options(*opts)
            result = await session.execute(stmt)
            db_instance = result.unique().scalar_one_or_none()
            if db_instance:
                return await cls.from_db_instance(db_instance, session=session)
            return None

    @classmethod
    async def load_one_by(cls: Type[T], use_cache: bool = False, **query_params) -> Optional[T]:
        async with _session_ctx() as session:
            conditions = [getattr(cls._db_model, key) == value for key, value in query_params.items()]
            stmt = select(cls._db_model).where(and_(*conditions))
            opts = cls._eager_options()
            if opts:
                stmt = stmt.options(*opts)
            result = await session.execute(stmt)
            db_instance = result.unique().scalar_one_or_none() if opts else result.scalar_one_or_none()
            if db_instance:
                return await cls.from_db_instance(db_instance, session=session)
            return None

    @classmethod
    async def load_all_by(cls: Type[T], use_cache: bool = False, **query_params) -> List[T]:
        async with _session_ctx() as session:
            conditions = [getattr(cls._db_model, key) == value for key, value in query_params.items()]
            stmt = select(cls._db_model).where(and_(*conditions))
            opts = cls._eager_options()
            if opts:
                stmt = stmt.options(*opts)
            result = await session.execute(stmt)
            db_instances = result.unique().scalars().all() if opts else result.scalars().all()
            return list(await asyncio.gather(*[
                cls.from_db_instance(db_instance, session=session)
                for db_instance in db_instances
            ]))

    @classmethod
    async def load_all(cls: Type[T], use_cache: bool = False) -> List[T]:
        async with _session_ctx() as session:
            stmt = select(cls._db_model)
            opts = cls._eager_options()
            if opts:
                stmt = stmt.options(*opts)
            result = await session.execute(stmt)
            db_instances = result.unique().scalars().all() if opts else result.scalars().all()
            return list(await asyncio.gather(*[
                cls.from_db_instance(db_instance, session=session)
                for db_instance in db_instances
            ]))

    @classmethod
    async def from_db_instance(cls: Type[T], db_instance, session: Optional[AsyncSession] = None, visited=None) -> T:
        if visited is None:
            visited = {}

        instance_id = (cls._db_model, db_instance.id)
        if instance_id in visited:
            return visited[instance_id]

        instance = cls()
        instance._db_instance = db_instance
        visited[instance_id] = instance

        for field in cls._db_model.__table__.columns.keys():
            setattr(instance, field, getattr(db_instance, field))

        created_session = False
        if session is None:
            transaction = current_transaction.get()
            if transaction is not None:
                session = transaction._session
            else:
                session = SessionLocal()
                await session.__aenter__()
                created_session = True

        try:
            for rel in cls._db_model.__mapper__.relationships:
                # AsyncSession.refresh(attribute_names=[relationship]) в async не загружает связи (SQLAlchemy #8701).
                # Загружаем связь явным async select по local_remote_pairs, чтобы не триггерить lazy load → MissingGreenlet.
                pairs = list(rel.local_remote_pairs)
                if not pairs:
                    setattr(instance, rel.key, [] if rel.uselist else None)
                    continue
                conditions = [
                    remote_col == getattr(db_instance, local_col.key)
                    for local_col, remote_col in pairs
                ]
                stmt = select(rel.mapper.class_).where(and_(*conditions))
                result = await session.execute(stmt)
                if rel.uselist:
                    related_objs = list(result.scalars().all())
                else:
                    related_obj = result.scalar_one_or_none()
                    related_objs = [related_obj] if related_obj is not None else []

                adapter_class = get_adapter_class_for_model(rel.mapper.class_)
                if adapter_class:
                    if rel.uselist:
                        related_adapters = [
                            await adapter_class.from_db_instance(obj, session=session, visited=visited)
                            for obj in related_objs
                        ]
                        setattr(instance, rel.key, related_adapters)
                    else:
                        setattr(
                            instance,
                            rel.key,
                            await adapter_class.from_db_instance(related_objs[0], session=session, visited=visited)
                            if related_objs else None,
                        )
                else:
                    setattr(instance, rel.key, related_objs if rel.uselist else (related_objs[0] if related_objs else None))
        finally:
            if created_session:
                await session.__aexit__(None, None, None)

        await instance.on_load_complete()
        return instance

    def to_dict(self, visited=None, enforce_datatypes: bool = False):
        if visited is None:
            visited = set()

        instance_id = (self._db_model, self.id)
        if instance_id in visited:
            return 'REMOVE'

        visited.add(instance_id)

        data = {field: getattr(self, field) for field in self._db_model.__table__.columns.keys()}

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
    async def from_dict(cls: Type[T], params: dict) -> T:
        instance = cls()
        for field, value in params.items():
            if field in cls._db_model.__table__.columns.keys():
                setattr(instance, field, value)
            else:
                rel = cls._db_model.__mapper__.relationships.get(field)
                if rel:
                    adapter_class = get_adapter_class_for_model(rel.mapper.class_)
                    if adapter_class:
                        if isinstance(value, list):
                            related_adapters = [await adapter_class.from_dict(item) for item in value]
                            setattr(instance, field, related_adapters)
                        else:
                            setattr(instance, field, await adapter_class.from_dict(value))
                    else:
                        setattr(instance, field, value)
        await instance.on_load_complete()
        return instance

    async def remove(self):
        transaction = current_transaction.get()
        owned_session = transaction is None

        async with _session_ctx() as session:
            try:
                db_instance = await session.get(self._db_model, self.id)
                if db_instance:
                    for rel in self._db_model.__mapper__.relationships:
                        related_adapter = getattr(self, rel.key, None)
                        if related_adapter is not None:
                            if isinstance(related_adapter, list):
                                for adapter in related_adapter:
                                    await adapter.remove()
                            else:
                                await related_adapter.remove()
                    await session.delete(db_instance)
                    if owned_session:
                        await session.commit()
            except Exception:
                if owned_session:
                    await session.rollback()
                raise

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

    async def update_sfs(self, params: SFSObject) -> SFSObject:
        return params

    async def on_remove(self):
        ...
