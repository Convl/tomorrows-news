from enum import Enum


class ScrapingSourceEnum(Enum):
    WEBPAGE = "Webpage"
    RSS = "Rss"
    API = "Api"


def get_enum_values(enum) -> list:
    """Helper function to ensure SqlAlchemy uses Enum values instead of names"""
    return [member.value for member in enum]
