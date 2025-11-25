from enum import Enum

class Visibility(str, Enum):
    PRIVATE = "private"
    WORKSPACE = "workspace"
    PUBLIC = "public"

class Role(str, Enum):
    ADMIN = "admin"
    MEMBER = "member"
    OBSERVER = "observer"