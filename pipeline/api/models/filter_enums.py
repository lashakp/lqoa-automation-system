from enum import Enum


class IndustryEnum(str, Enum):

    fintech = "Fintech"

    healthcare = "Healthcare"

    ai = "Artificial Intelligence"

    saas = "SaaS"

    ecommerce = "E-commerce"

    education = "Education"


class BatchEnum(str, Enum):

    winter_2024 = "Winter 2024"

    summer_2024 = "Summer 2024"

    winter_2025 = "Winter 2025"

    summer_2025 = "Summer 2025"

    winter_2026 = "Winter 2026"


class LocationEnum(str, Enum):

    san_francisco = "San Francisco"

    new_york = "New York"

    london = "London"

    toronto = "Toronto"

    remote = "Remote"
