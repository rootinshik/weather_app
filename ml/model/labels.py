from dataclasses import dataclass, field


@dataclass
class ClothingCategory:
    name: str
    description: str
    items: list[str]


CLOTHING_CATEGORIES: dict[str, ClothingCategory] = {
    "light_summer": ClothingCategory(
        name="light_summer",
        description="Очень жарко — лёгкая летняя одежда",
        items=["футболка", "шорты", "сандалии", "солнечные очки", "кепка"],
    ),
    "moderate_warm": ClothingCategory(
        name="moderate_warm",
        description="Тепло — повседневная одежда без верхней",
        items=["лёгкая рубашка", "джинсы или брюки", "кроссовки"],
    ),
    "light_jacket": ClothingCategory(
        name="light_jacket",
        description="Прохладно — лёгкая верхняя одежда",
        items=["ветровка или лёгкая куртка", "джинсы", "кроссовки"],
    ),
    "warm_dry": ClothingCategory(
        name="warm_dry",
        description="Холодно и сухо — тёплая одежда",
        items=["тёплая куртка", "свитер", "джинсы", "закрытая обувь"],
    ),
    "warm_rain": ClothingCategory(
        name="warm_rain",
        description="Холодно и дождливо — непромокаемая одежда",
        items=["непромокаемая куртка", "свитер", "джинсы", "резиновые сапоги", "зонт"],
    ),
    "winter_light": ClothingCategory(
        name="winter_light",
        description="Лёгкий мороз — зимняя одежда",
        items=["зимняя куртка", "тёплый свитер", "тёплые брюки", "зимние ботинки", "шапка", "перчатки"],
    ),
    "winter_heavy": ClothingCategory(
        name="winter_heavy",
        description="Сильный мороз — тёплая зимняя одежда",
        items=[
            "пуховик",
            "тёплый свитер",
            "термобельё",
            "зимние брюки",
            "зимние ботинки",
            "шапка",
            "шарф",
            "тёплые перчатки",
        ],
    ),
    "winter_extreme": ClothingCategory(
        name="winter_extreme",
        description="Экстремальный мороз — максимальное утепление",
        items=[
            "тёплый пуховик",
            "термобельё",
            "флисовый свитер",
            "зимние брюки на утеплителе",
            "валенки или тёплые зимние ботинки",
            "меховая шапка",
            "тёплый шарф",
            "варежки",
        ],
    ),
}

LABEL_NAMES: list[str] = list(CLOTHING_CATEGORIES.keys())
