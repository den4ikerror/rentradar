# Інструкція з розгортання RentFinder (24/7, безкоштовно)

Ця інструкція описує найпростіші та найактуальніші способи безкоштовного хостингу RentFinder із забезпеченням роботи 24/7.

Оскільки бекенд містить фоновий планувальник (APScheduler), який періодично сканує сайти (OLX, Dom.RIA, Lun.ua, Rieltor, Flatfy) та базу даних SQLite, найкраще обирати платформи, які підтримують постійні процеси або невеликі VPS.

---

## Варіант 1: Render.com (Безкоштовний Web Service + Persistent Disk)
Render надає безкоштовний тариф для вебсервісів (з обмеженням "системи засинають" при відсутності запитів, але планувальник усередині FastAPI піднімається при новому запиті, або можна налаштувати зовнішній пінґер на кшталт UptimeRobot).

1. **Репозиторій:** Запустіть проєкт на GitHub (якщо ще не зроблено).
2. **Створення сервісу на Render:**
   - Зайдіть на [render.com](https://render.com) та підключіть GitHub-акаунт.
   - Натисніть **New +** -> **Web Service**.
   - Оберіть ваш репозиторій `rentfinder`.
3. **Налаштування збірки (Build & Run):**
   - **Root Directory:** `backend`
   - **Environment:** `Python 3`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `uvicorn main:app --host 0.0.0.0 --port $PORT`
4. **Змінні середовища (Environment Variables):**
   - `ENABLED_SOURCES` = `olx,domria,lunua,rieltor,flatfy`
   - `NOMINATIM_CONTACT_EMAIL` = ваш email
5. **Фронтенд:**
   - Можна розгорнути фронтенд окремо як **Static Site** на Render (Root Directory: `frontend`, Build Command: `npm install && npm run build`, Publish Directory: `dist`), у файлі `frontend/src/api.js` вказавши URL вашого бекенду на Render.

---

## Варіант 2: Railway.app (Найзручніший та найстабільніший)
Railway має мінімальний безкоштовний ліміт і чудово тримає постійні Python-бекенди та SQLite бази даних без засинання.

1. Зайдіть на [railway.app](https://railway.app) через GitHub.
2. Створіть новий проєкт (**New Project**) -> **Deploy from GitHub repo**.
3. Оберіть папку `backend` як корінь сервісу (або увесь репозиторій, налаштувавши Start Command: `cd backend && uvicorn main:app --host 0.0.0.0 --port $PORT`).
4. Додайте змінні середовища в панелі Railway (`ENABLED_SOURCES=olx,domria,lunua,rieltor,flatfy`).

---

## Варіант 3: VPS на Oracle Cloud (Always Free — 24/7 без жодних обмежень)
Якщо вам потрібен повністю безкоштовний повноцінний сервер (VPS) з Linux, який ніколи не засинає і працює 24/7 без обмежень:
1. Зареєструйтесь на Oracle Cloud (тариф **Always Free** надає до 4 ARM віртуальних машин з 24 GB RAM абсолютно безкоштовно назавжди).
2. Створіть Ubuntu VPS (ARM Ampere).
3. Підключіться по SSH, встановіть Python, Git та Node.js:
   ```bash
   sudo apt update && sudo apt install -y python3-pip python3-venv git nodejs npm
   ```
4. Клонуйте репозиторій:
   ```bash
   git clone <ваш-репозиторій> rentfinder
   cd rentfinder
   ```
5. Запустіть бекенд через `systemd` або `pm2` / `screen`, а фронтенд зіберіть через `npm run build` і підключіть через Nginx.
