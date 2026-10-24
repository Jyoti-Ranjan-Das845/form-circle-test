"""Form templates: each builds the HTML for one realistic paper form.

Every circle-able option is a <span class="opt" data-qid=.. data-label=..>, and every
question's area carries data-qid, so the renderer can record exact boxes for grading.
All organisations, people and addresses are invented.
"""
import html
import random

HAND_FONTS = ["Caveat", "Homemade Apple", "Reenie Beanie", "Nanum Pen Script", "Kalam", "Shadows Into Light"]
INKS = ["#1b2a6b", "#14204f", "#222222", "#2b2b3a"]
FIRST = ["Jordan", "Priya", "Marcus", "Elena", "Tomás", "Grace", "Devon", "Aisha", "Liam", "Mei", "Owen", "Sofia"]
LAST = ["Ellis", "Raman", "Webb", "Novak", "Alvarez", "Okafor", "Hartley", "Chen", "Brennan", "Kowalski", "Patel", "Moreau"]

GOOGLE_FONTS = (
    "https://fonts.googleapis.com/css2?family=Caveat&family=Homemade+Apple&family=Reenie+Beanie"
    "&family=Nanum+Pen+Script&family=Kalam&family=Shadows+Into+Light&family=Special+Elite"
    "&family=Courier+Prime&family=EB+Garamond:wght@400;600&family=Source+Serif+4:wght@400;600;700"
    "&family=IBM+Plex+Sans:wght@400;600;700&family=Roboto+Condensed:wght@400;700&family=Comic+Neue:wght@400;700"
    "&family=Libre+Franklin:wght@400;600;800&display=block"
)

BASE_CSS = """
@page { size: 8.5in 11in; margin: 0; }
* { box-sizing: border-box; }
html, body { margin: 0; padding: 0; background: #fff; color: #111; }
.page { width: 816px; height: 1056px; padding: 46px 54px; position: relative; overflow: hidden; }
.opt { white-space: nowrap; display: inline-block; padding: 0 2px; }
.hw { position: relative; top: -3px; }
.line { display: inline-block; border-bottom: 1px solid #333; min-width: 120px; height: 20px; vertical-align: bottom; padding-left: 4px; }
table { border-collapse: collapse; }
.small { font-size: 9px; color: #444; }
.footer { position: absolute; bottom: 26px; left: 54px; right: 54px; font-size: 8.5px; color: #555; display: flex; justify-content: space-between; }
"""


class Form:
    def __init__(self, form_id, title, seed):
        self.form_id = form_id
        self.title = title
        self.rng = random.Random(seed)
        self.questions = []

    # --- question registry -------------------------------------------------
    def reg(self, text, options, select="one"):
        qid = f"q{len(self.questions) + 1}"
        self.questions.append({"id": qid, "text": text, "select": select, "options": list(options)})
        return qid

    def o(self, qid, label, display=None, cls=""):
        shown = html.escape(display if display is not None else label)
        return f'<span class="opt {cls}" data-qid="{qid}" data-label="{html.escape(label)}">{shown}</span>'

    def opts(self, qid, labels, gap=14, displays=None):
        displays = displays or labels
        return f'<span style="word-spacing:0">' + "".join(
            f'<span style="margin-right:{gap}px">{self.o(qid, l, d)}</span>' for l, d in zip(labels, displays)
        ) + "</span>"

    def inline(self, text, labels, select="one", note=None, gap=14, cls="qrow"):
        qid = self.reg(text, labels, select)
        note = note if note is not None else ("(circle one)" if select == "one" else "(circle all that apply)")
        return (f'<div class="{cls}" data-qid="{qid}"><span class="qt">{html.escape(text)}</span> '
                f'<span class="note">{note}</span>&nbsp;&nbsp; {self.opts(qid, labels, gap)}</div>')

    # --- handwriting fill-ins ---------------------------------------------
    def hw(self, text, size=None):
        font = self.rng.choice(HAND_FONTS)
        ink = self.rng.choice(INKS)
        size = size or self.rng.randint(17, 22)
        if font in ("Homemade Apple",):
            size -= 4
        rot = self.rng.uniform(-1.8, 1.8)
        return (f'<span class="hw" style="font-family:\'{font}\';color:{ink};font-size:{size}px;'
                f'display:inline-block;transform:rotate({rot:.1f}deg)">{html.escape(text)}</span>')

    def name(self):
        return f"{self.rng.choice(FIRST)} {self.rng.choice(LAST)}"

    def date(self):
        return f"{self.rng.randint(1, 12)}/{self.rng.randint(1, 28)}/{self.rng.choice([24, 25, 26])}"

    def field(self, label, value=None, width=180, fill_p=0.75):
        val = self.hw(value) if value and self.rng.random() < fill_p else ""
        return f'<span class="fl">{label}</span> <span class="line" style="width:{width}px">{val}</span>'


def page(css, body, footer_left="", footer_right=""):
    return f"""<!doctype html><html><head><meta charset="utf-8">
<link rel="stylesheet" href="{GOOGLE_FONTS}">
<style>{BASE_CSS}{css}</style></head><body><div class="page">{body}
<div class="footer"><span>{footer_left}</span><span>{footer_right}</span></div></div></body></html>"""


