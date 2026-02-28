"""Micro-tests for inline keyboard builders."""

from app.keyboards.inline import cities_keyboard


class TestCitiesKeyboard:
    def _cities(self, n: int = 3) -> list[dict]:
        return [{"id": i, "name": f"City{i}", "country": "RU"} for i in range(1, n + 1)]

    def test_one_button_per_city(self):
        kb = cities_keyboard(self._cities(3))
        buttons = [btn for row in kb.inline_keyboard for btn in row]
        assert len(buttons) == 3

    def test_button_text_contains_name_and_country(self):
        kb = cities_keyboard([{"id": 1, "name": "Moscow", "country": "RU"}])
        button = kb.inline_keyboard[0][0]
        assert "Moscow" in button.text
        assert "RU" in button.text

    def test_callback_data_format(self):
        kb = cities_keyboard([{"id": 42, "name": "Kazan", "country": "RU"}])
        button = kb.inline_keyboard[0][0]
        assert button.callback_data == "city_select:42:Kazan"

    def test_max_eight_cities(self):
        kb = cities_keyboard(self._cities(12))
        buttons = [btn for row in kb.inline_keyboard for btn in row]
        assert len(buttons) == 8

    def test_no_country_shows_name_only(self):
        kb = cities_keyboard([{"id": 1, "name": "Berlin", "country": ""}])
        button = kb.inline_keyboard[0][0]
        assert button.text == "Berlin"

    def test_empty_list_returns_empty_keyboard(self):
        kb = cities_keyboard([])
        buttons = [btn for row in kb.inline_keyboard for btn in row]
        assert len(buttons) == 0
