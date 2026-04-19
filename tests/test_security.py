import pytest
from app.core.security import encrypt_data, decrypt_data

pytestmark = pytest.mark.asyncio

class TestSecurityEncryption:
    """اختبارات تشفير وفك التشفير باستخدام Fernet."""

    def test_encrypt_and_decrypt_string(self):
        """تشفير نص ثم فك تشفيره والتأكد من مطابقتة للأصل."""
        original_data = "Bank Account: 123456789"
        encrypted = encrypt_data(original_data)

        assert encrypted != original_data  # النص المشفر مختلف
        assert isinstance(encrypted, str)

        decrypted = decrypt_data(encrypted)
        assert decrypted == original_data

    def test_encrypt_different_outputs_same_input(self):
        """التأكد من أن التشفير يعطي نتائج مختلفة لنفس المدخلات (بسبب IV)."""
        data = "Secret Message"
        encrypted1 = encrypt_data(data)
        encrypted2 = encrypt_data(data)

        assert encrypted1 != encrypted2  # يجب أن يكونا مختلفين

        # لكن فك التشفير يعطي نفس النتيجة
        assert decrypt_data(encrypted1) == data
        assert decrypt_data(encrypted2) == data

    def test_decrypt_invalid_token_raises_error(self):
        """محاولة فك تشفير نص غير صالح يجب أن ترفع استثناء."""
        invalid_token = "invalid-token-string"
        with pytest.raises(Exception):
            decrypt_data(invalid_token)

    def test_empty_string_encryption(self):
        """تشفير نص فارغ."""
        data = ""
        encrypted = encrypt_data(data)
        decrypted = decrypt_data(encrypted)
        assert decrypted == data

    def test_special_characters_encryption(self):
        """تشفير نصوص تحتوي على أحرف خاصة."""
        data = "Special!@#$%^&*()_+{}|:<>?"
        encrypted = encrypt_data(data)
        decrypted = decrypt_data(encrypted)
        assert decrypted == data

    def test_long_string_encryption(self):
        """تشفير نص طويل جداً."""
        data = "A" * 10000
        encrypted = encrypt_data(data)
        decrypted = decrypt_data(encrypted)
        assert decrypted == data
