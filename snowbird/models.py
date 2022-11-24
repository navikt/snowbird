from typing import Dict, List, Optional

from pydantic import BaseModel


class DictModel(BaseModel):
    __root__: Dict[str, BaseModel]

    def __getitem__(self, item):
        return self.__root__[item]

    def keys(self):
        return self.__root__.keys()


class Database(BaseModel):
    shared: Optional[bool]
    schemas: Optional[List[str]]


class Databases(DictModel):
    __root__: Dict[str, Database]


class Warehouse(BaseModel):
    size: str
    initially_suspended: bool = True
    auto_suspend: int = 2


class Warehouses(DictModel):
    __root__: Dict[str, Warehouse]


class Membership(BaseModel):
    include: Optional[List[str]]
    exclude: Optional[List[str]]


class PrivilegeRules(BaseModel):
    read: Optional[List[str]]
    write: Optional[List[str]]


class Privileges(BaseModel):
    databases: Optional[PrivilegeRules]
    schemas: Optional[PrivilegeRules]
    tables: Optional[PrivilegeRules]


class Resources(BaseModel):
    databases: Optional[List[str]]
    schemas: Optional[List[str]]
    tables: Optional[List[str]]


class Role(BaseModel):
    owner: Optional[str]
    warehouses: Optional[List[str]]
    integrations: Optional[List[str]]
    member_of: Optional[List[str]]
    privileges: Optional[Privileges]
    owns: Optional[Resources]


class Roles(DictModel):
    __root__: Dict[str, Role]


class User(BaseModel):
    owner: Optional[str]
    can_login: Optional[bool]
    member_of: Optional[List[str]]


class Users(DictModel):
    __root__: Dict[str, User]


class Model(BaseModel):
    databases: Optional[List[Databases]]
    warehouses: Optional[List[Warehouses]]
    roles: Optional[List[Roles]]
    users: Optional[List[Users]]
