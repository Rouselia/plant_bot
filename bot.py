import telebot
from telebot import types
import sqlite3
from datetime import datetime
import schedule
import time
import threading
from flask import Flask

# Ось цей блок додайте прямо після імпортів:
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running!"

def run_web_server():
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
# Кінець блоку

TOKEN = "8721909391:AAHj-d5NlPqYlZ586w3TnPy5RRN7VWuTw8I"
bot = telebot.TeleBot(TOKEN)

# --- Підключення до бази даних ---
conn = sqlite3.connect('plants.db', check_same_thread=False)
cursor = conn.cursor()

# Створення таблиць
cursor.execute('''
CREATE TABLE IF NOT EXISTS catalog (
    id INTEGER PRIMARY KEY,
    name TEXT,
    group_name TEXT,
    light TEXT,
    temperature TEXT,
    watering_interval_min INTEGER,
    watering_interval_max INTEGER,
    soil TEXT,
    humidity TEXT
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS user_plants (
    id INTEGER PRIMARY KEY,
    user_id INTEGER,
    plant_id INTEGER,
    custom_name TEXT,
    last_watered TEXT,
    watering_interval INTEGER,
    added_date TEXT,
    FOREIGN KEY (plant_id) REFERENCES catalog(id)
)
''')
conn.commit()