# =============================================================================
# 1. Patient intake
# =============================================================================
def patient_intake(f):
    css = """
    .page { font-family: Arial, Helvetica, sans-serif; font-size: 12.5px; }
    .hdr { display:flex; align-items:center; border-bottom: 3px solid #1d4f7a; padding-bottom: 8px; margin-bottom: 12px; }
    .logo { width: 40px; height: 40px; border-radius: 50%; background: #1d4f7a; color:#fff; font-weight:700; display:flex; align-items:center; justify-content:center; font-size: 18px; margin-right: 12px; }
    .org { font-size: 19px; font-weight: 700; color: #1d4f7a; } .sub { font-size: 11px; color:#444; }
    h2 { font-size: 14px; background:#dde7f0; padding: 4px 8px; margin: 14px 0 8px; }
    .row { margin: 9px 0; } .qrow { margin: 10px 0; } .note { font-size: 10.5px; color:#555; font-style: italic; }
    .qt { font-weight: 600; }
    table.mh { width: 100%; font-size: 12px; } table.mh td { border: 1px solid #888; padding: 5px 8px; }
    table.mh th { border: 1px solid #888; background:#eef2f6; padding: 4px; font-size: 11px; }
    td.yn { text-align:center; width: 46px; }
    """
    b = ['<div class="hdr"><div class="logo">R</div><div><div class="org">Riverside Family Health Clinic</div>'
         '<div class="sub">418 Alder Street, Suite 2 · Fairview · (555) 201-4470</div></div>'
         '<div style="margin-left:auto;text-align:right;font-weight:700;font-size:15px">NEW PATIENT<br>INTAKE FORM</div></div>']
    b.append("<h2>Patient Information</h2>")
    b.append(f'<div class="row">{f.field("Full name:", f.name(), 300)} &nbsp; {f.field("Date of birth:", f.date(), 140)}</div>')
    b.append(f'<div class="row">{f.field("Address:", None, 420)} &nbsp; {f.field("Phone:", "555-" + str(f.rng.randint(200, 999)) + "-" + str(f.rng.randint(1000, 9999)), 130)}</div>')
    b.append(f.inline("Sex:", ["Male", "Female", "Other"]))
    b.append(f.inline("Marital status:", ["Single", "Married", "Divorced", "Widowed", "Separated"]))
    b.append(f.inline("Preferred contact method:", ["Phone", "Email", "Text", "Mail"]))
    b.append(f.inline("Do you have health insurance?", ["Yes", "No"]))
    b.append("<h2>Medical History &mdash; circle Y or N for each condition</h2>")
    conds = ["Diabetes", "High blood pressure", "Asthma", "Heart disease", "Thyroid disorder", "Arthritis",
             "Depression / anxiety", "Cancer", "Kidney disease", "Migraines", "Seizures", "Stroke"]
    rows = []
    half = len(conds) // 2
    for i in range(half):
        cells = []
        for c in (conds[i], conds[i + half]):
            qid = f.reg(c, ["Y", "N"])
            cells.append(f'<td data-qid="{qid}">{c}</td><td class="yn" data-qid="{qid}">{f.o(qid, "Y")}</td>'
                         f'<td class="yn" data-qid="{qid}">{f.o(qid, "N")}</td>')
        rows.append("<tr>" + "".join(cells) + "</tr>")
    b.append('<table class="mh"><tr><th>Condition</th><th>Yes</th><th>No</th><th>Condition</th><th>Yes</th><th>No</th></tr>'
             + "".join(rows) + "</table>")
    b.append("<h2>Lifestyle</h2>")
    b.append(f.inline("Tobacco use:", ["Never", "Former", "Current"]))
    b.append(f.inline("Alcohol use:", ["None", "Occasional", "Weekly", "Daily"]))
    b.append(f.inline("Exercise:", ["Rarely", "1-2 times/week", "3-4 times/week", "5+ times/week"]))
    b.append(f.inline("Caffeine:", ["None", "1-2 cups/day", "3+ cups/day"]))
    b.append("<h2>Medications &amp; Allergies</h2>")
    b.append(f.inline("Are you allergic to any medications?", ["Yes", "No", "Not sure"]))
    b.append(f.inline("Are you currently pregnant?", ["Yes", "No", "N/A"]))
    b.append('<table class="mh"><tr><th style="width:40%">Current medication</th><th>Dose</th><th>How often</th></tr>'
             + "<tr><td>&nbsp;</td><td></td><td></td></tr>" * 3 + "</table>")
    b.append(f'<div class="row">{f.field("Preferred pharmacy:", None, 250)} &nbsp; {f.field("Emergency contact:", f.name(), 190)}</div>')
    b.append(f'<div class="row" style="margin-top:20px">{f.field("Patient signature:", f.name(), 260)} &nbsp; {f.field("Date:", f.date(), 120)}</div>')
    return page(css, "".join(b), "RFHC-101 Rev. 02/2025", "Page 1 of 1 · Please return to front desk")


# =============================================================================
# 2. Restaurant comment card
# =============================================================================
def comment_card(f):
    css = """
    .page { font-family: 'EB Garamond', Georgia, serif; font-size: 16px; padding: 60px 70px; }
    .frame { border: 2px solid #5b3a1e; outline: 1px solid #5b3a1e; outline-offset: 5px; padding: 30px 36px; height: 900px; }
    .t { text-align:center; font-size: 34px; color:#5b3a1e; letter-spacing: 2px; }
    .s { text-align:center; font-style: italic; margin-bottom: 18px; color:#5b3a1e; }
    table.r { width: 100%; margin: 6px 0 14px; } table.r td { padding: 7px 4px; border-bottom: 1px dotted #8a6a4a; }
    table.r td.n { text-align:center; width: 46px; font-size: 17px; }
    .anch { font-size: 12px; color:#5b3a1e; text-align:center; }
    .qrow { margin: 14px 0; } .note { font-size: 13px; font-style: italic; color:#6b4a2e; } .qt { font-weight:600; }
    """
    b = ['<div class="frame"><div class="t">MAPLE GROVE BISTRO</div><div class="s">We value your opinion &mdash; tell us about your visit</div>']
    b.append(f'<div>{f.field("Server:", f.rng.choice(FIRST), 150)} &nbsp; {f.field("Table #:", str(f.rng.randint(1, 30)), 60)} &nbsp; {f.field("Date:", f.date(), 120)}</div>')
    b.append(f.inline("Visit:", ["Breakfast", "Lunch", "Dinner"], gap=22))
    b.append('<div style="margin-top:10px;font-weight:600">Please circle a rating for each:</div>')
    rows = ['<tr><td></td>' + "".join(f'<td class="anch">{a}</td>' for a in ["Poor", "", "Average", "", "Excellent"]) + "</tr>"]
    for item in ["Food quality", "Speed of service", "Friendliness of staff", "Cleanliness", "Value for money", "Atmosphere"]:
        qid = f.reg(item, ["1", "2", "3", "4", "5"])
        rows.append(f'<tr data-qid="{qid}"><td>{item}</td>' + "".join(f'<td class="n">{f.o(qid, str(n))}</td>' for n in range(1, 6)) + "</tr>")
    b.append('<table class="r">' + "".join(rows) + "</table>")
    b.append(f.inline("How did you hear about us?", ["Friend", "Social media", "Walked by", "Online review", "Other"], gap=16))
    b.append(f.inline("Would you dine with us again?", ["Definitely", "Probably", "Not sure", "Probably not"], gap=16))
    b.append(f.inline("Party size:", ["1", "2", "3-4", "5+"], gap=22))
    b.append('<div style="margin-top:14px">Comments:</div>' + '<div style="border-bottom:1px solid #8a6a4a;height:30px"></div>' * 3)
    b.append(f.inline("May we add you to our mailing list?", ["Yes", "No"], gap=22))
    b.append(f'<div>{f.field("Email:", None, 380)}</div>')
    b.append("</div>")
    return page(css, "".join(b))


