from flask import Flask, render_template_string, request, redirect, url_for
import json
import os
from datetime import datetime, timedelta
import calendar
import base64

app = Flask(__name__)
DATA_FILE = 'quest_data.json'

CHALLENGES = [
    "Compliment a stranger today", "Try a food you've never eaten before",
    "Take a different route to work/school", "Call or text an old friend you haven't spoken to in a while",
    "Learn 5 words or sentences in a new language", "Write handwritten letters to loved ones",
    "Strike up a conversation with someone in line", "Visit a store you've never been to",
    "Draw or sketch something for 15 minutes", "Listen to a music genre you normally wouldn't",
    "Write a thank you note to someone", "Try doing something with your non-dominant hand for an hour",
    "Watch the sunrise or sunset", "Read a chapter of a book in a genre you don't usually read",
    "Wear something you normally wouldn't wear", "Cook a recipe from a different culture",
    "Learn a magic trick", "Meditate or sit in silence for 10 minutes",
    "Take a photo of something beautiful you notice", "Write a short poem or haiku",
    "Learn a dance choreography", "Go on a color walk",
    "Visit a museum or gallery", "Make a collage from old magazines or a scrapbook page",
    "Rearrange furniture in one room", "Learn the basics of a new skill on YouTube",
    "Go for a walk without your phone", "Introduce yourself to a neighbor",
    "Dance to your favorite song in public", "Write down 3 things you're grateful for and why"
]

