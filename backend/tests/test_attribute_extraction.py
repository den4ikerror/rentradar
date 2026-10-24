from services.attribute_extraction import extract_attributes, passes_soft_filter
from types import SimpleNamespace


def make_filter(**kwargs):
    """Мінімальна заглушка SearchFilter — passes_soft_filter читає лише атрибути з kwargs."""
    defaults = dict(
        property_types=[], furnished_only=False, is_new_building=False, heating_type=None,
        has_elevator=False, has_parking=False, has_balcony=False,
        internet_included=False, utilities_included=False,
        deposit_required=None, min_lease_months=None,
    )
    defaults.update(kwargs)
    return SimpleNamespace(**defaults)


class TestExtractAttributes:
    def test_studio_detected(self):
        attrs = extract_attributes("Здам студію в центрі", "Затишна студія з ремонтом")
        assert attrs["property_type"] == "studio"

    def test_apartment_default(self):
        attrs = extract_attributes("Здам 2-кімнатну квартиру", "Гарна квартира біля метро")
        assert attrs["property_type"] == "apartment"

    def test_furnished_positive(self):
        attrs = extract_attributes("Оренда", "Квартира повністю умебльована, є все необхідне")
        assert attrs["furnished"] is True

    def test_furnished_negative(self):
        attrs = extract_attributes("Оренда", "Здається без меблів, порожня квартира")
        assert attrs["furnished"] is False

    def test_furnished_unknown_when_not_mentioned(self):
        attrs = extract_attributes("Оренда", "Гарна квартира з ремонтом, тепла і світла")
        assert attrs["furnished"] is None

    def test_elevator_detected(self):
        attrs = extract_attributes("Оренда", "9 поверх, є ліфт, консьєрж")
        assert attrs["has_elevator"] is True

    def test_no_deposit_detected(self):
        attrs = extract_attributes("Оренда", "Здаю без застави, тільки оплата за місяць")
        assert attrs["deposit_required"] is False

    def test_deposit_detected(self):
        attrs = extract_attributes("Оренда", "Потрібна застава в розмірі місячної оплати")
        assert attrs["deposit_required"] is True

    def test_heating_autonomous(self):
        attrs = extract_attributes("Оренда", "Автономне опалення, тепло взимку")
        assert attrs["heating_type"] == "autonomous"

    def test_min_lease_months_extracted(self):
        attrs = extract_attributes("Оренда", "Здаю мінімум на 6 місяців")
        assert attrs["min_lease_months"] == 6


class TestPassesSoftFilter:
    def test_no_requirements_always_passes(self):
        f = make_filter()
        attrs = extract_attributes("Оренда", "Без жодних деталей")
        assert passes_soft_filter(f, attrs) is True

    def test_furnished_required_and_confirmed_passes(self):
        f = make_filter(furnished_only=True)
        attrs = extract_attributes("Оренда", "З меблями, все включено")
        assert passes_soft_filter(f, attrs) is True

    def test_furnished_required_but_explicitly_absent_fails(self):
        f = make_filter(furnished_only=True)
        attrs = extract_attributes("Оренда", "Без меблів, порожня")
        assert passes_soft_filter(f, attrs) is False

    def test_furnished_required_but_not_mentioned_still_passes(self):
        """Ключова поведінка: відсутність згадки НЕ повинна відкидати оголошення —
        інакше строгий фільтр вирізав би більшість валідних варіантів."""
        f = make_filter(furnished_only=True)
        attrs = extract_attributes("Оренда", "Гарна квартира з ремонтом")
        assert passes_soft_filter(f, attrs) is True

    def test_property_type_mismatch_fails(self):
        f = make_filter(property_types=["studio"])
        attrs = extract_attributes("2-кімнатна квартира", "Простора квартира")
        assert passes_soft_filter(f, attrs) is False

    def test_property_type_match_passes(self):
        f = make_filter(property_types=["studio", "apartment"])
        attrs = extract_attributes("Здам студію", "Компактна студія")
        assert passes_soft_filter(f, attrs) is True

    def test_deposit_mismatch_fails(self):
        f = make_filter(deposit_required=False)
        attrs = extract_attributes("Оренда", "Потрібна застава")
        assert passes_soft_filter(f, attrs) is False

    def test_min_lease_too_long_fails(self):
        f = make_filter(min_lease_months=3)
        attrs = extract_attributes("Оренда", "Здаю мінімум на 12 місяців")
        assert passes_soft_filter(f, attrs) is False

    def test_min_lease_within_limit_passes(self):
        f = make_filter(min_lease_months=12)
        attrs = extract_attributes("Оренда", "Здаю мінімум на 3 місяці")
        assert passes_soft_filter(f, attrs) is True
