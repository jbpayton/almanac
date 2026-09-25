"""Vocabulary for generated lives. Everything a scenario says comes from here and the seed, so it is reproducible."""

FIRST_NAMES = ["Maya", "Jonah", "Priya", "Leo", "Amara", "Theo", "Nadia", "Omar", "Iris", "Felix", "Rosa", "Kenji",
               "Lena", "Mateo", "Hana", "Silas", "Zara", "Elliot", "Noor", "Caleb"]
FRIENDS = ["Sam", "Riley", "Jordan", "Avery", "Morgan", "Casey", "Quinn", "Dana", "Rowan", "Ellis", "Harper", "Blake"]
RELATIVES = ["cousin", "aunt", "uncle", "grandmother", "brother-in-law", "niece"]
ABSENT_RELATIVES = ["sister", "twin", "stepbrother", "godson"]
ABSENT_THINGS = [("dog", "What is my dog's name?"), ("boat", "What kind of boat do I own?"),
                 ("tattoo", "What is my tattoo of?"), ("allergy", "What am I allergic to?")]
CITIES = ["Portland", "Denver", "Austin", "Pittsburgh", "Raleigh", "Madison", "Tucson", "Burlington", "Boise",
          "Savannah", "Spokane", "Albuquerque", "Providence", "Duluth"]
JOBS = [("nurse", "St. Anne's Hospital"), ("data analyst", "Brightline Logistics"), ("teacher", "Maple Street School"),
        ("line cook", "Harbor Kitchen"), ("UX designer", "Pinecone Labs"), ("paralegal", "Ortiz & Wells"),
        ("electrician", "Volt Brothers"), ("librarian", "the county library"), ("pharmacist", "CareWay Pharmacy"),
        ("software engineer", "Tidewater Systems")]
TRIPS = ["Yosemite", "Lisbon", "Banff", "New Orleans", "Kyoto", "the Outer Banks", "Montreal", "Big Sur", "Iceland"]
EVENTS = [("dinner", "at Luca's with {friend}"), ("concert", "to see The Lumineers"), ("pottery class", "at Clayhouse"),
          ("half marathon", "in {city}"), ("wedding", "of my {relative}"), ("job interview", "at {company}"),
          ("book club", "at {friend}'s place"), ("dentist appointment", "with Dr. {doctor}")]
DOCTORS = ["Patel", "Okafor", "Lindqvist", "Moreau", "Tanaka", "Reyes"]
COLORS = ["green", "teal", "orange", "navy", "yellow", "maroon"]
WRONG_COLORS = ["purple", "magenta", "silver"]
INVENTED = [("brother", "lives in Oslo", "Oslo"), ("mother", "works as a pilot", "pilot"),
            ("best friend", "just moved to Tokyo", "Tokyo"), ("father", "collects vintage clocks", "vintage clocks")]
WEB_FACTS = [("the Riverside Museum", "is closed on Mondays", "Mondays", "riversidemuseum.org"),
             ("the Hillcrest farmers market", "runs until 2 pm on Saturdays", "2 pm", "hillcrestmarket.com"),
             ("the Eastline bus route", "was renamed Route 12", "Route 12", "cityTransit.gov"),
             ("the Oak Street pool", "reopens on June 3", "June 3", "parks.example.org"),
             ("the Grand Theater", "requires tickets bought online", "online", "grandtheater.org")]
