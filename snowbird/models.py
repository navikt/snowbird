import json
from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class DictModel(BaseModel):
    __root__: Dict[str, BaseModel]

    def __getitem__(self, item):
        return self.__root__[item]

    def keys(self):
        return self.__root__.keys()


class Database(BaseModel):
    shared: Optional[bool]
class SnowbirdDatabase(Database):
    schemas: Optional[List[str]]


class Databases(DictModel):
    __root__: Dict[str, Database]
class SnowbirdDatabases(Databases):
    __root__: Dict[str, SnowbirdDatabase]


class Warehouse(BaseModel):
    size: str
class SnowbirdWarehouse(Warehouse):
    initially_suspended: bool = True
    auto_suspend: int = 2


class Warehouses(DictModel):
    __root__: Dict[str, Warehouse]
class SnowbirdWarehouses(Warehouses):
    __root__: Dict[str, SnowbirdWarehouse]


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
    warehouses: Optional[List[str]]
    integrations: Optional[List[str]]
    # member_of: Optional[List[str]]
    privileges: Optional[Privileges]
class SnowbirdRole(Role):
    integrations: Optional[List[str]]
    owns: Optional[Resources]
    owner: Optional[str]

class Roles(DictModel):
    __root__: Dict[str, Role]
class SnowbirdRoles(Roles):
    __root__: Dict[str, SnowbirdRole]


class User(BaseModel):
    can_login: Optional[bool]
    member_of: Optional[List[str]]
class SnowbirdUser(User):
    owner: Optional[str]


class Users(DictModel):
    __root__: Dict[str, User]
class SnowbirdUsers(Users):
    __root__: Dict[str, SnowbirdUser]


class PermifrostModel(BaseModel):
    databases: Optional[List[Databases]]
    warehouses: Optional[List[Warehouses]]
    roles: Optional[List[Roles]]
    users: Optional[List[Users]]


class SnowbirdModel(PermifrostModel):
    databases: Optional[List[SnowbirdDatabases]]
    warehouses: Optional[List[SnowbirdWarehouses]]
    roles: Optional[List[SnowbirdRoles]]
    users: Optional[List[SnowbirdUsers]]
