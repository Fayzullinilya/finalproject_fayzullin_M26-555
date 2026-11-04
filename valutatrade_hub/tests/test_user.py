import pytest
from datetime import datetime, timezone
import secrets
import hashlib
from valutatrade_hub.core.models import User


class TestUserInit:
    def test_valid_init(self):
        salt = secrets.token_hex(16)
        pwd_plain = "strongpassword123"
        byte_str = (pwd_plain + salt).encode("utf-8")
        hashed = hashlib.sha256(byte_str).hexdigest()

        u = User(user_id=1, username="alice", hashed_password=hashed, salt=salt)
        assert u.user_id == 1
        assert u.username == "alice"
        assert u.hashed_password == hashed
        assert u.salt == salt
        assert isinstance(u.registration_date, datetime)

    def test_invalid_user_id_raises(self):
        salt = secrets.token_hex(16)
        pwd_plain = "strongpassword123"
        byte_str = (pwd_plain + salt).encode("utf-8")
        pwd = hashlib.sha256(byte_str).hexdigest()  # заглушка
        with pytest.raises(ValueError, match="положительным целым числом"):
            User(user_id=-1, username="bob", hashed_password=pwd, salt=salt)
        with pytest.raises(ValueError, match="положительным целым числом"):
            User(user_id=0, username="bob", hashed_password=pwd, salt=salt)

    def test_username_normalization_and_validation(self):
        salt = secrets.token_hex(16)
        pwd_plain = "strongpassword123"
        byte_str = (pwd_plain + salt).encode("utf-8")
        pwd = hashlib.sha256(byte_str).hexdigest()  # заглушка
        u = User(user_id=2, username="  bob  ", hashed_password=pwd, salt=salt)
        assert u.username == "bob"

        with pytest.raises(ValueError, match="не может быть пустым"):
            User(user_id=3, username="", hashed_password=pwd, salt=salt)
        with pytest.raises(ValueError, match="не может быть пустым"):
            User(user_id=4, username="   ", hashed_password=pwd, salt=salt)

    def test_hashed_password_validation(self):
        salt = secrets.token_hex(16)
        # Слишком короткий хеш
        with pytest.raises(ValueError, match="SHA‑256 хешем"):
            User(user_id=5, username="carol", hashed_password="short", salt=salt)
        # Пустой хеш
        with pytest.raises(ValueError, match="SHA‑256 хешем"):
            User(user_id=6, username="dave", hashed_password="", salt=salt)

    def test_salt_validation(self):
        pwd = hashlib.sha256("x".encode("utf-8")).hexdigest()
        # Соль короче 32 символов
        with pytest.raises(ValueError, match="32 hex-символа"):
            User(user_id=7, username="eve", hashed_password=pwd, salt="short")
        # Пустая соль
        with pytest.raises(ValueError, match="32 hex-символа"):
            User(user_id=8, username="frank", hashed_password=pwd, salt="")

    def test_registration_date_default(self):
        salt = secrets.token_hex(16)
        pwd_plain = "strongpassword123"
        byte_str = (pwd_plain + salt).encode("utf-8")
        pwd = hashlib.sha256(byte_str).hexdigest()  # заглушка
        u = User(user_id=9, username="grace", hashed_password=pwd, salt=salt)
        assert isinstance(u.registration_date, datetime)
        assert u.registration_date.tzinfo is not None  # UTC

    def test_registration_date_custom(self):
        salt = secrets.token_hex(16)
        byte_str = ('p' + salt).encode("utf-8")
        pwd = hashlib.sha256(byte_str).hexdigest()  # заглушка
        dt = datetime(2020, 1, 15, 10, 20, tzinfo=timezone.utc)
        u = User(
            user_id=10,
            username="heidi",
            hashed_password=pwd,
            salt=salt,
            registration_date=dt,
        )
        assert u.registration_date == dt

    def test_registration_date_future_raises(self):
        salt = secrets.token_hex(16)
        byte_str = ('p' + salt).encode("utf-8")
        pwd = hashlib.sha256(byte_str).hexdigest()  # заглушка
        now = datetime.now(timezone.utc)
        future = now.replace(year=now.year + 1)
        with pytest.raises(ValueError, match="в будущем"):
            User(
                user_id=11,
                username="ivan",
                hashed_password=pwd,
                salt=salt,
                registration_date=future,
            )


class TestPasswordMethods:
    @pytest.fixture
    def user(self):
        salt = secrets.token_hex(16)
        pwd_plain = "initialpass123"
        byte_str = (pwd_plain + salt).encode("utf-8")
        hashed = hashlib.sha256(byte_str).hexdigest()
        return User(user_id=12, username="jane", hashed_password=hashed, salt=salt)

    def test_verify_password_correct(self, user):
        assert user.verify_password("initialpass123") is True

    def test_verify_password_wrong(self, user):
        assert user.verify_password("wrongpassword") is False

    def test_verify_password_too_short_returns_false(self, user):
        # По логике метода: если длина < 4 — сразу False
        assert user.verify_password("abc") is False
        assert user.verify_password("") is False

    def test_change_password_generates_new_salt_and_hash(self, user):
        old_salt = user.salt
        old_hash = user.hashed_password

        user.change_password("newstrongpass456")

        # Соль должна измениться
        assert user.salt != old_salt
        # Хеш должен измениться
        assert user.hashed_password != old_hash
        # Новый пароль должен подходить
        assert user.verify_password("newstrongpass456") is True
        # Старый пароль не должен подходить
        assert user.verify_password("initialpass123") is False

    def test_change_password_invalid_length_raises(self, user):
        with pytest.raises(ValueError, match="не менее 4 символов"):
            user.change_password("abc")
        with pytest.raises(ValueError, match="не менее 4 символов"):
            user.change_password("")


