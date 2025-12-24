#code of ai only with gui 

import sqlite3
import heapq
import customtkinter as ctk

# =========================
# DATABASE SETUP
# =========================
conn = sqlite3.connect("travel_ai.db")
cur = conn.cursor()

cur.execute("DROP TABLE IF EXISTS cities")
cur.execute("DROP TABLE IF EXISTS distances")

cur.execute("""
CREATE TABLE cities(
    name TEXT PRIMARY KEY,
    daily_cost INTEGER,
    rating INTEGER,
    category TEXT,
    x INTEGER,
    y INTEGER
)
""")

cur.execute("""
CREATE TABLE distances(
    from_city TEXT,
    to_city TEXT,
    travel_cost INTEGER
)
""")

# -----------------------------
# Cities: 20 cities with x,y for Map
# -----------------------------
cities = [
    ("Paris", 120, 5, "Cultural", 200, 100),
    ("Rome", 100, 4, "Cultural", 300, 180),
    ("Barcelona", 90, 4, "Beach", 250, 260),
    ("Cairo", 60, 3, "Cultural", 400, 300),
    ("Dubai", 150, 5, "Luxury", 450, 200),
    ("Bali", 80, 5, "Adventure", 520, 120),
    ("Tokyo", 200, 5, "Cultural", 600, 100),
    ("Sydney", 180, 4, "Beach", 700, 400),
    ("New York", 220, 4, "Luxury", 500, 50),
    ("London", 130, 5, "Historical", 100, 50),
    ("Moscow", 120, 4, "Historical", 150, 200),
    ("Istanbul", 90, 4, "Cultural", 350, 220),
    ("Rio de Janeiro", 140, 5, "Beach", 650, 300),
    ("Cape Town", 100, 4, "Adventure", 600, 500),
    ("Bangkok", 90, 4, "Cultural", 550, 180),
    ("Singapore", 160, 5, "Luxury", 580, 220),
    ("Venice", 110, 5, "Cultural", 320, 150),
    ("Athens", 95, 4, "Historical", 300, 200),
    ("Prague", 85, 4, "Historical", 220, 160),
    ("Amsterdam", 120, 5, "Cultural", 250, 120)
]

# -----------------------------
# Distances: travel cost
# -----------------------------
distances = [
    ("Paris", "Rome", 50),
    ("Paris", "Barcelona", 60),
    ("Rome", "Barcelona", 40),
    ("Rome", "Venice", 20),
    ("Venice", "Athens", 70),
    ("Athens", "Istanbul", 50),
    ("Istanbul", "Cairo", 60),
    ("Cairo", "Dubai", 70),
    ("Dubai", "Bali", 100),
    ("Bali", "Bangkok", 60),
    ("Bangkok", "Singapore", 30),
    ("Singapore", "Sydney", 120),
    ("Sydney", "Cape Town", 200),
    ("New York", "London", 100),
    ("London", "Amsterdam", 40),
    ("Amsterdam", "Prague", 30),
    ("Prague", "Moscow", 70),
    ("Rio de Janeiro", "Cape Town", 150),
    ("New York", "Rio de Janeiro", 130),
    ("Tokyo", "Singapore", 150)
]

cur.executemany("INSERT INTO cities VALUES (?,?,?,?,?,?)", cities)
cur.executemany("INSERT INTO distances VALUES (?,?,?)", distances)
conn.commit()

# =========================
# MODEL-BASED AGENT
# =========================
class TravelAgent:
    def __init__(self, budget, max_days, preference):
        self.budget = budget
        self.max_days = max_days
        self.preference = preference

    def heuristic(self, remaining_days):
        return remaining_days * 50  # optimistic estimate

    def get_city_data(self, city):
        cur.execute(
            "SELECT daily_cost, rating, category FROM cities WHERE name=?",
            (city,))
        return cur.fetchone()

    def neighbors(self, city):
        cur.execute(
            "SELECT to_city, travel_cost FROM distances WHERE from_city=?",
            (city,))
        #connect
        return cur.fetchall()
# =========================
# A* Algorithm
# =========================
    def a_star_plan(self, start_city):
        frontier = []
        heapq.heappush(frontier, (0, start_city, 0, 0, []))
        visited = set()

        while frontier:
            f, city, cost, days, path = heapq.heappop(frontier)
            if (city, days) in visited:
                continue
            visited.add((city, days))
            path = path + [city]

            if days == self.max_days:
                return path, cost

            daily_cost, rating, category = self.get_city_data(city)
