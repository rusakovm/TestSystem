<div align="center">

# 🧪 TestSystem

### TestFlow — управление тестированием компьютерного оборудования

**設計 • 開発 • 改善**  
*Design • Build • Improve*

![Python](https://img.shields.io/badge/Python-3.12-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Django](https://img.shields.io/badge/Django-092E20?style=for-the-badge&logo=django&logoColor=white)
![SQLite](https://img.shields.io/badge/SQLite-003B57?style=for-the-badge&logo=sqlite&logoColor=white)
![JavaScript](https://img.shields.io/badge/JavaScript-F7DF1E?style=for-the-badge&logo=javascript&logoColor=black)

**[Возможности](#-возможности) · [Архитектура](#-архитектура) · [Установка](#-локальный-запуск) · [Планы](#-планы-развития)**

</div>

---

## 🌙 О проекте

**TestFlow** — веб-приложение для организации тестирования компьютеров и ноутбуков: от регистрации устройства до фиксации результатов проверок.

Проект создаётся как практическая работа по **Python Backend**. В нём я изучаю Django, проектирование моделей, работу с ORM, обработку запросов и организацию бизнес-логики.

> **Идея:** сделать процесс проверки оборудования последовательным и прозрачным: у каждой модели свой план тестирования, у каждого устройства — история прохождения проверок.

## ⚙️ Возможности

| Модуль | Что делает |
| :--- | :--- |
| **Устройства** | Регистрация по серийному номеру, выбор модели и отслеживание статуса |
| **Модели** | Управление моделями оборудования |
| **Планы тестирования** | Настройка этапов и последовательности тестов для модели |
| **Тестовые сессии** | Запуск проверки и фиксация успешного или неуспешного выполнения тестов |
| **Результаты** | Сохранение результатов и комментариев |
| **История** | Просмотр предыдущих тестовых сессий |
| **Доступ** | Авторизация пользователей через Django |

## 🖥️ Интерфейс

*Здесь появятся реальные скриншоты приложения. Скриншоты будут добавлены после подготовки демонстрационных данных.*

<!-- Пример после добавления изображений в docs/screenshots/:
![Список устройств](docs/screenshots/devices.png)
![Тестовая сессия](docs/screenshots/session.png)
![План тестирования](docs/screenshots/test-plan.png)
-->

## 🏗️ Архитектура

```text
TestSystem/
├── config/                 # Настройки и маршрутизация Django
├── testing/                # Основное приложение
│   ├── migrations/         # Миграции моделей
│   ├── static/             # CSS и JavaScript
│   ├── templates/          # HTML-шаблоны
│   ├── models.py           # Структура данных
│   ├── views.py            # Обработка HTTP-запросов
│   ├── services.py         # Прикладная логика
│   └── urls.py             # Маршруты приложения
├── manage.py
└── requirements.txt
```

**Основные сущности:** `DeviceModel`, `Device`, `Phase`, `ModelPhase`, `TestDefinition`, `TestPlanItem`, `TestSession`, `TestRun`, `TestResult`.

**Стек:** Python · Django · Django ORM · SQLite · HTML · CSS · JavaScript · Git.

## 🚀 Локальный запуск

Инструкция для **Windows (CMD)**. Понадобятся Python и Git.

**1. Клонировать репозиторий**

```cmd
git clone https://github.com/rusakovm/TestSystem.git
cd TestSystem
```

**2. Создать окружение и установить зависимости**

```cmd
python -m venv .venv
.venv\Scripts\activate.bat
pip install -r requirements.txt
```

**3. Создать `.env` в корне проекта**

```dotenv
DJANGO_SECRET_KEY=replace-with-your-own-generated-secret-key
DJANGO_DEBUG=True
```

Сгенерировать собственный ключ можно командой:

```cmd
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

**4. Подготовить базу и пользователя**

```cmd
python manage.py migrate
python manage.py createsuperuser
```

**5. Запустить приложение**

```cmd
python manage.py runserver
```

Открыть в браузере: **http://127.0.0.1:8000/**

> `.env`, `.venv` и локальная база данных не должны попадать в Git.

## 🧭 Планы развития

- [ ] Развитие REST API
- [ ] Автоматизация выполнения тестов оборудования
- [ ] Расширенная отчётность
- [ ] Автоматизированные тесты для бизнес-логики
- [ ] Дальнейшее разделение и упрощение компонентов проекта

---

<div align="center">

**Создаёт [Konari](https://github.com/rusakovm)**  
*Learning • Building • Improving*

</div>