# =============================================================================
# 3. Pain assessment
# =============================================================================
def pain_assessment(f):
    css = """
    .page { font-family: 'IBM Plex Sans', Arial, sans-serif; font-size: 12.5px; }
    .top { display:flex; justify-content:space-between; align-items:flex-end; border-bottom: 2px solid #222; padding-bottom: 6px; }
    .org { font-weight:700; font-size: 17px; } .ft { font-size: 20px; font-weight:700; }
    .scale { margin: 10px 0 18px; } .scale .q { font-weight:600; margin-bottom: 4px; }
    .nums { display:flex; justify-content:space-between; width: 600px; margin-left: 20px; font-size: 15px; }
    .ends { display:flex; justify-content:space-between; width: 640px; font-size: 10px; color:#444; }
    .qrow { margin: 12px 0; } .note { font-size: 10.5px; color:#555; } .qt { font-weight:600; }
    .box { border: 1px solid #555; padding: 10px 14px; margin-top: 16px; }
    """
    b = ['<div class="top"><div><div class="org">Lakeside Physical Therapy &amp; Rehab</div><div class="small">2200 Shoreline Dr · Bldg C</div></div><div class="ft">PAIN ASSESSMENT</div></div>']
    b.append(f'<div style="margin:12px 0">{f.field("Name:", f.name(), 260)} &nbsp; {f.field("Visit date:", f.date(), 120)}</div>')
    b.append('<div class="small" style="margin-bottom:10px">Circle the ONE number that best describes your pain.</div>')
    for q in ["Pain level right now", "Worst pain in the past week", "Least pain in the past week"]:
        qid = f.reg(q, [str(n) for n in range(11)])
        b.append(f'<div class="scale" data-qid="{qid}"><div class="q">{q}</div><div class="nums">'
                 + "".join(f.o(qid, str(n)) for n in range(11))
                 + '</div><div class="ends"><span>No pain</span><span>Moderate</span><span>Worst possible pain</span></div></div>')
    b.append('<div class="box">')
    b.append(f.inline("Where is your pain?", ["Neck", "Shoulder", "Upper back", "Lower back", "Hip", "Knee", "Ankle", "Wrist"], "many", gap=12))
    b.append(f.inline("The pain feels:", ["Sharp", "Dull", "Burning", "Aching", "Throbbing", "Tingling", "Stabbing"], "many", gap=12))
    b.append(f.inline("The pain is:", ["Constant", "Comes and goes"], gap=20))
    b.append(f.inline("Since your last visit, the pain is:", ["Better", "Worse", "About the same"], gap=16))
    b.append(f.inline("Does pain affect your sleep?", ["Never", "Sometimes", "Often", "Every night"], gap=16))
    b.append(f.inline("How long have you had this pain?", ["Less than 1 week", "1-4 weeks", "1-3 months", "Over 3 months"], gap=12))
    b.append(f.inline("Activities that make it worse:", ["Sitting", "Standing", "Walking", "Lifting", "Bending", "Stairs", "Driving"], "many", gap=10))
    b.append(f.inline("Have you had physical therapy before?", ["Yes", "No"], gap=20))
    b.append("</div>")
    b.append('<div style="margin-top:14px;font-weight:600">What would you like to be able to do again?</div>'
             + '<div style="border-bottom:1px solid #555;height:26px"></div>' * 3)
    b.append('<div class="box"><b>FOR CLINIC USE</b><br>'
             + f.inline("Plan:", ["Continue", "Modify", "Re-evaluate", "Discharge"], gap=14)
             + f'{f.field("Therapist initials:", None, 80)} &nbsp; {f.field("Next visit:", None, 110)}</div>')
    return page(css, "".join(b), "LPT-PA-04", "Confidential patient information")


# =============================================================================
# 4. Employee engagement survey (dense Likert grid)
# =============================================================================
def employee_survey(f):
    css = """
    .page { font-family: 'Roboto Condensed', Arial Narrow, sans-serif; font-size: 12px; }
    .band { background: #2d2d2d; color: #fff; padding: 10px 14px; display:flex; justify-content:space-between; }
    .band b { font-size: 18px; letter-spacing: 1px; }
    .legend { margin: 10px 0; font-size: 11px; border: 1px solid #999; padding: 6px 10px; }
    table.lk { width: 100%; } table.lk th { background:#e4e4e4; font-size: 10.5px; padding: 5px 2px; border: 1px solid #aaa; }
    table.lk td { border: 1px solid #bbb; padding: 8px 6px; } table.lk td.c { text-align:center; width: 44px; font-weight:700; font-size: 12.5px; }
    table.lk tr:nth-child(even) td { background: #f3f3f3; }
    .qrow { margin: 10px 0; } .note { font-size: 10px; color:#555; } .qt { font-weight:700; }
    """
    b = ['<div class="band"><b>CORVANE LOGISTICS</b><span>Annual Employee Engagement Survey 2025</span></div>']
    b.append('<div class="legend">Circle one response per statement: <b>SD</b> = Strongly Disagree &nbsp; <b>D</b> = Disagree &nbsp; <b>N</b> = Neutral &nbsp; <b>A</b> = Agree &nbsp; <b>SA</b> = Strongly Agree. Responses are anonymous.</div>')
    b.append(f.inline("Department:", ["Warehouse", "Transport", "Office", "Customer Service", "IT", "Management"], gap=10))
    b.append(f.inline("Years with company:", ["<1", "1-3", "4-6", "7-10", "10+"], gap=14))
    stmts = ["I understand what is expected of me at work.", "I have the tools and equipment to do my job well.",
             "My supervisor gives me useful feedback.", "I feel my work is recognized.", "Communication between teams is effective.",
             "I have opportunities to learn and grow.", "My workload is manageable.", "Safety is a priority in my area.",
             "I would recommend this company as a place to work.", "I see myself working here in two years.",
             "Shift schedules are fair.", "Management listens to employee concerns.", "I am paid fairly for the work I do.",
             "I feel part of a team."]
    scale = ["SD", "D", "N", "A", "SA"]
    rows = ['<tr><th style="text-align:left;padding-left:8px">#&nbsp; Statement</th>' + "".join(f"<th>{s}</th>" for s in scale) + "</tr>"]
    for i, s in enumerate(stmts, 1):
        qid = f.reg(s, scale)
        rows.append(f'<tr data-qid="{qid}"><td>{i}. {s}</td>' + "".join(f'<td class="c">{f.o(qid, x)}</td>' for x in scale) + "</tr>")
    b.append('<table class="lk">' + "".join(rows) + "</table>")
    b.append(f.inline("Overall, how satisfied are you with your job?", ["Very satisfied", "Satisfied", "Neutral", "Dissatisfied", "Very dissatisfied"], gap=10))
    b.append(f.inline("Your usual shift:", ["Day", "Evening", "Night", "Rotating"], gap=14))
    b.append('<div style="margin-top:10px;font-weight:700">What is one thing that would make Corvane a better place to work?</div>'
             + '<div style="border-bottom:1px solid #888;height:26px"></div>' * 3)
    return page(css, "".join(b), "HR-ES-2025 · Do not write your name on this form", "Return to the sealed box in the break room")


