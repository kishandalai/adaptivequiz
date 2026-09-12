"""Curated Technical Languages learning content used by the notes UI."""

from copy import deepcopy

LANGUAGE_DEFINITIONS = [
    {
        "slug": "c",
        "name": "C",
        "icon": "C",
        "description": "Build a strong foundation in procedural programming, memory, and systems thinking.",
        "topics": ["Introduction", "Variables & Data Types", "Operators", "Input/Output", "Conditions", "Loops", "Arrays", "Strings", "Functions", "Pointers", "Structures", "Unions", "Memory Management", "File Handling", "Important Interview Concepts"],
    },
    {
        "slug": "cpp",
        "name": "C++",
        "icon": "C+",
        "description": "Learn modern C++ from language basics through object-oriented design and the STL.",
        "topics": ["Basics", "Variables & Data Types", "Operators", "Conditions", "Loops", "Arrays", "Strings", "Functions", "Pointers & References", "OOP", "Classes & Objects", "Constructors & Destructors", "Inheritance", "Polymorphism", "Encapsulation", "Abstraction", "STL", "Exception Handling", "Interview Concepts"],
    },
    {
        "slug": "java",
        "name": "Java",
        "icon": "J",
        "description": "Study Java fundamentals, object-oriented programming, collections, and runtime concepts.",
        "topics": ["Java Basics", "Variables & Data Types", "Operators", "Conditions", "Loops", "Arrays", "Strings", "Methods", "Classes & Objects", "Constructors", "Inheritance", "Polymorphism", "Encapsulation", "Abstraction", "Interfaces", "Collections", "Exception Handling", "Multithreading Basics", "JVM/JDK/JRE", "Interview Concepts"],
    },
    {
        "slug": "python",
        "name": "Python",
        "icon": "Py",
        "description": "Learn Python from fundamentals to interview preparation with practical, readable examples.",
        "topics": ["Python Basics", "Variables & Data Types", "Operators", "Conditions", "Loops", "Strings", "Lists", "Tuples", "Sets", "Dictionaries", "Functions", "Modules", "Exception Handling", "File Handling", "OOP", "Inheritance", "Polymorphism", "Lambda", "List Comprehension", "Interview Concepts"],
    },
    {
        "slug": "javascript",
        "name": "JavaScript",
        "icon": "JS",
        "description": "Master the language of the web, from core syntax to asynchronous browser applications.",
        "topics": ["JavaScript Basics", "Variables", "Data Types", "Operators", "Conditions", "Loops", "Functions", "Arrays", "Objects", "Strings", "DOM", "Events", "ES6 Features", "Arrow Functions", "Promises", "Async/Await", "JSON", "Local Storage", "Interview Concepts"],
    },
    {
        "slug": "sql",
        "name": "SQL",
        "icon": "SQL",
        "description": "Query, shape, and reason about relational data with practical database patterns.",
        "topics": ["SQL Introduction", "Database Basics", "CREATE", "INSERT", "SELECT", "WHERE", "DISTINCT", "ORDER BY", "UPDATE", "DELETE", "ALTER", "Constraints", "Aggregate Functions", "GROUP BY", "HAVING", "Joins", "Subqueries", "CASE", "String Functions", "Date Functions", "Views", "Indexes", "Transactions", "PostgreSQL-specific concepts", "Interview Questions"],
    },
    {
        "slug": "html",
        "name": "HTML",
        "icon": "<>...",
        "description": "Create accessible, semantic document structures that form the foundation of the web.",
        "topics": ["HTML Basics", "Document Structure", "Headings", "Paragraphs", "Links", "Images", "Lists", "Tables", "Forms", "Input Elements", "Semantic HTML", "HTML5", "Accessibility", "Interview Concepts"],
    },
    {
        "slug": "css",
        "name": "CSS",
        "icon": "#",
        "description": "Design resilient interfaces with selectors, layout systems, responsive rules, and motion.",
        "topics": ["CSS Basics", "Selectors", "Colors", "Units", "Box Model", "Display", "Position", "Flexbox", "Grid", "Responsive Design", "Media Queries", "Transitions", "Animations", "Pseudo Classes", "Pseudo Elements", "Interview Concepts"],
    },
    {
        "slug": "git-github",
        "name": "Git & GitHub",
        "icon": "git",
        "description": "Build confident version-control habits for individual work and collaborative projects.",
        "topics": ["What is Git?", "Git vs GitHub", "Installation", "git config", "git init", "git status", "git add", "git commit", "git log", "git clone", "git push", "git pull", "git fetch", "Branches", "Merge", "Merge Conflicts", "git restore", "git reset", "git revert", "git stash", ".gitignore", "Pull Requests", "GitHub Repository", "Real Project Workflow", "Interview Questions"],
    },
]

