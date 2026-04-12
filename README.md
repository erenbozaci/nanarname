# Nanarname

### Branchlerimiz
`nanarname`: Ana sistemizin olduğu branch<br>
`toxic-model`: Toksisite modelimizi eğittiğimiz ve test ettiğimiz branch.

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