# =============================================================================
# 5. Course evaluation (two columns, serif)
# =============================================================================
def course_evaluation(f):
    css = """
    .page { font-family: 'Times New Roman', Times, serif; font-size: 13px; }
    .t { text-align:center; } .t .c { font-size: 18px; font-weight: 700; letter-spacing: 1px; } .t .d { font-size: 14px; }
    .meta { margin: 12px 0; display:flex; gap: 20px; flex-wrap: wrap; }
    .legend { text-align:center; font-size: 12px; border-top: 1px solid #000; border-bottom: 1px solid #000; padding: 4px; margin: 8px 0; }
    .cols { columns: 2; column-gap: 30px; }
    .it { break-inside: avoid; margin: 0 0 10px; } .it .n { display:flex; gap: 22px; margin: 3px 0 0 18px; font-size: 14px; }
    .sec { font-weight: 700; font-variant: small-caps; font-size: 14px; margin: 6px 0; break-after: avoid; }
    .qrow { margin: 9px 0; break-inside: avoid; } .note { font-size: 11px; font-style: italic; } .qt { font-weight: 700; }
    """
    b = ['<div class="t"><div class="c">NORTHFIELD COMMUNITY COLLEGE</div><div class="d">Student Evaluation of Instruction</div></div>']
    b.append(f'<div class="meta">{f.field("Course:", f.rng.choice(["BIO 110", "ENG 102", "MATH 140", "HIST 201", "CHEM 121"]), 100)} {f.field("Section:", str(f.rng.randint(1, 9)).zfill(2), 45)} {f.field("Instructor:", None, 150)} {f.field("Term:", f.rng.choice(["Fall", "Spring"]) + " 25", 75)}</div>')
    b.append('<div class="legend">1 = Strongly disagree &nbsp;&nbsp; 2 = Disagree &nbsp;&nbsp; 3 = Neutral &nbsp;&nbsp; 4 = Agree &nbsp;&nbsp; 5 = Strongly agree &nbsp;&nbsp; (circle one number)</div>')
    secs = {"The Instructor": ["Explained concepts clearly.", "Was well prepared for class.", "Encouraged questions.", "Was available outside class.", "Returned work promptly.", "Treated students with respect."],
            "The Course": ["Objectives were clear.", "Assignments helped me learn.", "Exams reflected course material.", "Workload was reasonable.", "Textbook was useful.", "I would recommend this course."]}
    b.append('<div class="cols">')
    k = 1
    for sec, items in secs.items():
        b.append(f'<div class="sec">{sec}</div>')
        for it in items:
            qid = f.reg(it, ["1", "2", "3", "4", "5"])
            b.append(f'<div class="it" data-qid="{qid}">{k}. {it}<div class="n">' + "".join(f.o(qid, str(n)) for n in range(1, 6)) + "</div></div>")
            k += 1
    b.append("</div>")
    b.append(f.inline("Expected grade:", ["A", "B", "C", "D", "F"], gap=18))
    b.append(f.inline("This course was:", ["Required", "Elective"], gap=18))
    b.append(f.inline("Hours per week spent outside class:", ["0-2", "3-5", "6-8", "9+"], gap=18))
    b.append(f.inline("Attendance:", ["Always", "Usually", "Sometimes", "Rarely"], gap=18))
    b.append(f.inline("Overall rating of this instructor:", ["Excellent", "Good", "Average", "Below average", "Poor"], gap=14))
    for prompt in ["What did you like most about this course?", "What could be improved?"]:
        b.append(f'<div style="margin-top:10px">{prompt}</div>' + '<div style="border-bottom:1px solid #000;height:26px"></div>' * 3)
    return page(css, "".join(b), "Form IR-7", "Office of Institutional Research")


# =============================================================================
# 6. Multiple-choice quiz (options are full text lines)
# =============================================================================
def science_quiz(f):
    css = """
    .page { font-family: 'Source Serif 4', Georgia, serif; font-size: 13px; }
    .h { display:flex; justify-content:space-between; border-bottom: 1px solid #000; padding-bottom: 6px; }
    .h .t { font-size: 18px; font-weight:700; }
    .ins { margin: 10px 0; font-style: italic; }
    .cols { columns: 2; column-gap: 34px; }
    .mq { break-inside: avoid; margin-bottom: 14px; } .mq .s { font-weight: 600; margin-bottom: 3px; }
    .mq .opt { display:block; margin: 3px 0 3px 16px; width: fit-content; }
    """
    qs = [("Which organelle produces most of a cell's energy?", ["Nucleus", "Mitochondria", "Ribosome", "Golgi body"]),
          ("What is the chemical symbol for sodium?", ["S", "So", "Na", "Sd"]),
          ("Which planet is closest to the Sun?", ["Venus", "Earth", "Mars", "Mercury"]),
          ("Water boils at what temperature at sea level?", ["90 °C", "100 °C", "110 °C", "212 °C"]),
          ("Which gas do plants absorb from the air?", ["Oxygen", "Nitrogen", "Carbon dioxide", "Hydrogen"]),
          ("What force keeps planets in orbit?", ["Magnetism", "Friction", "Gravity", "Inertia"]),
          ("Which of these is a mammal?", ["Shark", "Dolphin", "Salmon", "Octopus"]),
          ("What is the hardest natural substance?", ["Gold", "Iron", "Quartz", "Diamond"]),
          ("Sound travels fastest through:", ["Air", "Water", "Steel", "A vacuum"]),
          ("The pH of pure water is about:", ["3", "5", "7", "9"]),
          ("Which blood cells fight infection?", ["Red blood cells", "White blood cells", "Platelets", "Plasma"]),
          ("Light from the Sun reaches Earth in about:", ["8 seconds", "8 minutes", "8 hours", "8 days"])]
    b = [f'<div class="h"><div class="t">Unit 4 Science Quiz</div><div>{f.field("Name:", f.name(), 190)} &nbsp; {f.field("Period:", str(f.rng.randint(1, 7)), 40)}</div></div>']
    b.append('<div class="ins">Circle the letter of the best answer for each question.</div><div class="cols">')
    for i, (q, ops) in enumerate(qs, 1):
        labels = [f"{l}. {o}" for l, o in zip("abcd", ops)]
        qid = f.reg(q, labels)
        b.append(f'<div class="mq" data-qid="{qid}"><div class="s">{i}. {html.escape(q)}</div>' + "".join(f.o(qid, l) for l in labels) + "</div>")
    b.append("</div>")
    b.append('<div style="border-top:1px solid #000;margin-top:6px;padding-top:8px;font-weight:600">Part B &mdash; True or False. Circle T or F.</div>'
             '<table style="width:100%;margin-top:6px">')
    tf = ["The Moon produces its own light.", "Humans have 206 bones as adults.", "Ice is denser than liquid water.",
          "Bats are mammals.", "Electricity flows easily through rubber."]
    for i, s in enumerate(tf, 13):
        qid = f.reg(s, ["T", "F"])
        b.append(f'<tr data-qid="{qid}"><td style="padding:5px 0">{i}. {s}</td><td style="width:40px;text-align:center">{f.o(qid, "T")}</td>'
                 f'<td style="width:40px;text-align:center">{f.o(qid, "F")}</td></tr>')
    b.append("</table>")
    return page(css, "".join(b), "Mr. Halvorsen · Grade 8 Physical & Life Science", "Score: ______ / 17")


