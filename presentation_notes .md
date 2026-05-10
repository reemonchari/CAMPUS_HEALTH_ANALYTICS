# University Clinic Patient Prediction System
## Presentation Notes — Full Script

---
git add .
g
## OPENING (say this to introduce yourself and the project)

*"Good [morning/afternoon]. What I built is a prediction tool for a university clinic — specifically, a system that tells the clinic supervisor how many patients to expect on any given day, before that day arrives. The goal is simple: better planning, fewer surprises."*

---

## 1. THE PROBLEM

University clinics run on fixed staff and limited medication stock. The challenge is that demand is not fixed — it changes significantly depending on what is happening academically and what the weather is like.

During exam periods, students come in with stress headaches, anxiety, insomnia, and burnout. On rainy days, students who would normally push through illness come in because they are stuck on campus anyway. Without a way to anticipate these peaks, the clinic either overstaffs on quiet days or is caught short on busy ones.

This system solves that by giving the supervisor a prediction — a number — for each day on the calendar, generated automatically from two inputs they already have: the academic schedule and the city's weather.

---

## 2. WHAT THE MODEL IS BASED ON

The system uses a **Linear Regression model** trained on historical patient data from the clinic. Three variables were identified as the main drivers of daily patient volume:

**1. Exam Period**
Whether the day falls during an examination or CAT (Continuous Assessment Test) period. This is the single strongest predictor. Clinic visits rise sharply during high-stress academic periods.

**2. Rainfall**
The amount of rain expected that day. Higher rainfall correlates with more clinic visits — partly because wet conditions increase respiratory illness, and partly because students who feel unwell are more likely to seek care when they cannot comfortably avoid it.

**3. Temperature**
The expected maximum temperature. Extreme heat and cold both push more students to seek care. Mild temperatures see the fewest visits.

These three numbers go into the model, and the model returns an estimated patient count for the day.

---

## 3. HOW THE APP WORKS

The app has two modes, accessible as tabs at the top of the screen.

### Tab 1 — Calendar and Live Weather Mode

This is the primary mode for planning ahead.

**Step 1:** The supervisor uploads the university's academic calendar. The file can be a CSV or an Excel file. It needs a date column and ideally an exam period column — though the app is smart enough to figure this out even if the column is named differently or the file has extra columns.

**Step 2:** The supervisor types in the city name — for example, Nairobi.

**Step 3:** They click Run Predictions.

Behind the scenes, the app contacts the Open-Meteo weather service — a free, public API used by meteorological applications globally — and pulls real temperature and rainfall data for every date in the calendar. For past dates it uses the historical archive. For upcoming dates it uses the live forecast. Both are fetched automatically and combined.

The results appear as:
- Four summary tiles: total dates, exam days, average patients per day, and the peak day
- A line chart showing predicted patient volume across the full calendar period
- A full day-by-day table with date, period type, temperature, rainfall, and predicted patients
- A comparison table showing exam period averages versus regular day averages
- A download button to save everything as a CSV

**A note on weather coverage:** The app will tell you exactly how many dates had real weather data and how many fell back to defaults. If it says "180 of 195 dates covered", that means 15 dates used an assumed temperature and rainfall. That is normal for dates too recent for the archive or too far ahead for the forecast.

### Tab 2 — Quick Single-Day Estimate

This is for fast, informal questions. No file upload needed.

The supervisor selects three things from dropdowns:
- Academic period: Regular Day or Exam Period
- Rainfall: None, Light, Moderate, Heavy, or Very Heavy
- Temperature: Cold, Cool, Mild, Warm, or Hot

They press the button and get an estimated patient count, a ±15% range, and a plain sentence explaining the result in words.

---

## 4. THE CALENDAR FILE

The sample calendar provided covers the full **2025–2026 academic year** — 195 working days across both semesters. It follows a realistic Kenyan university structure:

| Period | Dates | Exam Flag |
|---|---|---|
| Semester 1 Teaching | September – November 2025 | 0 |
| Semester 1 CAT Week | October 2025 | 1 |
| Semester 1 Examinations | November – December 2025 | 1 |
| Semester Break | December 2025 – January 2026 | 0 |
| Semester 2 Teaching | January – March 2026 | 0 |
| Semester 2 CAT Week | February 2026 | 1 |
| Semester 2 Examinations | April – May 2026 | 1 |