LANGUAGES = {item["slug"]: item for item in LANGUAGE_DEFINITIONS}


def get_languages():
    """Return built-in notes with administrator overrides applied."""
    languages = {item["slug"]: deepcopy(item) for item in LANGUAGE_DEFINITIONS}
    from .models import TechnicalNote

    for stored in TechnicalNote.objects.all():
        language = languages.setdefault(
            stored.language_slug,
            {
                "slug": stored.language_slug,
                "name": stored.language_name,
                "icon": stored.language_name[:2],
                "description": f"Technical notes for {stored.language_name}.",
                "topics": [],
                "notes": {},
            },
        )
        if stored.topic not in language["topics"]:
            language["topics"].append(stored.topic)
        language["notes"][stored.topic] = stored.content
    return languages

LANGUAGE_CONTEXT = {
    "C": ("printf(\"%d\\n\", value);", "int value = 42;", "C gives direct control over memory and is used for operating systems, embedded software, and performance-critical code."),
    "C++": ("std::cout << value << '\\n';", "int value = 42;", "C++ combines low-level control with classes, templates, and the standard library."),
    "Java": ("System.out.println(value);", "int value = 42;", "Java runs on the JVM, providing portability, automatic memory management, and a large standard library."),
    "Python": ("print(value)", "value = 42", "Python favors readable syntax and is used for automation, web services, data work, and interviews."),
    "JavaScript": ("console.log(value);", "const value = 42;", "JavaScript runs in browsers and servers; its event loop makes asynchronous programming important."),
    "SQL": ("SELECT column_name FROM table_name;", "SELECT 42 AS answer;", "SQL is declarative: you describe the result and the database chooses an execution plan."),
    "HTML": ("<p>Content</p>", "<main><h1>Study notes</h1></main>", "HTML describes the structure and meaning of web content through a document tree."),
    "CSS": ("selector { property: value; }", "body { color: #172033; }", "CSS controls presentation and layout through selectors, the cascade, inheritance, and the box model."),
    "Git & GitHub": ("git command [options]", "git status", "Git records project snapshots locally, while GitHub hosts repositories and collaboration workflows."),
}