# =============================================================================
# 7. 5K race registration (colour header, inline sizes)
# =============================================================================
def race_registration(f):
    css = """
    .page { font-family: 'Libre Franklin', Arial, sans-serif; font-size: 12.5px; }
    .hero { background: linear-gradient(90deg,#0e6ba8,#13a0a8); color:#fff; padding: 16px 20px; border-radius: 4px; }
    .hero .a { font-size: 26px; font-weight: 800; } .hero .b { font-size: 13px; }
    .sec { font-weight: 800; color:#0e6ba8; border-bottom: 2px solid #0e6ba8; margin: 16px 0 8px; font-size: 13px; text-transform: uppercase; letter-spacing: 1px; }
    .row { margin: 9px 0; } .qrow { margin: 11px 0; } .note { font-size: 10px; color:#666; } .qt { font-weight: 600; }
    .waiver { font-size: 8.8px; line-height: 1.35; color: #333; text-align: justify; border: 1px solid #aaa; padding: 8px; margin-top: 10px; }
    """
    b = ['<div class="hero"><div class="a">Tri-County Charity 5K Run &amp; Walk</div><div class="b">Saturday, May 16 · Willow Creek Park · Proceeds support local food banks</div></div>']
    b.append('<div class="sec">Participant</div>')
    b.append(f'<div class="row">{f.field("Name:", f.name(), 280)} &nbsp; {f.field("Age:", str(f.rng.randint(12, 70)), 50)}</div>')
    b.append(f'<div class="row">{f.field("Email:", None, 300)} &nbsp; {f.field("Emergency contact:", f.name(), 170)}</div>')
    b.append(f.inline("Gender:", ["Male", "Female", "Non-binary", "Prefer not to say"], gap=14))
    b.append(f.inline("Age group:", ["Under 15", "15-19", "20-29", "30-39", "40-49", "50-59", "60+"], gap=10))
    b.append('<div class="sec">Event</div>')
    b.append(f.inline("Event:", ["5K Run", "5K Walk", "1-Mile Kids Fun Run"], gap=16))
    b.append(f.inline("T-shirt size:", ["XS", "S", "M", "L", "XL", "XXL"], gap=16))
    b.append(f.inline("Have you run a 5K before?", ["Yes", "No"], gap=18))
    b.append(f.inline("Expected finish time:", ["Under 25 min", "25-35 min", "35-45 min", "Over 45 min"], gap=12))
    b.append(f.inline("Post-race meal:", ["Pasta", "Garden salad", "Veggie wrap", "No meal"], gap=12))
    b.append(f.inline("How did you hear about the race?", ["Flyer", "Radio", "Friend", "Facebook", "School", "Other"], gap=10))
    b.append(f.inline("Registration fee:", ["$25 Adult", "$15 Student", "$10 Child"], gap=14, note="(circle one &mdash; payable at check-in)"))
    b.append('<div class="waiver"><b>Release and waiver.</b> I understand that participating in this event involves physical exertion and I certify that I am physically fit and have trained sufficiently for this event. I agree to follow the instructions of event officials and volunteers. I give permission for the organizers to use photographs taken during the event for promotional purposes. I acknowledge that the organizers, sponsors, and volunteers are not responsible for lost or stolen items. Parent or guardian signature is required for participants under 18. Fees are non-refundable; the event will proceed rain or shine.</div>')
    b.append(f'<div class="row" style="margin-top:14px">{f.field("Signature:", f.name(), 250)} &nbsp; {f.field("Date:", f.date(), 110)}</div>')
    b.append(f'<div class="row">{f.field("Parent / guardian (if under 18):", None, 300)}</div>')
    b.append('<div class="sec">Volunteers &amp; Office Use</div>')
    b.append(f.inline("Interested in volunteering at a future event?", ["Yes", "No", "Maybe"], gap=16))
    b.append(f.inline("Payment received:", ["Cash", "Check", "Card", "Waived"], gap=16, note="(office use)"))
    b.append(f.inline("Packet picked up:", ["Friday", "Race morning"], gap=16, note="(office use)"))
    return page(css, "".join(b), "Mail to: Tri-County 5K, PO Box 77, Willow Creek", "Office use: Bib # ______")


# =============================================================================
# 8. Vintage product-test questionnaire (typewriter, codes, column numbers)
# =============================================================================
def vintage_product_test(f):
    css = """
    .page { font-family: 'Courier Prime', 'Courier New', monospace; font-size: 13px; }
    .tl { font-size: 11px; line-height: 1.3; } .tr { position:absolute; top: 46px; right: 54px; border: 1px solid #000; padding: 6px 8px; font-size: 10px; width: 210px; text-align:center; }
    .c { text-align:center; margin-top: 18px; } .c u { display:block; margin: 2px 0; }
    .side { position:absolute; right: 54px; top: 230px; width: 90px; border-left: 1px solid #000; padding-left: 6px; font-size: 10px; line-height: 2.4; }
    .main { width: 560px; }
    .mq { margin: 14px 0; } .mq .opt { display:block; width: fit-content; margin: 2px 0 2px 40px; white-space: pre; }
    .ins { margin: 14px 0; text-transform: uppercase; }
    """
    b = ['<div class="tl">Home Taste Institute<br>Box 812<br>Glen Harbor, N.Y.</div>',
         '<div class="tr">Please disregard numbers. They are for tabulating purposes only.</div>',
         '<div class="c"><u>PRODUCT TEST</u><u>REPORT FORM</u><u>PART I</u></div>',
         '<div class="ins">To be answered immediately after you have finished trying sample K-14, and before you open sample M-7.</div>',
         '<div class="side">Do not write<br>in this space<br>(6)<br>(7)<br>(8)<br>(9)<br>(10)<br>(11)<br>(12)<br>(13)</div><div class="main">',
         '<div style="text-align:center;margin:8px 0">CIRCLE ONE CODE ONLY</div>']
    qs = [("1. Overall, how would you rate sample K-14?", ["Excellent", "Very good", "Good", "Fair", "Poor"]),
          ("2. How does it compare with the brand you usually buy?", ["Much better", "Somewhat better", "About the same", "Somewhat worse", "Much worse"]),
          ("3. How would you describe the flavor?", ["Much too strong", "A little too strong", "Just right", "A little too mild", "Much too mild"]),
          ("4. If this product were available at your store, would you:", ["Definitely buy it", "Probably buy it", "Might or might not", "Probably not buy it", "Definitely not buy it"]),
          ("5. How often do you buy products of this type?", ["Once a week or more", "2-3 times a month", "Once a month", "Less often"]),
          ("6. Which sample did you prefer?", ["Sample K-14", "Sample M-7", "No preference"]),
          ("7. Into which group does your age fall?", ["Under 25", "25-34", "35-49", "50 or over"])]
    for q, ops in qs:
        labels = [f"{o} {'.' * (26 - len(o))} {i}" for i, o in enumerate(ops, 1)]
        qid = f.reg(q, labels)
        b.append(f'<div class="mq" data-qid="{qid}">{html.escape(q)}' + "".join(f.o(qid, l) for l in labels) + "</div>")
    b.append("</div>")
    return page(css, "".join(b), "", f"{f.rng.randint(1000, 9999)}  {f.rng.randint(100, 999)}")