# connect
            for next_city, travel_cost in self.neighbors(city):
                new_cost = cost + travel_cost + daily_cost
                if new_cost > self.budget:
                    continue

                rating_bonus = rating * 25
                pref_bonus = 40 if category == self.preference else 0
                g = new_cost - rating_bonus - pref_bonus
                h = self.heuristic(self.max_days - days)

                heapq.heappush(
                    frontier,
                    (g + h, next_city, new_cost, days + 1, path)
                )

        return [], 0

# =========================
# GUI
# =========================
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

app = ctk.CTk()
app.title("AI Travel Planner - Advanced")
app.geometry("1250x720")

# -------------------
# Controls Frame
# -------------------
control_frame = ctk.CTkFrame(app, width=300, corner_radius=10)
control_frame.pack(side="left", fill="y", padx=10, pady=10)

labels = ["Start City", "Budget", "Days", "Preference"]
for i, text in enumerate(labels):
    ctk.CTkLabel(control_frame, text=text).grid(row=i, column=0, pady=10, padx=10, sticky="w")

cur.execute("SELECT name FROM cities")
city_list = [c[0] for c in cur.fetchall()]

start_city_cb = ctk.CTkComboBox(control_frame, values=city_list)
budget_entry = ctk.CTkEntry(control_frame)
days_entry = ctk.CTkEntry(control_frame)
pref_cb = ctk.CTkComboBox(control_frame, values=["Cultural","Beach","Adventure","Luxury","Historical"])

start_city_cb.grid(row=0, column=1, pady=10)
budget_entry.grid(row=1, column=1, pady=10)
days_entry.grid(row=2, column=1, pady=10)
pref_cb.grid(row=3, column=1, pady=10)

# -------------------
# Canvas Map
# -------------------
canvas_frame = ctk.CTkFrame(app)
canvas_frame.pack(side="left", fill="both", expand=True, padx=10, pady=10)

canvas = ctk.CTkCanvas(canvas_frame, width=800, height=650, bg="#0f172a")
canvas.pack(fill="both", expand=True)

# -------------------
# Results Box
# -------------------
result_box = ctk.CTkTextbox(app, width=300)
result_box.pack(side="right", fill="y", padx=10, pady=10)

# -------------------
# Functions
# -------------------
def draw_map(path=[]):
    canvas.delete("all")
    cur.execute("SELECT * FROM cities")
    city_pos = {}
    for name, _, _, _, x, y in cur.fetchall():
        city_pos[name] = (x, y)
        canvas.create_oval(x-6, y-6, x+6, y+6, fill="white")
        canvas.create_text(x, y-12, text=name, fill="white")
    cur.execute("SELECT * FROM distances")
    for a, b, _ in cur.fetchall():
        x1, y1 = city_pos[a]
        x2, y2 = city_pos[b]
        canvas.create_line(x1, y1, x2, y2, fill="gray")
    for i in range(len(path)-1):
        x1, y1 = city_pos[path[i]]
        x2, y2 = city_pos[path[i+1]]
        canvas.create_line(x1, y1, x2, y2, fill="#22c55e", width=3)

def plan_trip():
    result_box.delete("0.0", "end")
    try:
        agent = TravelAgent(
            budget=int(budget_entry.get()),
            max_days=int(days_entry.get()),
            preference=pref_cb.get()
        )
    except ValueError:
        result_box.insert("0.0","Please enter valid numeric values for Budget and Days.")
        return

    path, total_cost = agent.a_star_plan(start_city_cb.get())
    if not path:
        result_box.insert("0.0","No valid plan found for the given constraints.")
        draw_map()
        return

    result_box.insert("0.0","🧠 AI Suggested Travel Plan:\n\n")
    for i, city in enumerate(path, 1):
        cur.execute("SELECT rating FROM cities WHERE name=?", (city,))
        rating = cur.fetchone()[0]
        result_box.insert("end", f"Day {i}: {city} ⭐ {rating}\n")
    result_box.insert("end", f"\nTotal Estimated Cost: ${total_cost}")
    draw_map(path)

# -------------------
# Button
# -------------------
plan_btn = ctk.CTkButton(control_frame, text="PLAN TRIP", command=plan_trip)
plan_btn.grid(row=4, column=0, columnspan=2, pady=20)

# -------------------
# Initial Map
# -------------------
draw_map()

app.mainloop()