# --- Додавання рослин з вашого файлу в каталог ---
def init_catalog():
    plants = [
        # 🌵 Сукуленти та кактуси
        ("Алое вера", "🌵 Сукуленти та кактуси", "Яскраве сонце", "+18..+28", 10, 25, "Піщаний, дренаж", "Сухе"),
        ("Хавортія", "🌵 Сукуленти та кактуси", "Яскраве розсіяне", "+18..+25", 10, 30, "Для сукулентів", "Сухе"),
        ("Красула (товстянка)", "🌵 Сукуленти та кактуси", "Сонце/півтінь", "+18..+25", 10, 25, "Пісок+дерн", "Сухе"),
        ("Ечеверія", "🌵 Сукуленти та кактуси", "Пряме сонце", "+20..+28", 7, 20, "Дуже піщаний", "Сухе"),
        ("Молочай", "🌵 Сукуленти та кактуси", "Яскраве сонце", "+18..+26", 7, 21, "Для сукулентів", "Сухе"),
        
        # 🌿 Тіньовитривалі
        ("Сансевієрія", "🌿 Тіньовитривалі", "Півтінь/штучне", "+16..+28", 14, 40, "Супіщаний", "Сухе"),
        ("Заміокулькас", "🌿 Тіньовитривалі", "Півтінь/темно", "+20..+28", 14, 30, "Пухкий+перліт", "Сухе"),
        ("Аспідістра", "🌿 Тіньовитривалі", "Тінь (дуже темно)", "+12..+25", 7, 21, "Універсальний", "Сухе"),
        ("Аглаонема", "🌿 Тіньовитривалі", "Півтінь", "+20..+26", 5, 14, "Торф+перліт", "Підвищена"),
        ("Драцена", "🌿 Тіньовитривалі", "Півтінь/розсіяне", "+18..+25", 5, 14, "Пухкий, торф'яний", "Помірна"),
        
        # 🌸 Квітучі
        ("Спатифілум", "🌸 Квітучі", "Розсіяне (схід/захід)", "+18..+25", 3, 8, "Торф+перліт (кислий)", "Висока"),
        ("Антуріум", "🌸 Квітучі", "Розсіяне (без сонця)", "+22..+28", 3, 9, "Кора+торф (пухкий)", "Дуже висока"),
        ("Фіалка", "🌸 Квітучі", "Яскраве розсіяне", "+20..+24", 3, 7, "Торф+перліт", "Помірна"),
        ("Пеларгонія", "🌸 Квітучі", "Пряме сонце", "+18..+25", 3, 14, "Дерн+пісок", "Сухе"),
        ("Гібіскус", "🌸 Квітучі", "Яскраве сонце", "+20..+28", 2, 10, "Родючий, суглинистий", "Висока"),
        ("Каланхое", "🌸 Квітучі", "Яскраве сонце", "+18..+28", 7, 14, "Для сукулентів", "Сухе"),
        
        # 🍃 Ампельні та ліани
        ("Хлорофітум", "🍃 Ампельні та ліани", "Розсіяне/півтінь", "+15..+25", 5, 12, "Універсальний", "Нейтральна"),
        ("Епіпремнум", "🍃 Ампельні та ліани", "Півтінь/розсіяне", "+18..+26", 5, 14, "Універс.+перліт", "Помірна"),
        ("Традесканція", "🍃 Ампельні та ліани", "Яскраве розсіяне", "+18..+24", 3, 10, "Пухкий, торф'яний", "Помірна"),
        ("Плющ", "🍃 Ампельні та ліани", "Півтінь/розсіяне", "+15..+22", 4, 10, "Універсальний", "Висока"),
        ("Філодендрон", "🍃 Ампельні та ліани", "Розсіяне/півтінь", "+18..+26", 4, 10, "Торф+перліт", "Висока"),
        
        # 🌴 Пальми та великі рослини
        ("Монстера", "🌴 Пальми та великі", "Яскраве розсіяне", "+20..+28", 4, 10, "Торф+перліт", "Висока"),
        ("Фікус ліроподібний", "🌴 Пальми та великі", "Яскраве розсіяне", "+18..+28", 4, 10, "Родючий, пухкий", "Висока"),
        ("Хамедорея", "🌴 Пальми та великі", "Півтінь (без сонця)", "+18..+24", 3, 7, "Кислий, торф'яний", "Дуже висока"),
    ]
    
    cursor.execute("SELECT COUNT(*) FROM catalog")
    if cursor.fetchone()[0] == 0:
        for plant in plants:
            cursor.execute('''
            INSERT INTO catalog (name, group_name, light, temperature, watering_interval_min, watering_interval_max, soil, humidity)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', plant)
        conn.commit()
        print("🌿 Каталог наповнено 24 рослинами!")

init_catalog()

# --- ГОЛОВНЕ МЕНЮ ---
@bot.message_handler(commands=['start'])
def start(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add('📚 Каталог рослин', '➕ Додати з каталогу')
    markup.add('🌱 Моя бібліотека', '💧 Полити рослину')
    markup.add('📋 Статус поливу', '❓ Догляд за рослиною')
    bot.send_message(message.chat.id, 
                     "🌿 *Вітаю в бібліотеці рослин!*\n\n"
                     "Я *РостОк* — твій персональний помічник із догляду за рослинами! 🌱\n"
                     "📚 Обирай рослини з каталогу, додавай у свою бібліотеку та отримуй нагадування про полив.\n\n"
                     "💧 Не дай своїм зеленим друзям засохнути!", 
                     parse_mode='Markdown', reply_markup=markup)

# --- ПОКАЗАТИ КАТАЛОГ (згруповано) ---
@bot.message_handler(func=lambda msg: msg.text == '📚 Каталог рослин')
def show_catalog(message):
    cursor.execute("SELECT DISTINCT group_name FROM catalog")
    groups = cursor.fetchall()
    
    response = "📚 *ВСІ РОСЛИНИ В КАТАЛОЗІ:*\n\n"
    for (group,) in groups:
        response += f"*{group}*\n"
        cursor.execute("SELECT name, watering_interval_min, watering_interval_max FROM catalog WHERE group_name=?", (group,))
        plants = cursor.fetchall()
        for name, min_int, max_int in plants:
            if min_int == max_int:
                response += f"   🌱 {name} — полив кожні {min_int} днів\n"
            else:
                response += f"   🌱 {name} — полив кожні {min_int}-{max_int} днів\n"
        response += "\n"
    
    bot.send_message(message.chat.id, response, parse_mode='Markdown')

# --- ДОДАТИ РОСЛИНУ ---
@bot.message_handler(func=lambda msg: msg.text == '➕ Додати з каталогу')
def add_from_catalog(message):
    markup = types.InlineKeyboardMarkup(row_width=2)
    cursor.execute("SELECT id, name FROM catalog ORDER BY name")
    plants = cursor.fetchall()
    
    for plant_id, name in plants:
        cursor.execute("SELECT * FROM user_plants WHERE user_id=? AND plant_id=?", (message.chat.id, plant_id))
        if not cursor.fetchone():
            markup.add(types.InlineKeyboardButton(f"➕ {name}", callback_data=f"add_{plant_id}"))
        else:
            markup.add(types.InlineKeyboardButton(f"✅ {name}", callback_data=f"none"))
    
    bot.send_message(message.chat.id, "🌱 *Оберіть рослину для додавання в бібліотеку:*", 
                     parse_mode='Markdown', reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('add_'))
def add_plant_to_library(call):
    plant_id = int(call.data.replace('add_', ''))
    
    cursor.execute("SELECT name, watering_interval_min, watering_interval_max, group_name FROM catalog WHERE id=?", (plant_id,))
    name, min_int, max_int, group = cursor.fetchone()
    
    # Використовуємо середнє значення для поливу
    avg_interval = (min_int + max_int) // 2
    
    cursor.execute('''
    INSERT INTO user_plants (user_id, plant_id, custom_name, last_watered, watering_interval, added_date)
    VALUES (?, ?, ?, ?, ?, ?)
    ''', (call.message.chat.id, plant_id, name, datetime.now().isoformat(), avg_interval, datetime.now().isoformat()))
    conn.commit()
    
    bot.answer_callback_query(call.id, f"✅ {name} додано до вашої бібліотеки!")
    bot.send_message(call.message.chat.id, 
                     f"🌱 *{name}* додано до вашої бібліотеки!\n"
                     f"📂 Група: {group}\n"
                     f"💧 Полив: кожні {avg_interval} днів (рекомендовано {min_int}-{max_int})", 
                     parse_mode='Markdown')

@bot.callback_query_handler(func=lambda call: call.data == 'none')
def nothing(call):
    bot.answer_callback_query(call.id, "Ця рослина вже у вашій бібліотеці ✅")

# --- МОЯ БІБЛІОТЕКА ---
@bot.message_handler(func=lambda msg: msg.text == '🌱 Моя бібліотека')
def my_library(message):
    cursor.execute('''
    SELECT c.name, c.group_name, u.custom_name, u.last_watered, u.watering_interval, c.light, c.temperature, c.soil, c.humidity
    FROM user_plants u
    JOIN catalog c ON u.plant_id = c.id
    WHERE u.user_id=?
    ''', (message.chat.id,))
    plants = cursor.fetchall()
    
    if not plants:
        bot.send_message(message.chat.id, "🌱 У вас ще немає рослин в бібліотеці.\n"
                                           "Скористайтесь ➕ Додати з каталогу")
        return
    
    response = "🌿 *МОЯ БІБЛІОТЕКА:*\n\n"
    for name, group, custom_name, last, interval, light, temp, soil, humidity in plants:
        last_date = datetime.fromisoformat(last)
        days_since = (datetime.now() - last_date).days
        days_left = interval - days_since
        
        if days_left <= 0:
            status = "🔴 *ПОТРІБНО ПОЛИТИ!*"
        else:
            status = f"🟢 Полив через {days_left} днів"
        
        response += f"🌱 *{custom_name}*\n"
        response += f"   📂 {group}\n"
        response += f"   💧 {status}\n"
        response += f"   📅 Останній полив: {last_date.strftime('%d.%m.%Y')}\n"
        response += f"   ☀️ Світло: {light}\n"
        response += f"   🌡️ Температура: {temp}\n"
        response += f"   🪴 Ґрунт: {soil}\n"
        response += f"   💨 Вологість: {humidity}\n\n"
    
    bot.send_message(message.chat.id, response, parse_mode='Markdown')

# --- ПОЛИТИ РОСЛИНУ ---
@bot.message_handler(func=lambda msg: msg.text == '💧 Полити рослину')
def water_plant(message):
    markup = types.InlineKeyboardMarkup(row_width=2)
    cursor.execute('''
    SELECT u.id, u.custom_name
    FROM user_plants u
    WHERE u.user_id=?
    ''', (message.chat.id,))
    plants = cursor.fetchall()
    
    if not plants:
        bot.send_message(message.chat.id, "❌ У вас немає рослин для поливу.\nДодайте їх через ➕ Додати з каталогу")
        return
    
    for user_plant_id, name in plants:
        markup.add(types.InlineKeyboardButton(f"💧 {name}", callback_data=f"water_{user_plant_id}"))
    
    bot.send_message(message.chat.id, "💧 *Оберіть рослину, яку полили:*", parse_mode='Markdown', reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('water_'))
def water_plant_save(call):
    user_plant_id = int(call.data.replace('water_', ''))
    
    cursor.execute('''
    UPDATE user_plants 
    SET last_watered=? 
    WHERE id=?
    ''', (datetime.now().isoformat(), user_plant_id))
    conn.commit()
    
    cursor.execute("SELECT custom_name FROM user_plants WHERE id=?", (user_plant_id,))
    name = cursor.fetchone()[0]
    
    bot.answer_callback_query(call.id, f"✅ {name} полито!")
    bot.send_message(call.message.chat.id, f"💧 *{name}* полито сьогодні! 🌱", parse_mode='Markdown')

# --- СТАТУС ПОЛИВУ ---
@bot.message_handler(func=lambda msg: msg.text == '📋 Статус поливу')
def watering_status(message):
    cursor.execute('''
    SELECT u.custom_name, u.last_watered, u.watering_interval
    FROM user_plants u
    WHERE u.user_id=?
    ''', (message.chat.id,))
    plants = cursor.fetchall()
    
    if not plants:
        bot.send_message(message.chat.id, "🌱 У вас ще немає рослин.")
        return
    
    need_water = []
    ok_plants = []
    
    for name, last, interval in plants:
        last_date = datetime.fromisoformat(last)
        days_since = (datetime.now() - last_date).days
        days_left = interval - days_since
        
        if days_left <= 0:
            need_water.append(f"🔴 {name} (полив {days_since} днів тому)")
        else:
            ok_plants.append(f"🟢 {name} (через {days_left} днів)")
    
    response = "🌿 *СТАТУС ПОЛИВУ:*\n\n"
    if need_water:
        response += "⚠️ *ПОТРЕБУЮТЬ ПОЛИВУ:*\n" + "\n".join(need_water) + "\n\n"
    if ok_plants:
        response += "✅ *В ПОРЯДКУ:*\n" + "\n".join(ok_plants)
    
    if not need_water and not ok_plants:
        response = "🌿 У вас немає рослин."
    
    bot.send_message(message.chat.id, response, parse_mode='Markdown')

# --- ДОГЛЯД ЗА РОСЛИНОЮ ---
@bot.message_handler(func=lambda msg: msg.text == '❓ Догляд за рослиною')
def plant_care(message):
    markup = types.InlineKeyboardMarkup(row_width=2)
    cursor.execute("SELECT id, name FROM catalog ORDER BY name")
    plants = cursor.fetchall()
    
    for plant_id, name in plants:
        markup.add(types.InlineKeyboardButton(f"📖 {name}", callback_data=f"care_{plant_id}"))
    
    bot.send_message(message.chat.id, "🌱 *Оберіть рослину, щоб отримати поради з догляду:*", 
                     parse_mode='Markdown', reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith('care_'))
def show_plant_care(call):
    plant_id = int(call.data.replace('care_', ''))
    
    cursor.execute('''
    SELECT name, group_name, light, temperature, watering_interval_min, watering_interval_max, soil, humidity
    FROM catalog WHERE id=?
    ''', (plant_id,))
    name, group, light, temp, min_int, max_int, soil, humidity = cursor.fetchone()
    
    response = f"🌱 *{name}*\n"
    response += f"📂 *Група:* {group}\n\n"
    response += f"☀️ *Світло:* {light}\n"
    response += f"🌡️ *Температура:* {temp}\n"
    response += f"💧 *Полив:* кожні {min_int}-{max_int} днів\n"
    response += f"🪴 *Ґрунт:* {soil}\n"
    response += f"💨 *Вологість:* {humidity}\n\n"
    response += "💡 *Порада:* Дотримуйтесь рекомендацій і ваша рослина буде здоровою та красивою! 🌿"
    
    bot.send_message(call.message.chat.id, response, parse_mode='Markdown')
    bot.answer_callback_query(call.id)

# --- АВТОМАТИЧНЕ НАГАДУВАННЯ ---
def check_watering():
    cursor.execute('''
    SELECT u.user_id, u.custom_name, u.last_watered, u.watering_interval
    FROM user_plants u
    ''')
    for user_id, name, last, interval in cursor.fetchall():
        last_date = datetime.fromisoformat(last)
        if (datetime.now() - last_date).days >= interval:
            bot.send_message(user_id, 
                             f"🔔 *НАГАДУВАННЯ!*\n\n"
                             f"🌱 *{name}* пора поливати!\n"
                             f"💧 Не дай своїй рослині засохнути!", 
                             parse_mode='Markdown')

schedule.every().hour.do(check_watering)

# --- ЗАПУСК БОТА ---
if __name__ == "__main__":
    # 1. Запускаємо фейковий веб-сервер (щоб Render не закрив бота)
    threading.Thread(target=run_web_server).start()
    
    # 2. Ваші красиві принт-повідомлення
    print("🌿 Бот 'РостОк' запущено!")
    print("📚 Каталог містить 24 рослини")
    print("⏳ Очікую повідомлення...")
    
    # 3. Запускаємо бота
    bot.infinity_polling()