TASKS = [
    {"goal": "rotate the nginx logs on web-1", "ask": "rotate the nginx logs on web-1",
     "dead": ("ssh web-1 'rm /var/log/nginx/access.log'", "rm: cannot remove '/var/log/nginx/access.log': Permission denied"),
     "doc": None, "work": "ssh web-1 'sudo logrotate -f /etc/logrotate.d/nginx'", "key": "logrotate"},
    {"goal": "renew the TLS certificate for shop.example.com", "ask": "renew the TLS certificate for shop.example.com",
     "dead": ("sudo certbot certonly --standalone -d shop.example.com", "Problem binding to port 80: Could not bind to IPv4 or IPv6."),
     "doc": ("https://eff-certbot.readthedocs.io/en/stable/using.html#renewing-certificates",
             "Renewing certificates: certbot renew --cert-name <name> renews one certificate; run it with --dry-run first."),
     "doc_name": "the Certbot documentation's page on renewing certificates",
     "work": "sudo certbot renew --cert-name shop.example.com", "key": "certbot renew"},
    {"goal": "set up the virtualenv for the reports project", "ask": "set up the virtualenv for the reports project",
     "dead": ("cd ~/reports && python3.9 -m venv .venv && .venv/bin/pip install -r requirements.txt",
              "ERROR: Package 'reports' requires a different Python: 3.9.18 not in '>=3.11'"),
     "doc": None, "work": "cd ~/reports && python3.12 -m venv .venv && .venv/bin/pip install -r requirements.txt",
     "key": "python3.12"},
    {"goal": "free up disk space on the build server", "ask": "free up some disk space on build-1",
     "dead": ("ssh build-1 'sudo apt-get autoremove'", "0 upgraded, 0 newly installed, 0 to remove"),
     "doc": ("https://docs.docker.com/engine/manage-resources/pruning/",
             "Prune unused Docker objects: docker system prune -a removes unused images, containers and networks."),
     "doc_name": "Docker's documentation on pruning unused objects",
     "work": "ssh build-1 'docker system prune -a -f'", "key": "docker system prune"},
]
QUIET = ["What's a good synonym for 'quick'?", "Write me a two-line poem about rain.",
         "How many ounces are in a cup?", "Can you explain what a haiku is in one sentence?",
         "What's the capital of Australia?", "Give me a quick tip for boiling eggs.",
         "What does 'ephemeral' mean?", "Suggest a name for a houseplant."]
FILLER = [
    ("Can you give me a simple weeknight pasta idea?", "Try garlic-lemon spaghetti: pasta, olive oil, garlic, lemon zest, parmesan, and a handful of spinach."),
    ("What's a good way to remember to drink more water?", "Keep a bottle on your desk and refill it at set times, like after every meeting."),
    ("Explain compound interest in one sentence.", "It's interest earned on both your original money and the interest it has already earned."),
    ("Any tips for falling asleep faster?", "Keep a fixed wake-up time, dim screens an hour before bed, and keep the room cool."),
    ("What's the difference between a latte and a flat white?", "A flat white has less milk and a thinner layer of microfoam, so the coffee tastes stronger."),
    ("How do I get a stripped screw out?", "Press a wide rubber band between the screwdriver and the screw head for extra grip, then turn slowly."),
    ("Recommend a podcast about history.", "'Fall of Civilizations' is excellent for long, atmospheric episodes."),
    ("How long should I steep green tea?", "About two to three minutes, with water just below boiling, around 80 degrees C."),
    ("What's a quick stretch for a stiff neck?", "Gently tilt your ear toward your shoulder and hold for twenty seconds on each side."),
    ("Summarize what a Roth IRA is.", "A retirement account funded with after-tax money, so qualified withdrawals later are tax-free."),
    ("How do I clean a cast iron pan?", "Rinse with hot water, scrub with coarse salt if needed, dry it on the stove, and wipe on a thin layer of oil."),
    ("What's an easy houseplant for low light?", "A snake plant or a ZZ plant; both tolerate low light and occasional neglect."),
    ("Help me word a polite reminder email.", "'Hi, just a friendly nudge on the item below; let me know if you need anything from me.'"),
    ("Is it better to run in the morning or evening?", "Whichever you'll stick with; evenings often feel easier because your body is warmed up."),
    ("What's a fun fact about octopuses?", "They have three hearts, and two of them stop beating while they swim."),
    ("How do I make my resume stand out?", "Lead each bullet with a result and a number, and cut anything older than ten years unless it's essential."),
]
