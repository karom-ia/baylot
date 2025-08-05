# app/main.py

from fastapi import FastAPI
from fastapi.responses import HTMLResponse

app = FastAPI()

# This is the root URL handler, which will serve your website's main page.
@app.get("/", response_class=HTMLResponse)
async def read_root():
    """
    Handles requests to the root URL (e.g., http://www.metabase.info/)
    It returns a simple HTML string for the main page.
    """
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Главная страница Metabase.info</title>
        <link href="https://cdn.jsdelivr.net/npm/tailwindcss@2.2.19/dist/tailwind.min.css" rel="stylesheet">
    </head>
    <body class="bg-gray-100 flex items-center justify-center min-h-screen">
        <div class="bg-white p-8 rounded-lg shadow-md text-center">
            <h1 class="text-3xl font-bold text-gray-800 mb-4">Добро пожаловать на Metabase.info!</h1>
            <p class="text-gray-600 mb-4">Это ваша главная страница.</p>
            <p class="text-gray-600">Чтобы перейти на дашборд, пожалуйста, посетите <a href="/dashboard" class="text-blue-500 hover:underline">/dashboard</a></p>
        </div>
    </body>
    </html>
    """
    return html_content

# This is the handler for the dashboard page.
# You can keep this or delete it if the dashboard is no longer needed.
@app.get("/dashboard", response_class=HTMLResponse)
async def read_dashboard():
    """
    Handles requests to the dashboard URL (e.g., http://www.metabase.info/dashboard)
    This will serve the ticket management dashboard page.
    """
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Админ-панель управления билетами</title>
        <link href="https://cdn.jsdelivr.net/npm/tailwindcss@2.2.19/dist/tailwind.min.css" rel="stylesheet">
    </head>
    <body class="bg-gray-100 flex items-center justify-center min-h-screen">
        <div class="bg-white p-8 rounded-lg shadow-md text-center">
            <h1 class="text-3xl font-bold text-gray-800 mb-4">Админ-панель управления билетами</h1>
            <p class="text-gray-600">Это дашборд, который вы видели ранее.</p>
            <p class="text-gray-600">Чтобы вернуться на главную, пожалуйста, посетите <a href="/" class="text-blue-500 hover:underline">/</a></p>
        </div>
    </body>
    </html>
    """
    return html_content