# =============================================================================
# 9. Visitor health screening (big YES / NO table)
# =============================================================================
def health_screening(f):
    css = """
    .page { font-family: Verdana, Geneva, sans-serif; font-size: 12px; }
    .t { font-size: 20px; font-weight: 700; text-align:center; border: 3px double #000; padding: 8px; }
    .s { text-align:center; margin: 6px 0 14px; font-size: 11px; }
    table.yn { width: 100%; } table.yn td, table.yn th { border: 1.5px solid #000; padding: 10px 10px; }
    table.yn th { background: #d9d9d9; } table.yn td.c { text-align:center; width: 70px; font-weight: 700; font-size: 14px; }
    .qrow { margin: 13px 0; } .note { font-size: 10px; } .qt { font-weight: 700; } .row { margin: 12px 0; }
    """
    b = ['<div class="t">VISITOR HEALTH SCREENING</div><div class="s">Cedar Hills Senior Living Community · Complete before entering</div>']
    b.append(f'<div class="row">{f.field("Visitor name:", f.name(), 250)} &nbsp; {f.field("Date:", f.date(), 110)} &nbsp; {f.field("Time in:", f.rng.choice(["9:15", "10:40", "1:05", "3:30"]), 60)}</div>')
    b.append(f.inline("Visitor type:", ["Family", "Friend", "Vendor", "Contractor", "Volunteer", "Clergy"], gap=10))
    b.append('<div style="margin:10px 0 6px;font-weight:700">In the last 10 days, have you had any of the following? Circle YES or NO.</div>')
    qs = ["Fever of 100.4 °F or higher", "New cough or shortness of breath", "Sore throat", "Vomiting or diarrhea",
          "New loss of taste or smell", "Close contact with someone who was sick", "Travel outside the country"]
    rows = ['<tr><th style="text-align:left">Question</th><th>YES</th><th>NO</th></tr>']
    for q in qs:
        qid = f.reg(q, ["YES", "NO"])
        rows.append(f'<tr data-qid="{qid}"><td>{q}</td><td class="c">{f.o(qid, "YES")}</td><td class="c">{f.o(qid, "NO")}</td></tr>')
    b.append('<table class="yn">' + "".join(rows) + "</table>")
    b.append(f.inline("Resident you are visiting is on floor:", ["1", "2", "3", "Memory Care"], gap=18))
    b.append(f.inline("Did you receive a visitor badge?", ["Yes", "No"], gap=20))
    b.append(f.inline("Purpose of visit:", ["Social visit", "Care meeting", "Delivery", "Maintenance", "Other"], gap=12))
    b.append(f.inline("Are you up to date on your flu vaccine?", ["Yes", "No", "Prefer not to say"], gap=14))
    b.append('<div class="small" style="margin-top:10px">I confirm that the answers above are true to the best of my knowledge. I will wear a mask if asked by staff and will leave the building if I develop symptoms during my visit.</div>')
    b.append(f'<div class="row">{f.field("Visitor signature:", f.name(), 260)}</div>')
    b.append('<div style="margin-top:18px;border:1px solid #000;padding:8px"><b>STAFF USE ONLY</b><br>'
             + f.inline("Entry:", ["Approved", "Denied", "Referred to nurse"], gap=14) + f'{f.field("Staff initials:", None, 70)}</div>')
    return page(css, "".join(b), "Form IC-12 (rev. 2024)", "Keep on file 30 days")


# =============================================================================
# 10. Vehicle inspection checklist (dense 3-option grid, two columns)
# =============================================================================
def vehicle_inspection(f):
    css = """
    .page { font-family: Arial, Helvetica, sans-serif; font-size: 11px; }
    .t { display:flex; justify-content:space-between; align-items:center; border: 2px solid #000; padding: 6px 10px; }
    .t b { font-size: 17px; }
    .meta { display:flex; gap: 18px; margin: 10px 0; white-space: nowrap; }
    .ins { font-size: 10.5px; margin-bottom: 6px; }
    .grid { display:flex; gap: 14px; }
    table.vi { width: 50%; } table.vi th { background:#000; color:#fff; font-size: 10px; padding: 4px; }
    table.vi td { border: 1px solid #666; padding: 4px 5px; } table.vi td.c { text-align:center; width: 46px; font-size: 10.5px; }
    .qrow { margin: 10px 0; } .note { font-size: 9.5px; } .qt { font-weight: 700; }
    """
    b = ['<div class="t"><b>DRIVER\'S DAILY VEHICLE INSPECTION REPORT</b><span>Brightline Fleet Services</span></div>']
    b.append(f'<div class="meta">{f.field("Driver:", f.name(), 150)}{f.field("Truck #:", str(f.rng.randint(100, 999)), 70)}{f.field("Odometer:", str(f.rng.randint(20000, 240000)), 90)}</div>')
    b.append(f.inline("Inspection type:", ["Pre-trip", "Post-trip"], gap=16))
    b.append('<div class="ins">For each item circle <b>OK</b>, <b>R</b> (needs repair) or <b>N/A</b>.</div>')
    items = ["Air compressor", "Battery", "Belts and hoses", "Brakes - parking", "Brakes - service", "Clutch", "Coupling devices",
             "Defroster / heater", "Drive line", "Engine", "Exhaust", "Fifth wheel", "Fluid levels", "Frame and assembly",
             "Fuel tanks", "Horn", "Lights - head/stop", "Lights - tail/dash", "Mirrors", "Muffler", "Oil pressure", "Radiator",
             "Rear end", "Reflectors", "Steering", "Suspension", "Tires", "Wheels and rims", "Windows", "Windshield wipers"]
    half = len(items) // 2
    tables = []
    for chunk in (items[:half], items[half:]):
        rows = ["<tr><th style='text-align:left'>Item</th><th>OK</th><th>REPAIR</th><th>N/A</th></tr>"]
        for it in chunk:
            qid = f.reg(it, ["OK", "R", "N/A"])
            rows.append(f'<tr data-qid="{qid}"><td>{it}</td>' + "".join(f'<td class="c">{f.o(qid, x)}</td>' for x in ["OK", "R", "N/A"]) + "</tr>")
        tables.append('<table class="vi">' + "".join(rows) + "</table>")
    b.append('<div class="grid">' + "".join(tables) + "</div>")
    b.append(f'<div style="margin:12px 0 4px"><b>TRAILER</b> &nbsp; {f.field("Trailer #:", None, 80)}</div>')
    trailer = ["Brake connections", "Brakes", "Coupling chains", "Coupling pin", "Doors", "Hitch", "Landing gear", "Lights - all",
               "Roof", "Suspension", "Tarpaulin", "Tires"]
    tables = []
    for chunk in (trailer[:6], trailer[6:]):
        rows = ["<tr><th style='text-align:left'>Item</th><th>OK</th><th>REPAIR</th><th>N/A</th></tr>"]
        for it in chunk:
            qid = f.reg(f"Trailer: {it}", ["OK", "R", "N/A"])
            rows.append(f'<tr data-qid="{qid}"><td>{it}</td>' + "".join(f'<td class="c">{f.o(qid, x)}</td>' for x in ["OK", "R", "N/A"]) + "</tr>")
        tables.append('<table class="vi">' + "".join(rows) + "</table>")
    b.append('<div class="grid">' + "".join(tables) + "</div>")
    b.append(f.inline("Condition of the above vehicle is:", ["Satisfactory", "Unsatisfactory"], gap=16))
    b.append(f.inline("Defects need to be corrected before operation?", ["Yes", "No"], gap=16))
    b.append('<div style="margin-top:6px">Remarks:</div><div style="border-bottom:1px solid #000;height:22px"></div><div style="border-bottom:1px solid #000;height:22px"></div>')
    b.append(f'<div style="margin-top:14px">{f.field("Driver signature:", f.name(), 210)} &nbsp; {f.field("Mechanic signature:", None, 190)}</div>')
    return page(css, "".join(b), "BFS-DVIR-3", "Keep in cab for 24 hours")


