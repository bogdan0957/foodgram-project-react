# ПРОЕКТ ФУДГРАММ. 

![example workflow](https://github.com/bogdan0957/foodgram-project-react/actions/workflows/main.yml/badge.svg)

## Проект "Проект Фудграм" разработан на языке программирования Python, с использованием фреймворка Django и библиотеки Django REST framework.

### Описание проекта:
Продуктовый помощник - это веб-приложение, предназначенное для удобного и эффективного управления покупками и списками продуктов. Он позволяет пользователям создавать и управлять списками покупокб, создавать рецепты, отслеживать авторов рецептов и контролировать запасы продуктов в доме.

### Основные функциональные возможности:
1. Регистрация и аутентификация пользователя: пользователи могут создавать аккаунт, входить в систему.
2. Создание и управление списками покупок: пользователи могут создавать новые списки покупок, добавлять и удалять продукты.
3. Создание рецептов и отслеживание авторов: пользователи могут создавать рецепты, подписываться на авторов рецептов, добавлять рецепты в избранное.

### Преимущества проекта:
1. Удобство использования: приложение имеет интуитивно понятный интерфейс, простую навигацию и понятные действия для управления рецептами и продуктовыми списками.
2. Масштабируемость: архитектура проекта позволяет легко расширять его функционал и добавлять новые возможности в будущем.

### Технические детали:
- Проект написан на языке программирования Python, который предоставляет мощные инструменты для разработки веб-приложений.
- Фреймворк Django используется для создания мощных и надежных веб-приложений на Python с минимальными затратами времени и усилий.
- Библиотека Django REST framework позволяет создавать простые и мощные API для взаимодействия с фронтендом и мобильными приложениями.
- Для хранения данных используется реляционная база данных, такая как PostgreSQL.
- При разработке интерфейса используются HTML, CSS и JavaScript для создания дружественного и отзывчивого пользовательского интерфейса.

### Проект "Фудграмм" позволяет пользователям более эффективно управлять рецептами и запасами продуктов, экономить время и деньги.

## Инструкция по запуску сайта: 

1. Для начала склонируйте репозиторий на ваш компьютер `git@github.com:bogdan0957/foodgram-project-react.git`
2. Откройте проект, создайте виртуальное окружение. `python -m venv venv` - для Windows, `python3 -m venv venv` - для MacOs или Linux.
3. Активируйте виртуальное окружение. `source venv/Scripts/activate` - для Windows, `source venv/Scripts/activate` - для MacOs или Linux.
4. Обновите pip пакет и установите зависимости. `python -m pip install --upgrade pip` и `pip install -r backend/requirements.txt`.
5. Создайте в папке /infra файл .env и впишите свои данные по примеру .env.example находящийся в корне проекта.
6. Зайдите на облачный сервер и создайте директорию под названием foodgram.
7. Скопируйте все файлы из папки /infra находясь в ней на облачный сервер. Команда для копирования \
   `scp -i path_to_SSH/SSH_name docker-compose.production.yml username@server_ip:/home/username/foodgram/docker-compose.production.yml` \
   `scp -i path_to_SSH/SSH_name .env username@server_ip:/home/username/foodgram/.env` \
   `scp -i path_to_SSH/SSH_name nginx.conf username@server_ip:/home/username/foodgram/nginx.conf` 
8. Сбилдите образы находясь в папках соответствующим их названию: \
   `cd backend` -> `docker build -t username/foodgram_backend` -> `docker push username/foodgram_backend` \
   `cd frontend` -> `docker build -t username/foodgram_frontend` -> `docker push username/foodgram_frontend`
9. Находясь на сервере перейдите в папку foodgramm и запустите docker-compose.yml командой. \
   `sudo docker compose -f docker-compose.yml up -d`
10. Далее когда контейнеры запустяться необходимо прописать ряд команд (для миграции таблиц, заполнения этих таблиц данными и сборка ститики с их последующим копированием. \
    `sudo docker compose -f docker-compose.yml exec backend python manage.py migrate` \
    `sudo docker compose -f docker-compose.yml exec backend python manage.py import_db` \
    `sudo docker compose -f docker-compose.yml exec backend python manage.py import_tag` \
    `sudo docker compose -f docker-compose.yml exec backend python manage.py collectstatic` \
    `sudo docker compose -f docker-compose.yml exec backend cp -r /app/collected_static/. /static/`.

После того как вы выполнили все команды указанные выше, проект будет доступен по адресу: \
### `foodgrambogdannug.zapto.org`
