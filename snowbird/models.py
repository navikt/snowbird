import json
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, RootModel


class DictModel(RootModel):
    root: Dict[str, BaseModel]

    def __getitem__(self, item):
        return self.root[item]

    def keys(self):
        return self.root.keys()


class Database(BaseModel):
    shared: Optional[bool] = None


class SnowbirdDatabase(Database):
    schemas: Optional[List[str]] = None


class Databases(DictModel):
    root: Dict[str, Database]


class SnowbirdDatabases(Databases):
    root: Dict[str, SnowbirdDatabase]


class Warehouse(BaseModel):
    size: str


class SnowbirdWarehouse(Warehouse):
    initially_suspended: bool = True
    auto_suspend: int = 2


class Warehouses(DictModel):
    root: Dict[str, Warehouse]


class SnowbirdWarehouses(Warehouses):
    root: Dict[str, SnowbirdWarehouse]


class Membership(BaseModel):
    include: Optional[List[str]] = None
    exclude: Optional[List[str]] = None


class PrivilegeRules(BaseModel):
    read: Optional[List[str]] = None
    write: Optional[List[str]] = None


class Privileges(BaseModel):
    databases: Optional[PrivilegeRules] = None
    schemas: Optional[PrivilegeRules] = None
    tables: Optional[PrivilegeRules] = None


class Resources(BaseModel):
    databases: Optional[List[str]] = None
    schemas: Optional[List[str]] = None
    tables: Optional[List[str]] = None


class Role(BaseModel):
    warehouses: Optional[List[str]] = None
    member_of: Optional[List[str]] = None
    privileges: Optional[Privileges] = None


class SnowbirdRole(Role):
    integrations: Optional[List[str]] = None
    owns: Optional[Resources] = None
    owner: Optional[str] = None


class Roles(DictModel):
    root: Dict[str, Role]


class SnowbirdRoles(Roles):
    root: Dict[str, SnowbirdRole]


class User(BaseModel):
    can_login: Optional[bool] = None
    member_of: Optional[List[str]] = None


class SnowbirdUser(User):
    owner: Optional[str] = None


class Users(DictModel):
    root: Dict[str, User]


class SnowbirdUsers(Users):
    root: Dict[str, SnowbirdUser]


class SnowbirdShare(BaseModel):
    owner: str = None
    consumers: List[str] = None
    privileges: Privileges = None


class SnowbirdShares(DictModel):
    root: Dict[str, SnowbirdShare]


class PermifrostModel(BaseModel):
    databases: Optional[List[Databases]] = None
    warehouses: Optional[List[Warehouses]] = None
    roles: Optional[List[Roles]] = None
    users: Optional[List[Users]] = None


class SnowbirdModel(PermifrostModel):
    databases: Optional[List[SnowbirdDatabases]] = None
    warehouses: Optional[List[SnowbirdWarehouses]] = None
    roles: Optional[List[SnowbirdRoles]] = None
    users: Optional[List[SnowbirdUsers]] = None
    shares: Optional[List[SnowbirdShares]] = None
