from services.anti_realtor import is_agency


class TestIsAgency:
    def test_agency_keyword_detected(self):
        assert is_agency("Здам квартиру", "Звертайтесь в наше агентство нерухомості", "unknown") is True

    def test_company_seller_type_detected(self):
        assert is_agency("Здам квартиру", "Гарна квартира", "company") is True

    def test_private_owner_passes(self):
        assert is_agency("Здам квартиру", "Здаю власну квартиру, без посередників", "private") is False

    def test_exclusion_phrase_overrides_agency_keyword(self):
        # Навіть якщо десь у тексті є слово "агентство" (напр. в описі району),
        # явне "виключно власник" повинно переважати.
        text = "Виключно власник. Комісія агентствам не сплачується."
        assert is_agency("Здам квартиру", text, "unknown") is False

    def test_no_signal_defaults_to_private(self):
        assert is_agency("Здам квартиру", "Простора, тепла, світла", "unknown") is False