HTML = '''<!DOCTYPE html>
<html>
<head>
    <title>{% if page == 'today' %}Daily Side Quest{% else %}Quest Calendar{% endif %}</title>
    <link href="https://fonts.googleapis.com/css2?family=Josefin+Sans:wght@400;600;700&display=swap" rel="stylesheet">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Josefin Sans', sans-serif; background: #3d5a40; min-height: 100vh; padding: 20px; }
        .container { max-width: {% if page == 'calendar' %}1000{% else %}800{% endif %}px; margin: 0 auto; background: #f4f6f4; border-radius: 20px; padding: 40px; box-shadow: 0 20px 60px rgba(0,0,0,0.3); }
        h1 { color: #2d4a2f; text-align: center; margin-bottom: 10px; font-size: 2.5em; }
        .streak { text-align: center; font-size: 1.2em; color: #3d5a40; margin-bottom: 30px; font-weight: bold; }
        .streak span { background: #a4b494; padding: 5px 15px; border-radius: 20px; color: #1e3a1f; }
        .date { text-align: center; color: #666; margin-bottom: 20px; font-size: 1.1em; }
        .challenge-box { background: #588157; color: white; padding: 30px; border-radius: 15px; margin: 30px 0; text-align: center; font-size: 1.3em; font-weight: 500; }
        label { display: block; margin-bottom: 8px; color: #333; font-weight: 600; }
        textarea { width: 100%; padding: 15px; border: 2px solid #a4b494; border-radius: 10px; font-size: 1em; font-family: inherit; resize: vertical; min-height: 120px; margin-bottom: 20px; }
        textarea:focus { outline: none; border-color: #588157; }
        input[type="file"] { margin-bottom: 20px; padding: 10px; border: 2px dashed #588157; border-radius: 10px; width: 100%; cursor: pointer; }
        button { background: #3d5a40; color: white; border: none; padding: 15px 40px; font-size: 1.1em; border-radius: 10px; cursor: pointer; width: 100%; font-weight: bold; transition: all 0.2s; }
        button:hover { transform: translateY(-2px); background: #2d4a2f; }
        .nav-buttons { display: flex; gap: 10px; margin-top: 20px; }
        .nav-buttons button { flex: 1; background: #718f71; }
        .nav-buttons button:hover { background: #5f7a5f; }
        .completed-badge { background: #588157; color: white; padding: 5px 15px; border-radius: 20px; font-size: 0.9em; display: inline-block; margin-bottom: 10px; }
        .month-navigation { display: flex; justify-content: space-between; align-items: center; margin-bottom: 30px; }
        .month-navigation button { background: #588157; color: white; border: none; padding: 10px 20px; border-radius: 8px; cursor: pointer; font-size: 1em; width: auto; }
        .month-navigation button:hover { background: #3d5a40; }
        .month-title { font-size: 1.5em; color: #2d4a2f; font-weight: bold; }
        .calendar-grid { display: grid; grid-template-columns: repeat(7, 1fr); gap: 10px; margin-bottom: 30px; }
        .day-header { text-align: center; font-weight: bold; color: #3d5a40; padding: 10px; font-size: 0.9em; }
        .calendar-day { aspect-ratio: 1; border: 2px solid #a4b494; border-radius: 10px; display: flex; align-items: center; justify-content: center; font-size: 1.1em; cursor: pointer; transition: all 0.3s; position: relative; background: white; }
        .calendar-day:hover { transform: scale(1.05); border-color: #588157; }
        .calendar-day.empty { border: none; cursor: default; }
        .calendar-day.empty:hover { transform: none; }
        .calendar-day.completed { background: #588157; color: white; font-weight: bold; border-color: #3d5a40; }
        .calendar-day.completed::after { content: '✓'; position: absolute; top: 5px; right: 5px; font-size: 0.8em; background: #2d4a2f; color: white; width: 20px; height: 20px; border-radius: 50%; display: flex; align-items: center; justify-content: center; }
        .calendar-day.today { border-color: #a4b494; border-width: 3px; font-weight: bold; }
        .calendar-day.future { color: #ccc; cursor: not-allowed; }
        .calendar-day.future:hover { transform: none; border-color: #a4b494; }
        .modal { display: none; position: fixed; z-index: 1000; left: 0; top: 0; width: 100%; height: 100%; background-color: rgba(0,0,0,0.5); }
        .modal-content { background-color: white; margin: 5% auto; padding: 30px; border-radius: 15px; width: 90%; max-width: 600px; max-height: 80vh; overflow-y: auto; position: relative; }
        .close { color: #aaa; float: right; font-size: 28px; font-weight: bold; cursor: pointer; line-height: 20px; }
        .close:hover { color: #000; }
        .modal h2 { color: #2d4a2f; margin-bottom: 20px; }
        .modal .challenge { background: #e8ebe8; padding: 20px; border-radius: 10px; margin: 15px 0; border-left: 5px solid #588157; }
        .modal .reflection { margin: 15px 0; line-height: 1.6; color: #333; }
        .modal img { max-width: 100%; border-radius: 10px; margin-top: 15px; }
    </style>
</head>
<body>
    <div class="container">
        {% if page == 'today' %}
            <h1>Daily Side Quest</h1>
            <div class="streak">Current Streak: <span>{{ streak }} days</span></div>
            <div class="date">{{ today_date }}</div>
            <div class="challenge-box">{{ challenge }}</div>
            {% if already_completed %}
                <div class="completed-badge">Quest Completed!</div>
                <p style="text-align: center; color: #666; margin-top: 20px;">Great job! Come back tomorrow for a new challenge.</p>
            {% else %}
                <form method="POST" enctype="multipart/form-data">
                    <label>Reflect on your experience:</label>
                    <textarea name="reflection" placeholder="How did it go? What did you learn or feel?" required></textarea>
                    <label>Upload a photo (optional):</label>
                    <input type="file" name="photo" accept="image/*">
                    <button type="submit">Complete Quest</button>
                </form>
            {% endif %}
            <div class="nav-buttons"><button onclick="window.location.href='/calendar'">View Calendar</button></div>
        {% else %}
            <h1>Quest Calendar</h1>
            <div class="streak">Current Streak: <span>{{ streak }} days</span></div>
            <div class="month-navigation">
                <button onclick="changeMonth(-1)">← Previous</button>
                <div class="month-title">{{ month_name }} {{ year }}</div>
                <button onclick="changeMonth(1)">Next →</button>
            </div>
            <div class="calendar-grid">
                <div class="day-header">Sun</div><div class="day-header">Mon</div><div class="day-header">Tue</div>
                <div class="day-header">Wed</div><div class="day-header">Thu</div><div class="day-header">Fri</div><div class="day-header">Sat</div>
                {% for day in calendar_days %}
                    {% if day.empty %}
                        <div class="calendar-day empty"></div>
                    {% else %}
                        <div class="calendar-day {% if day.completed %}completed{% endif %} {% if day.is_today %}today{% endif %} {% if day.is_future %}future{% endif %}"
                            {% if day.completed %}onclick="showQuest('{{ day.date }}')"{% endif %}>{{ day.day }}</div>
                    {% endif %}
                {% endfor %}
            </div>
            <div class="nav-buttons"><button onclick="window.location.href='/'">Back to Today's Quest</button></div>
        {% endif %}
    </div>
    {% if page == 'calendar' %}
        <div id="questModal" class="modal">
            <div class="modal-content">
                <span class="close" onclick="closeModal()">&times;</span>
                <div id="modalContent"></div>
            </div>
        </div>
        <script>
            const questData = {{ quest_data_json|safe }};
            function showQuest(d) {
                const q = questData[d];
                if (!q) return;
                let h = '<div class="completed-badge">Completed</div><h2>' + new Date(d).toLocaleDateString('en-US', {weekday: 'long', year: 'numeric', month: 'long', day: 'numeric'}) + '</h2>';
                h += '<div class="challenge"><strong>Challenge:</strong> ' + q.challenge + '</div>';
                h += '<div class="reflection"><strong>Reflection:</strong><br>' + q.reflection + '</div>';
                if (q.photo) h += '<img src="data:image/jpeg;base64,' + q.photo + '">';
                document.getElementById('modalContent').innerHTML = h;
                document.getElementById('questModal').style.display = 'block';
            }
            function closeModal() { document.getElementById('questModal').style.display = 'none'; }
            function changeMonth(delta) {
                let m = {{ current_month }} + delta, y = {{ current_year }};
                if (m > 12) { m = 1; y++; } else if (m < 1) { m = 12; y--; }
                window.location.href = '/calendar?month=' + m + '&year=' + y;
            }
            window.onclick = e => { if (e.target == document.getElementById('questModal')) closeModal(); }
        </script>
    {% endif %}
</body>
</html>'''

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    return {'quests': [], 'last_completed': None}

