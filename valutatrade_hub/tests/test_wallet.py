import pytest
from valutatrade_hub.core.models import Wallet


class TestWalletInit:
    def test_valid_init_default_balance(self):
        w = Wallet("USD")
        assert w.currency_code == "USD"
        assert w.balance == 0.0

    def test_valid_init_with_balance(self):
        w = Wallet("BTC", 0.5)
        assert w.currency_code == "BTC"
        assert w.balance == pytest.approx(0.5)

    def test_currency_code_normalization(self):
        w = Wallet("  btc ")
        assert w.currency_code == "BTC"

    def test_invalid_currency_code_raises(self):
        with pytest.raises(ValueError, match="непустой строкой"):
            Wallet("")
        with pytest.raises(ValueError, match="непустой строкой"):
            Wallet(None)  # type: ignore

    def test_initial_balance_validation_via_setter(self):
        with pytest.raises(ValueError, match="не может быть отрицательным"):
            Wallet("USD", -10.0)

        with pytest.raises(TypeError, match="числом"):
            Wallet("USD", "100")  # type: ignore


class TestBalanceProperty:
    def test_getter_returns_current_balance(self):
        w = Wallet("EUR", 50.0)
        assert w.balance == pytest.approx(50.0)

    def test_setter_rejects_negative_value(self):
        w = Wallet("JPY", 100.0)
        with pytest.raises(ValueError, match="не может быть отрицательным"):
            w.balance = -1.0

    def test_setter_accepts_int_and_float(self):
        w = Wallet("CHF", 0.0)
        w.balance = 10      # int
        w.balance = 20.5    # float
        assert w.balance == pytest.approx(20.5)

    def test_setter_converts_to_float(self):
        w = Wallet("CAD", 0.0)
        w.balance = 5
        assert isinstance(w.balance, float)
        assert w.balance == pytest.approx(5.0)


class TestDeposit:
    def test_deposit_positive_amount(self):
        w = Wallet("GBP", 100.0)
        w.deposit(50.0)
        assert w.balance == pytest.approx(150.0)

    def test_deposit_int_amount(self):
        w = Wallet("AUD", 200.0)
        w.deposit(25)
        assert w.balance == pytest.approx(225.0)

    def test_deposit_zero_raises(self):
        w = Wallet("SEK", 300.0)
        with pytest.raises(ValueError, match="положительным числом"):
            w.deposit(0)

    def test_deposit_negative_raises(self):
        w = Wallet("NZD", 400.0)
        with pytest.raises(ValueError, match="положительным числом"):
            w.deposit(-10.0)

    def test_deposit_invalid_type_raises(self):
        w = Wallet("HKD", 500.0)
        with pytest.raises(TypeError, match="числом"):
            w.deposit("100")  # type: ignore


class TestWithdraw:
    def test_withdraw_success(self):
        w = Wallet("RUB", 1000.0)
        result = w.withdraw(300.0)
        assert result is True
        assert w.balance == pytest.approx(700.0)

    def test_withdraw_insufficient_funds_returns_false(self):
        w = Wallet("CNY", 50.0)
        result = w.withdraw(100.0)
        assert result is False
        # Баланс не должен измениться
        assert w.balance == pytest.approx(50.0)

    def test_withdraw_zero_raises(self):
        w = Wallet("INR", 200.0)
        with pytest.raises(ValueError, match="положительным числом"):
            w.withdraw(0)

    def test_withdraw_negative_raises(self):
        w = Wallet("BRL", 300.0)
        with pytest.raises(ValueError, match="положительным числом"):
            w.withdraw(-50.0)

    def test_withdraw_invalid_type_raises(self):
        w = Wallet("ZAR", 400.0)
        with pytest.raises(TypeError, match="числом"):
            w.withdraw("50")  # type: ignore

    def test_withdraw_exact_balance_success(self):
        w = Wallet("TRY", 123.45)
        result = w.withdraw(123.45)
        assert result is True
        assert w.balance == pytest.approx(0.0)


class TestGetBalanceInfo:
    def test_get_balance_info_format(self):
        w = Wallet("PLN", 99.99)
        info = w.get_balance_info()
        assert isinstance(info, dict)
        assert info["currency_code"] == "PLN"
        assert info["balance"] == pytest.approx(99.99)

    def test_get_balance_info_after_operations(self):
        w = Wallet("SGD", 10.0)
        w.deposit(5.5)
        w.withdraw(2.0)
        
        info = w.get_balance_info()
        assert info["balance"] == pytest.approx(13.5)
