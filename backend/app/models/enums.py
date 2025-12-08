from enum import Enum


class Visibility(str, Enum):
    private = "private"
    workspace = "workspace"
    public = "public"


class MemberRole(str, Enum):
    admin = "admin"
    member = "member"
    observer = "observer"