def _code_examples(language, topic):
    if language == "Python":
        return [("Basic", "numbers = [2, 4, 6]\nprint(sum(numbers))", "The list is passed to the built-in sum function.", "12"), ("Practical", "scores = [72, 91, 84]\naverage = sum(scores) / len(scores)\nprint(round(average, 1))", "The calculation combines a collection, aggregation, and formatted output.", "82.3"), ("Interview problem", "def first_repeated(values):\n    seen = set()\n    for value in values:\n        if value in seen:\n            return value\n        seen.add(value)\n    return None\n\nprint(first_repeated([4, 7, 4, 9]))", "A set provides average constant-time membership checks, so the scan is O(n).", "4")]
    if language == "JavaScript":
        return [("Basic", "const numbers = [2, 4, 6];\nconsole.log(numbers.reduce((a, b) => a + b, 0));", "reduce combines the values into one result.", "12"), ("Practical", "const user = { name: 'Mina', active: true };\nconsole.log(`${user.name}: ${user.active}`);", "A template literal reads object properties and builds a string.", "Mina: true"), ("Interview problem", "function firstRepeated(values) {\n  const seen = new Set();\n  for (const value of values) {\n    if (seen.has(value)) return value;\n    seen.add(value);\n  }\n  return null;\n}\nconsole.log(firstRepeated([4, 7, 4]));", "Set membership keeps the one-pass solution at O(n) average time.", "4")]
    if language == "SQL":
        return [("Basic", "SELECT name, salary\nFROM employees\nWHERE salary > 50000;", "WHERE filters rows before they are returned.", "Employees earning more than 50000"), ("Practical", "SELECT department_id, COUNT(*) AS headcount\nFROM employees\nGROUP BY department_id\nHAVING COUNT(*) >= 3;", "GROUP BY creates one group per department and HAVING filters groups.", "Departments with at least 3 employees"), ("Interview problem", "SELECT e.name, d.name AS department\nFROM employees AS e\nJOIN departments AS d ON d.id = e.department_id;", "The join matches rows using the declared key relationship.", "Each employee with its department")]
    if language == "HTML":
        return [("Basic", "<h1>Course notes</h1>\n<p>Revise one concept today.</p>", "A heading gives the page a title and a paragraph gives it readable content.", "A page with a heading and paragraph"), ("Practical", "<article>\n  <h2>Functions</h2>\n  <p>Reusable blocks of logic.</p>\n  <a href=\"/practice\">Practice</a>\n</article>", "article groups a self-contained item and the link gives it an action.", "A semantic study card"), ("Interview problem", "<form action=\"/search\" method=\"get\">\n  <label for=\"q\">Search notes</label>\n  <input id=\"q\" name=\"q\" required>\n  <button>Search</button>\n</form>", "The label, name, and method make the form usable and submit meaningful data.", "A labelled search form")]
    if language == "CSS":
        return [("Basic", ".card {\n  padding: 1rem;\n  border: 1px solid #dbe3ee;\n}", "The rule selects cards and gives them space and a visible boundary.", "A padded bordered card"), ("Practical", ".cards {\n  display: grid;\n  grid-template-columns: repeat(3, 1fr);\n  gap: 1rem;\n}", "Grid creates three equal columns with a consistent gap.", "Three aligned columns"), ("Interview problem", "@media (max-width: 700px) {\n  .cards { grid-template-columns: 1fr; }\n}", "The media query changes the layout when the viewport is narrow.", "A single-column mobile layout")]
    if language == "Git & GitHub":
        return [("Basic", "git status\ngit add notes.md\ngit commit -m \"Add notes\"", "Status checks the working tree, add stages a file, and commit records a snapshot.", "A committed notes change"), ("Practical", "git switch -c feature/search\n# edit files\ngit add .\ngit commit -m \"Add note search\"\ngit push -u origin feature/search", "A feature branch isolates work before it is shared with the remote.", "A pushed feature branch"), ("Interview problem", "git fetch origin\ngit log --oneline main..origin/main\ngit merge origin/main", "Fetch updates remote-tracking refs without changing the working tree; inspect before merging.", "Local main includes reviewed remote changes")]
    if language in ("C", "C++", "Java"):
        basic = "int total = 2 + 3;\nprintf(\"%d\\n\", total);" if language == "C" else "int total = 2 + 3;\nSystem.out.println(total);" if language == "Java" else "int total = 2 + 3;\nstd::cout << total << '\\n';"
        practical = "int values[] = {2, 4, 6};\nint total = 0;\nfor (int i = 0; i < 3; i++) total += values[i];" if language != "Java" else "int[] values = {2, 4, 6};\nint total = 0;\nfor (int value : values) total += value;"
        output = "printf(\"even\\n\");\nelse printf(\"odd\\n\");" if language == "C" else "System.out.println(value % 2 == 0 ? \"even\" : \"odd\");" if language == "Java" else "std::cout << (value % 2 == 0 ? \"even\" : \"odd\") << '\\n';"
        interview_code = "int value = 17;\nif (value % 2 == 0) " + output
        return [("Basic", basic, "The program evaluates an expression and prints the result.", "5"), ("Practical", practical, "A loop visits each array element and accumulates a total.", "total becomes 12"), ("Interview problem", interview_code, "The remainder operator distinguishes even and odd integers.", "odd")]
    return [("Basic", LANGUAGE_CONTEXT[language][1], "This is the smallest working form of the idea.", "The statement executes without extra state."), ("Practical", LANGUAGE_CONTEXT[language][0], "This syntax is a useful starting point inside a real application.", "The requested value is produced."), ("Interview problem", LANGUAGE_CONTEXT[language][0], "Explain the inputs, operation, output, and the edge case before coding.", "A correct result for valid input.")]