# =============================================================================
# 11. Rental application (dense inline options, field boxes)
# =============================================================================
def rental_application(f):
    css = """
    .page { font-family: 'IBM Plex Sans', Arial, sans-serif; font-size: 11.5px; }
    .h { display:flex; justify-content:space-between; align-items:flex-end; }
    .h .a { font-size: 22px; font-weight: 700; } .h .b { text-align:right; font-size: 10px; }
    .sec { background:#333; color:#fff; padding: 3px 8px; font-weight: 700; margin: 12px 0 6px; font-size: 11px; letter-spacing: 1px; }
    .boxes { display:grid; grid-template-columns: 2fr 1fr 1fr; border: 1px solid #333; }
    .boxes div { border: 1px solid #999; padding: 3px 6px; height: 40px; font-size: 9px; color:#444; }
    .boxes div .hw { display:block; margin-top: 2px; }
    .qrow { margin: 7px 0; } .note { font-size: 9px; color:#666; } .qt { font-weight: 600; }
    """
    def box(label, val):
        v = f.hw(val, 18) if val else ""
        return f"<div>{label}{v}</div>"
    b = ['<div class="h"><div class="a">Rental Application</div><div class="b"><b>Oakridge Property Management</b><br>90 Fenwick Ave · Unit applications</div></div>']
    b.append('<div class="sec">APPLICANT</div>')
    b.append('<div class="boxes">' + box("Full legal name", f.name()) + box("Date of birth", f.date()) + box("Phone", None)
             + box("Current address", None) + box("City", f.rng.choice(["Fairview", "Glen Harbor", "Milton"])) + box("Move-in date", f.date()) + "</div>")
    b.append(f.inline("Current housing:", ["Own", "Rent", "Live with family", "Other"], gap=12))
    b.append(f.inline("How long at current address?", ["<1 yr", "1-2 yrs", "3-5 yrs", "5+ yrs"], gap=12))
    b.append(f.inline("Reason for moving:", ["Job", "Family", "Price", "Size", "Location", "Other"], gap=10))
    b.append('<div class="sec">EMPLOYMENT &amp; INCOME</div>')
    b.append(f.inline("Employment status:", ["Full-time", "Part-time", "Self-employed", "Unemployed", "Retired", "Student"], gap=8))
    b.append(f.inline("Gross annual household income:", ["Under $25k", "$25-50k", "$50-75k", "$75-100k", "Over $100k"], gap=8))
    b.append(f.inline("Pay frequency:", ["Weekly", "Biweekly", "Monthly"], gap=12))
    b.append('<div class="boxes">' + box("Employer", f.rng.choice(["Halvern Foods", "City Transit", "Brightline Fleet", "Self"])) + box("Position", None) + box("Years employed", None) + "</div>")
    b.append('<div class="sec">HOUSEHOLD</div>')
    b.append(f.inline("Bedrooms needed:", ["Studio", "1", "2", "3", "4+"], gap=16))
    b.append(f.inline("Number of occupants:", ["1", "2", "3", "4", "5", "6+"], gap=16))
    b.append(f.inline("Pets:", ["None", "Dog", "Cat", "Bird", "Other"], "many", gap=12))
    b.append(f.inline("Does anyone in the household smoke?", ["Yes", "No"], gap=16))
    b.append(f.inline("Vehicles:", ["0", "1", "2", "3+"], gap=16))
    b.append(f.inline("Have you ever been evicted?", ["Yes", "No"], gap=16))
    b.append(f.inline("Have you ever filed for bankruptcy?", ["Yes", "No"], gap=16))
    b.append('<div class="sec">RENTAL HISTORY &amp; PREFERENCES</div>')
    b.append('<div class="boxes">' + box("Previous landlord", None) + box("Landlord phone", None) + box("Monthly rent paid", f.rng.choice(["$1,150", "$980", "$1,420"])) + "</div>")
    b.append(f.inline("Preferred lease term:", ["6 months", "12 months", "18 months", "24 months"], gap=12))
    b.append(f.inline("Parking needed:", ["None", "1 space", "2 spaces", "Garage"], gap=12))
    b.append(f.inline("Do you have renter's insurance?", ["Yes", "No", "Will purchase"], gap=12))
    b.append(f.inline("How did you find this listing?", ["Website", "Sign", "Referral", "Rental app", "Newspaper"], gap=10))
    b.append('<div class="small" style="margin-top:10px">I certify that the information provided is true and complete. I authorize Oakridge Property Management to verify the information above, including contacting employers and prior landlords. A non-refundable application fee of $40 is required.</div>')
    b.append(f'<div style="margin-top:12px">{f.field("Applicant signature:", f.name(), 230)} &nbsp; {f.field("Date:", f.date(), 100)}</div>')
    return page(css, "".join(b), "OPM-RA-1 2025", "Page 1 of 2")


# =============================================================================
# 12. Elementary student survey (friendly font, kid-style)
# =============================================================================
def student_survey(f):
    css = """
    .page { font-family: 'Comic Neue', 'Comic Sans MS', sans-serif; font-size: 15px; }
    .t { text-align:center; font-size: 28px; font-weight: 700; } .s { text-align:center; margin-bottom: 14px; }
    .card { border: 2px dashed #555; border-radius: 14px; padding: 8px 16px; margin: 11px 0; }
    .qrow { margin: 4px 0; } .qt { font-weight: 700; display:block; margin-bottom: 4px; } .note { font-size: 12px; color:#555; }
    .opt { font-size: 16px; }
    """
    b = ['<div class="t">All About Me!</div><div class="s">Elm Street Elementary · Student Survey · Grades 3-5</div>']
    b.append(f'<div>{f.field("My first name:", f.rng.choice(FIRST), 180)} &nbsp; {f.field("Grade:", str(f.rng.randint(3, 5)), 50)}</div>')
    qs = [("How do you get to school?", ["Walk", "Bus", "Car", "Bike", "Scooter"], "one"),
          ("What is your favorite subject?", ["Math", "Reading", "Science", "Art", "P.E.", "Music"], "one"),
          ("Do you eat breakfast before school?", ["Every day", "Some days", "Never"], "one"),
          ("How much do you like reading?", ["Not at all", "A little", "A lot"], "one"),
          ("What do you like to do at recess?", ["Play tag", "Swings", "Soccer", "Talk with friends", "Read"], "many"),
          ("How many hours do you sleep?", ["6 or less", "7", "8", "9", "10 or more"], "one"),
          ("Do you have a pet?", ["Yes", "No"], "one"),
          ("How do you feel about homework?", ["I like it", "It's okay", "I don't like it"], "one"),
          ("How do you feel at school most days?", ["Happy", "Okay", "Sad", "Worried"], "one"),
          ("Which do you like more?", ["Cats", "Dogs", "Both", "Neither"], "one")]
    for q, ops, sel in qs:
        b.append(f'<div class="card">{f.inline(q, ops, sel, gap=24, note="(circle all you like)" if sel == "many" else "(circle one)")}</div>')
    return page(css, "".join(b), "Thank you for helping us!", "Room ____")