All Kenyan public holidays are included and marked as Regular Days. The file also has extra columns — period label, day of week, semester, and notes — which the app ignores automatically. Only the date and exam_period columns are used for predictions.

---

## 5. WHAT MAKES THIS ROBUST

These are the things that make the app work reliably with any reasonable calendar file, not just the sample one:

- **Any date format is accepted.** Whether the file uses 2025-05-01, 01/05/2025, or May 1 2025, pandas converts it automatically.
- **Any column name for the date is accepted.** "Date", "event_date", "DATE" — the app finds it.
- **Extra columns are ignored.** A file with 10 columns works just as well as one with 2.
- **Exam period can be text or numbers.** A column with "Yes"/"No" works, as does one with 1/0 or "Exam"/"Regular".
- **If the exam column is missing entirely**, the app warns the supervisor and continues with all days treated as regular.
- **Past dates and future dates use different weather APIs** automatically — historical archive for past, forecast for upcoming — so a full academic year calendar works in one click without manual splitting.
- **Encoding issues are handled.** Files with special characters open correctly because the app tries UTF-8 first and falls back to latin-1.

---

## 6. THINGS TO EMPHASISE TO THE AUDIENCE

**It requires no technical knowledge to use.**
A supervisor uploads a file, types a city, and clicks one button. They do not need to understand machine learning, APIs, or data formats.

**It uses real data, not assumptions.**
The weather figures come from an actual meteorological service, not guesses. The model was trained on actual clinic records, not invented numbers.

**It covers the entire year in one action.**
195 days of predictions are generated in the time it takes to spin up the API call — a few seconds. That is the whole academic year planned before the semester even starts.

**It fails gracefully.**
If the weather API cannot cover some dates, the app tells you exactly which ones and fills them with sensible defaults rather than crashing. If the exam period column is missing, it warns you and continues.

**The output is portable.**
The full prediction table downloads as a CSV. A supervisor can open it in Excel, share it with the clinical team, or attach it to a staffing plan.

---

## 7. ANTICIPATED QUESTIONS

**"What type of model is this?"**
Linear Regression. It finds the straight-line relationship between the three input variables and the expected patient count. It was chosen because the relationship between stress, weather, and clinic attendance is expected to be proportional — not random or cyclical.

**"How accurate is it?"**
That depends on the training data. The ±15% range shown in single-day mode reflects the natural day-to-day variation that no model can fully predict — a disease outbreak, a campus event, an unusual weather event. The model is most useful for planning averages and trends, not for guaranteeing exact numbers.

**"What if our city name is not found?"**
The app uses a geocoding service that covers virtually every named city and town in the world. If a city is not found, the app shows an error and asks the user to check the spelling. Typing the country alongside the city — for example "Kisumu Kenya" — improves results for less-common names.

**"Can we add more prediction variables?"**
Yes. The model can be retrained with additional features — day of the week, student enrolment numbers, or even illness outbreak flags. The app is structured so that adding a new variable means updating the model training script and adding one dropdown to the manual entry tab.

**"Does this send our data anywhere?"**
The only external request the app makes is to the Open-Meteo weather API, which receives a city name and a date range — nothing about the clinic, patients, or the university. All processing happens locally on the machine running the app.

**"What if our calendar is in a different format?"**
The app accepts CSV or Excel. As long as there is a column with dates in it, the app will work. It handles different date formats, different column names, extra columns, and missing exam period columns.

---

## 8. CLOSING LINE

*"In summary — this takes two things the clinic already has, the academic schedule and the city's weather, and turns them into a forward-looking patient count for every working day of the year. It is not a replacement for clinical judgment, but it gives the person in charge a concrete number to plan around instead of guessing."*

---

## QUICK REFERENCE CARD (keep this open during the demo)

| What they ask | What to say |
|---|---|
| What does it do? | Predicts daily patient numbers using the academic calendar and weather |
| What variables? | Exam period, rainfall, temperature — trained on historical clinic data |
| How do I use it? | Upload calendar CSV → type city → click Run Predictions |
| What if the file format is different? | Any CSV or Excel with a date column works |
| Is it accurate? | Tracks trends well; ±15% on individual days is normal |
| Does it store data? | No — everything runs locally, only the weather API is called |
| Can it do the whole year? | Yes — 195 days predicted in one click |
