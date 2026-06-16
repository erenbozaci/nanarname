from django.test import TestCase
from django.urls import reverse
from .models import Movie

class BasicTest(TestCase):
    def test_index_page_status_code(self):
        """Ana sayfanın 200 döndürdüğünü doğrula."""
        response = self.client.get(reverse('movies:index'))
        self.assertEqual(response.status_code, 200)

    def test_toxic_utils_importable(self):
        """toxic_utils modülünün model dosyası olmasa bile yüklenebildiğini doğrula."""
        from .toxic_utils import predict_text, leetspeak_to_normal
        text = "s@l4k"
        normalized = leetspeak_to_normal(text)
        self.assertEqual(normalized, "salak")