# =============================================================================
# 13. Hotel guest feedback (word columns: Excellent / Good / Fair / Poor)
# =============================================================================
def hotel_feedback(f):
    css = """
    .page { font-family: Georgia, 'Times New Roman', serif; font-size: 13px; }
    .band { border-top: 6px solid #7a1f3d; border-bottom: 1px solid #7a1f3d; padding: 10px 0; text-align:center; }
    .band .a { font-size: 26px; letter-spacing: 6px; color:#7a1f3d; } .band .b { font-size: 12px; letter-spacing: 3px; }
    table.hf { width: 100%; margin-top: 12px; } table.hf th { font-size: 11px; color:#7a1f3d; border-bottom: 1px solid #7a1f3d; padding: 5px; font-weight: normal; letter-spacing: 1px; }
    table.hf td { padding: 7px 5px; border-bottom: 1px solid #ddd; } table.hf td.c { text-align:center; width: 88px; font-size: 12.5px; }
    .qrow { margin: 12px 0; } .note { font-size: 11px; font-style: italic; color:#555; } .qt { font-weight: 700; }
    """
    b = ['<div class="band"><div class="a">HARBOR POINT</div><div class="b">HOTEL &amp; SUITES · GUEST QUESTIONNAIRE</div></div>']
    b.append(f'<div style="margin-top:12px">{f.field("Room number:", str(f.rng.randint(101, 940)), 70)} &nbsp; {f.field("Departure date:", f.date(), 110)} &nbsp; {f.field("Name (optional):", None, 130)}</div>')
    b.append(f.inline("Purpose of stay:", ["Business", "Leisure", "Conference", "Wedding / event"], gap=14))
    scale = ["Excellent", "Good", "Fair", "Poor"]
    items = ["Reservation process", "Check-in speed", "Friendliness of front desk", "Room cleanliness", "Bed comfort",
             "Bathroom", "Noise level", "Wi-Fi", "Restaurant & bar", "Breakfast", "Fitness center", "Value for the price"]
    rows = ["<tr><th style='text-align:left'>Please circle one for each</th>" + "".join(f"<th>{s.upper()}</th>" for s in scale) + "</tr>"]
    for it in items:
        qid = f.reg(it, scale)
        rows.append(f'<tr data-qid="{qid}"><td>{it}</td>' + "".join(f'<td class="c">{f.o(qid, s)}</td>' for s in scale) + "</tr>")
    b.append('<table class="hf">' + "".join(rows) + "</table>")
    b.append(f.inline("Would you recommend Harbor Point to a friend?", ["Yes", "No", "Maybe"], gap=20))
    b.append(f.inline("Is this your first stay with us?", ["Yes", "No"], gap=20))
    b.append(f.inline("How did you book?", ["Our website", "Phone", "Travel agent", "Booking site", "Company travel"], gap=10))
    b.append(f.inline("Would you stay with us again?", ["Definitely", "Probably", "Not likely"], gap=16))
    b.append('<div style="margin-top:12px">Did a member of our team make your stay special? Please tell us who and why:</div>'
             + '<div style="border-bottom:1px solid #bbb;height:28px"></div>' * 3)
    b.append('<div style="margin-top:12px">Additional comments:</div>' + '<div style="border-bottom:1px solid #bbb;height:28px"></div>' * 3)
    return page(css, "".join(b), "Leave at the front desk or in your room", "HP-GQ-09")


# =============================================================================
# 14. Wellbeing check-in (frequency table with long column headers)
# =============================================================================
def wellbeing_checkin(f):
    css = """
    .page { font-family: 'Source Serif 4', Georgia, serif; font-size: 12.5px; }
    .h { border-bottom: 2px solid #3d5a40; padding-bottom: 6px; } .h .a { font-size: 19px; font-weight: 700; color:#3d5a40; }
    .ins { margin: 10px 0; }
    table.w { width: 100%; } table.w th { font-size: 10.5px; padding: 6px 3px; border: 1px solid #777; background:#eef3ee; width: 92px; }
    table.w td { border: 1px solid #777; padding: 8px 6px; } table.w td.c { text-align:center; font-size: 14px; }
    .qrow { margin: 12px 0; } .note { font-size: 10.5px; font-style: italic; } .qt { font-weight: 700; }
    """
    b = [f'<div class="h"><div class="a">Student Wellbeing Check-In</div><div class="small">Westbrook University Counseling Center · {f.field("Date:", f.date(), 100)}</div></div>']
    b.append('<div class="ins">Over the <b>last two weeks</b>, how often have you experienced the following? Circle the number in one column for each row.</div>')
    cols = [("Not at all", "0"), ("On a few days", "1"), ("On more than half the days", "2"), ("Almost every day", "3")]
    items = ["Difficulty falling or staying asleep", "Feeling low on energy", "Trouble concentrating on coursework",
             "Feeling worried or on edge", "Losing interest in things I usually enjoy", "Changes in appetite",
             "Feeling overwhelmed by responsibilities", "Avoiding friends or social activities", "Feeling hopeful about the future"]
    rows = ["<tr><th style='width:auto;text-align:left'>Item</th>" + "".join(f"<th>{c}</th>" for c, _ in cols) + "</tr>"]
    for i, it in enumerate(items, 1):
        qid = f.reg(it, [n for _, n in cols])
        rows.append(f'<tr data-qid="{qid}"><td>{i}. {it}</td>' + "".join(f'<td class="c">{f.o(qid, n)}</td>' for _, n in cols) + "</tr>")
    b.append('<table class="w">' + "".join(rows) + "</table>")
    b.append(f.inline("Year of study:", ["First", "Second", "Third", "Fourth", "Graduate"], gap=12))
    b.append(f.inline("Do you live:", ["On campus", "Off campus with others", "Off campus alone", "With family"], gap=10))
    b.append(f.inline("Have you used counseling services before?", ["Yes", "No"], gap=16))
    qid = f.reg("Overall stress level this week", [str(n) for n in range(1, 11)])
    b.append(f'<div class="qrow" data-qid="{qid}"><span class="qt">Overall stress level this week:</span> <span class="note">(1 = very low, 10 = very high)</span>'
             f'<div style="display:flex;justify-content:space-between;width:560px;margin:6px 0 0 20px;font-size:14px">'
             + "".join(f.o(qid, str(n)) for n in range(1, 11)) + "</div></div>")
    b.append(f.inline("Would you like a counselor to contact you?", ["Yes", "No", "Not sure"], gap=16))
    b.append(f.inline("Preferred contact:", ["Email", "Phone call", "Text"], gap=16))
    b.append(f.inline("Best time to reach you:", ["Morning", "Afternoon", "Evening"], gap=16))
    b.append(f'<div style="margin-top:8px">{f.field("Name:", f.name(), 220)} &nbsp; {f.field("Student ID:", None, 120)}</div>')
    b.append('<div class="small" style="margin-top:16px">If you are in crisis, please go to the front desk right away or call the 24-hour support line printed on the back of your student ID.</div>')
    return page(css, "".join(b), "WUCC-WB-2", "Confidential")


TEMPLATES = [patient_intake, comment_card, pain_assessment, employee_survey, course_evaluation, science_quiz,
             race_registration, vintage_product_test, health_screening, vehicle_inspection, rental_application,
             student_survey, hotel_feedback, wellbeing_checkin]
