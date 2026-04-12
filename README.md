# EksiCaciklar (Django)

Bu branch, projeyi ASP.NET MVC'den Python/Django yapısına taşır.

## Kurulum

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

## Ana URL'ler

- `/movies/` film listesi
- `/accounts/login/` giriş
- `/accounts/register/` kayıt
- `/movies/users/` kullanıcı rol yönetimi (admin)