def save_data(data):
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=2)

def get_challenge_for_date(date_obj):
    return CHALLENGES[date_obj.timetuple().tm_yday % len(CHALLENGES)]

def calculate_streak(data):
    if not data['quests']:
        return 0
    sorted_quests = sorted(data['quests'], key=lambda x: x['date'], reverse=True)
    streak, expected = 0, datetime.now().date()
    for q in sorted_quests:
        qd = datetime.strptime(q['date'], '%Y-%m-%d').date()
        if qd == expected:
            streak += 1
            expected -= timedelta(days=1)
        elif qd < expected:
            break
    return streak

def build_calendar_data(year, month, completed):
    cal, today, days = calendar.monthcalendar(year, month), datetime.now().date(), []
    for week in cal:
        for day in week:
            if day == 0:
                days.append({'empty': True})
            else:
                d = datetime(year, month, day).date()
                ds = d.strftime('%Y-%m-%d')
                days.append({'day': day, 'date': ds, 'completed': ds in completed, 'is_today': d == today, 'is_future': d > today, 'empty': False})
    return days

@app.route('/', methods=['GET', 'POST'])
def today_quest():
    data = load_data()
    today = datetime.now().strftime('%Y-%m-%d')
    challenge = get_challenge_for_date(datetime.now())
    already_completed = any(q['date'] == today for q in data['quests'])
    
    if request.method == 'POST' and not already_completed:
        photo = request.files.get('photo')
        photo_data = base64.b64encode(photo.read()).decode('utf-8') if photo and photo.filename else None
        data['quests'].append({'date': today, 'challenge': challenge, 'reflection': request.form.get('reflection'), 'photo': photo_data})
        data['last_completed'] = today
        save_data(data)
        return redirect(url_for('today_quest'))
    
    return render_template_string(HTML, page='today', challenge=challenge, today_date=datetime.now().strftime('%B %d, %Y'), 
                                  already_completed=already_completed, streak=calculate_streak(data))

@app.route('/calendar')
def calendar_view():
    month = request.args.get('month', type=int) or datetime.now().month
    year = request.args.get('year', type=int) or datetime.now().year
    data = load_data()
    completed = {q['date']: q for q in data['quests']}
    
    return render_template_string(HTML, page='calendar', calendar_days=build_calendar_data(year, month, completed),
                                  month_name=calendar.month_name[month], year=year, current_month=month, 
                                  current_year=year, streak=calculate_streak(data), quest_data_json=json.dumps(completed))

if __name__ == '__main__':
    print("\n" + "="*50)
    print("DAILY SIDE QUEST APP IS RUNNING!")
    print("="*50)
    print("\n Open your browser and go to:")
    print("\n   http://localhost:5000")
    print("   or")
    print("\n   http://127.0.0.1:5000")
    print("\n Press CTRL+C to stop the server")
    print("="*50 + "\n")
    app.run(debug=True, port=5000)