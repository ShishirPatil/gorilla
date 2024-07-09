from enum import Enum


class CustomEnum(Enum):
    @classmethod
    def add(cls, other):
        combined_members = {member.name: member.value for member in cls}
        combined_members.update({member.name: member.value for member in other})
        return __class__(cls.__name__, combined_members)
    
    @classmethod
    def subtract(cls, other):
        remaining_members = {
            member.name: member.value 
            for member in cls if member.value not in other._value2member_map_
        }
        return __class__(cls.__name__, remaining_members)
    
    @classmethod
    def rename(cls, new_name):
        members = {member.name: member.value for member in cls}
        return __class__(new_name, members)

    @classmethod
    def update(cls, new_members):
        members = {member.name: member.value for member in cls}
        members.update(new_members)
        return __class__(cls.__name__, members)