class TestGetUserInfo:
    def test_get_user_info_excludes_password_and_salt(self):
        salt = secrets.token_hex(16)
        pwd_plain = "secret123"
        byte_str = (pwd_plain + salt).encode("utf-8")
        hashed = hashlib.sha256(byte_str).hexdigest()
        u = User(user_id=13, username="kate", hashed_password=hashed, salt=salt)

        info = u.get_user_info()
        assert info["user_id"] == 13
        assert info["username"] == "kate"
        assert "registration_date" in info
        assert "hashed_password" not in info
        assert "salt" not in info

    def test_get_user_info_registration_date_isoformat(self):
        salt = secrets.token_hex(16)
        byte_str = ('p' + salt).encode("utf-8")
        pwd = hashlib.sha256(byte_str).hexdigest()
        u = User(user_id=14, username="leo", hashed_password=pwd, salt=salt)
        info = u.get_user_info()
        date_str = info["registration_date"]
        # Должно быть валидным ISO-форматом (с часовым поясом)
        datetime.fromisoformat(date_str)

class TestFromDict:
    def test_from_dict_valid_iso_with_z(self):
        data = {
            "user_id": 42,
            "username": "alice",
            "hashed_password": "a" * 64,
            "salt": "b" * 32,
            "registration_date": "2025-10-09T10:30:00Z"
        }
        user = User.from_dict(data)

        assert user.user_id == 42
        assert user.username == "alice"
        assert user.hashed_password == data["hashed_password"]
        assert user.salt == data["salt"]
        assert user.registration_date.tzinfo is not None
        # Проверка, что Z корректно преобразовался в UTC
        assert user.registration_date == datetime(2025, 10, 9, 10, 30, tzinfo=timezone.utc)

    def test_from_dict_valid_iso_without_z(self):
        data = {
            "user_id": 77,
            "username": "bob",
            "hashed_password": "a" * 64,
            "salt": "b" * 32,
            "registration_date": "2025-01-01T12:00:00+02:00"
        }
        user = User.from_dict(data)
        assert user.user_id == 77
        assert user.registration_date.strftime("%Y-%m-%dT%H:%M:%S%z") == "2025-01-01T12:00:00+0200"

    def test_from_dict_missing_registration_date_uses_default(self):
        data = {
            "user_id": 88,
            "username": "carol",
            "hashed_password": "a" * 64,
            "salt": "b" * 32
        }
        user = User.from_dict(data)
        assert user.registration_date is not None
        assert user.registration_date.tzinfo is not None

    def test_from_dict_invalid_date_raises_value_error(self):
        data = {
            "user_id": 99,
            "username": "dave",
            "hashed_password": "a" * 64,
            "salt": "b" * 32,
            "registration_date": "not-a-date"
        }
        with pytest.raises(ValueError, match="Некорректный формат"):
            User.from_dict(data)

    def test_from_dict_missing_required_fields_raises(self):
        # Не хватает user_id
        data_no_id = {
            "username": "eve",
            "hashed_password": "a" * 64,
            "salt": "b" * 32,
            "registration_date": "2025-01-01T00:00:00Z"
        }
        with pytest.raises(KeyError):
            User.from_dict(data_no_id)

        # Не хватает hashed_password
        data_no_pwd = {
            "user_id": 101,
            "username": "frank",
            "salt": "b" * 32,
            "registration_date": "2025-01-01T00:00:00Z"
        }
        with pytest.raises(KeyError):
            User.from_dict(data_no_pwd)


class TestToDict:
    @pytest.fixture
    def user(self):
        now = datetime.now(timezone.utc)
        return User(
            user_id=123,
            username="grace",
            hashed_password="a" * 64,
            salt="b" * 32,
            registration_date=now
        )

    def test_to_dict_contains_all_fields(self, user):
        d = user.to_dict()
        assert d["user_id"] == 123
        assert d["username"] == "grace"
        assert d["hashed_password"] == "a" * 64
        assert d["salt"] == "b" * 32
        # registration_date должен быть строкой ISO
        assert isinstance(d["registration_date"], str)
        parsed = datetime.fromisoformat(d["registration_date"])
        assert parsed.tzinfo is not None

    def test_to_dict_roundtrip_with_from_dict(self, user):
        original_date = user.registration_date
        d = user.to_dict()
        restored = User.from_dict(d)

        assert restored.user_id == user.user_id
        assert restored.username == user.username
        assert restored.hashed_password == user.hashed_password
        assert restored.salt == user.salt
        # Даты должны совпадать (с точностью до микросекунд)
        assert restored.registration_date == original_date

    def test_to_dict_does_not_drop_secrets_for_storage(self, user):
        d = user.to_dict()
        assert "hashed_password" in d
        assert "salt" in d
