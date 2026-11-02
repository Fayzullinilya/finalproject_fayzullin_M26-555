import pytest
from valutatrade_hub.core.models import Portfolio, Wallet


class TestPortfolioInit:
    def test_valid_init_with_user_id(self):
        p = Portfolio(user_id=1)
        assert p.user_id == 1
        assert p.wallets == {}

    def test_init_with_existing_wallets(self):
        w_usd = Wallet("USD", 100.0)
        w_btc = Wallet("BTC", 0.5)
        p = Portfolio(user_id=2, wallets={"USD": w_usd, "BTC": w_btc})
        assert p.user_id == 2
        assert "USD" in p.wallets
        assert "BTC" in p.wallets
        assert p.wallets["USD"].balance == 100.0
        assert p.wallets["BTC"].balance == 0.5

    def test_invalid_user_id_raises(self):
        with pytest.raises(ValueError):
            Portfolio(user_id=-1)
        with pytest.raises(ValueError):
            Portfolio(user_id=0)
        with pytest.raises(ValueError):
            Portfolio(user_id="1")  # type: ignore


class TestAddCurrency:
    def test_add_new_currency(self):
        p = Portfolio(user_id=1)
        p.add_currency("EUR")
        assert "EUR" in p.wallets
        assert p.wallets["EUR"].currency_code == "EUR"
        assert p.wallets["EUR"].balance == 0.0

    def test_add_currency_with_whitespace_and_lowercase(self):
        p = Portfolio(user_id=1)
        p.add_currency("  btc ")
        assert "BTC" in p.wallets

    def test_add_existing_currency_raises(self):
        p = Portfolio(user_id=1)
        p.add_currency("USD")
        with pytest.raises(ValueError, match="уже существует"):
            p.add_currency("usd")

    def test_add_invalid_currency_code_raises(self):
        p = Portfolio(user_id=1)
        with pytest.raises(ValueError):
            p.add_currency("")
        with pytest.raises(ValueError):
            p.add_currency(None)  # type: ignore


class TestGetWallet:
    def test_get_existing_wallet(self):
        p = Portfolio(user_id=1)
        p.add_currency("GBP")
        wallet = p.get_wallet("GBP")
        assert wallet is not None
        assert wallet.currency_code == "GBP"

    def test_get_nonexistent_wallet_returns_none(self):
        p = Portfolio(user_id=1)
        wallet = p.get_wallet("JPY")
        assert wallet is None

    def test_get_wallet_case_insensitive(self):
        p = Portfolio(user_id=1)
        p.add_currency("eur")
        wallet = p.get_wallet("EUR")
        assert wallet is not None


class TestTotalValueStrictMode:
    """Тесты под строгую логику get_total_value: ошибка, если нет курса."""

    def test_total_value_single_currency_usd_base(self):
        p = Portfolio(user_id=1)
        p.add_currency("USD")
        p.wallets["USD"].deposit(1000.0)

        total = p.get_total_value(base_currency="USD")
        # 1000 USD * 1.0 / 1.0 = 1000
        assert total == pytest.approx(1000.0, rel=1e-6)

    def test_total_value_multiple_currencies_usd_base(self):
        p = Portfolio(user_id=1)
        p.add_currency("USD")
        p.add_currency("BTC")
        p.wallets["USD"].deposit(500.0)
        p.wallets["BTC"].deposit(0.01)

        # Курсы: BTC=42000, USD=1.0
        expected = 500 + (0.01 * 42000)  # 500 + 420 = 920
        total = p.get_total_value(base_currency="USD")
        assert total == pytest.approx(expected, rel=1e-6)

    def test_total_value_different_base_currency(self):
        p = Portfolio(user_id=1)
        p.add_currency("USD")
        p.wallets["USD"].deposit(220.0)

        # base_currency = EUR (курс 1.1), значит 220 USD = 220 / 1.1 = 200 EUR
        total = p.get_total_value(base_currency="EUR")
        assert total == pytest.approx(200.0, rel=1e-6)

    def test_unknown_base_currency_raises(self):
        p = Portfolio(user_id=1)
        with pytest.raises(ValueError, match="не задан"):
            p.get_total_value(base_currency="XYZ")

    def test_missing_rate_for_currency_in_portfolio_raises(self):
        """Если в портфеле есть валюта без курса — должна быть ошибка."""
        p = Portfolio(user_id=1)
        p.add_currency("XYZ")  # XYZ нет в _exchange_rates
        p.wallets["XYZ"].deposit(1_000_000)

        with pytest.raises(ValueError, match="Курс для валюты XYZ не задан"):
            p.get_total_value("USD")

    def test_all_currencies_present_no_error(self):
        """Когда у всех валют есть курс — ошибка не должна возникать."""
        p = Portfolio(user_id=1)
        p.add_currency("USD")
        p.add_currency("EUR")
        p.wallets["USD"].deposit(100.0)
        p.wallets["EUR"].deposit(100.0)

        # Оба курса есть в _exchange_rates, ошибка не должна быть
        total = p.get_total_value("USD")
        assert total > 0


class TestWalletsProperty:
    def test_wallets_returns_copy(self):
        p = Portfolio(user_id=1)
        p.add_currency("CAD")
        original_keys = list(p.wallets.keys())
        # Меняем копию снаружи — это не должно менять внутреннее состояние
        p.wallets.clear()
        assert list(p.wallets.keys()) == original_keys

    def test_wallets_does_not_allow_direct_replacement(self):
        p = Portfolio(user_id=1)
        new_dict = {"USD": Wallet("USD", 10.0)}
        with pytest.raises(AttributeError):
            p.wallets = new_dict  # type: ignore