def _make_note(language, topic, index):
    syntax, starter, context = LANGUAGE_CONTEXT[language]
    lower_topic = topic.lower()
    examples = _code_examples(language, topic)
    if language == "SQL" and lower_topic == "joins":
        core = ["A join combines rows from two or more tables using a related column.", "INNER JOIN keeps only matching rows; LEFT JOIN keeps every left row and fills missing right values with NULL.", "RIGHT JOIN is the mirror of LEFT JOIN, FULL JOIN keeps unmatched rows from both sides, and CROSS JOIN produces every pair.", "A self join joins a table to itself, useful for manager relationships or comparing rows.", "Always state the relationship in ON, qualify same-named columns, and inspect whether duplicate keys multiply rows."]
    elif language in ("C++", "Java", "Python") and lower_topic in ("oop", "classes & objects", "inheritance", "polymorphism", "encapsulation", "abstraction"):
        core = ["A class defines data and behavior; an object is a concrete instance with its own state.", "Constructors establish valid initial state, while methods define operations that protect or use that state.", "Encapsulation hides representation behind a small public interface.", "Inheritance reuses and specializes a base type, while polymorphism lets one interface work with multiple implementations.", "Prefer composition when a has-a relationship is clearer than an is-a relationship."]
    else:
        core = [f"{topic} solves a recurring problem in {language}: {context}", f"Start with the basic form, identify its inputs and output, then trace the state change one step at a time.", f"Next combine {topic} with nearby features such as conditions, collections, functions, or data validation.", "In production, choose names that reveal intent, handle invalid input, and test boundary cases.", f"Performance and readability matter together: know the usual time or space cost of the {topic} operation when it applies."]
    interview = [{"question": f"What is {topic} and why is it useful?", "answer": f"It is a {language} feature for solving a recurring programming problem. Explain its purpose first, then show a small example and its main trade-off."}, {"question": f"What is a common mistake when using {topic}?", "answer": "Using the syntax mechanically without checking input, output, and edge cases. Trace a small example and verify the assumptions."}, {"question": f"How would you use {topic} in a practical system?", "answer": "Define the data contract, use the simplest correct form, validate external data, and test normal and boundary cases."}, {"question": f"How is {topic} different from a nearby concept?", "answer": "Compare purpose, scope, lifetime, performance, and readability rather than only comparing syntax."}]
    if language == "SQL" and lower_topic == "joins":
        interview.append({"question": "Why can a join return more rows than either table?", "answer": "A one-to-many or many-to-many match creates one output row for every matching pair. Check key uniqueness and the intended result grain."})
    return {"overview": f"{topic} is a core {language} topic. {context} Students should learn it because it appears in coursework, technical interviews, and everyday code. It is used when a program needs to represent data, control behavior, or communicate with another system.", "core_concepts": core, "syntax": syntax, "examples": [{"title": title, "description": explanation, "code": code, "explanation": explanation, "output": output} for title, code, explanation, output in examples], "important": [f"Know the purpose and basic structure of {topic}.", "Be able to explain the input, output, and one edge case.", "Use clear names and keep the example small enough to test.", "Mention the relevant safety, performance, or maintainability trade-off in an interview."], "mistakes": [f"Memorizing {topic} syntax without tracing the value or state.", "Ignoring empty, missing, duplicate, or invalid input.", "Confusing a related feature because the names look similar.", "Writing a clever example that is harder to verify than a simple one."], "interview": interview, "exam_points": [f"Define {topic} and state its purpose.", "Write the basic structure and label its important parts.", "Explain one advantage, one limitation, and one practical use.", "Include a small example and its expected result."], "revision": f"{topic}: know what it represents, when to use it, its basic syntax, one practical example, one edge case, and its main interview trade-off.", "practice": [f"Easy: write a small {language} example that demonstrates {topic}.", f"Medium: change the input, predict the output, and explain the boundary case.", f"Hard: design a small interview-style solution using {topic}; state its complexity and testing plan."], "index": index}


for language in LANGUAGE_DEFINITIONS:
    language["notes"] = {topic: _make_note(language["name"], topic, index) for index, topic in enumerate(language["topics"])}


def all_search_items():
    for language in get_languages().values():
        yield {"type": "language", "language": language, "title": language["name"], "description": language["description"]}
        for topic_index, topic in enumerate(language["topics"]):
            note = language["notes"][topic]
            searchable = " ".join([note["overview"], *note["core_concepts"], *note["important"]])
            yield {"type": "topic", "language": language, "title": topic, "topic_index": topic_index, "description": note["overview"], "matching_section": searchable}