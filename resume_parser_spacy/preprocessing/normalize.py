import re

ONTOLOGY = {
    "programming_languages": {
        "Python": (["python3", "python 3", "py"], ["Backend", "Data Science"]),
        "Java": (["java 8", "java se", "core java"], ["Backend", "JVM"]),
        "JavaScript": (["js", "java script", "ecmascript", "es6"], ["Frontend", "JavaScript Ecosystem"]),
        "TypeScript": (["ts"], ["Frontend", "JavaScript Ecosystem"]),
        "C": ([], ["Systems Programming"]),
        "C++": (["cpp", "c plus plus"], ["Systems Programming"]),
        "C#": (["c sharp", "csharp"], ["Backend", ".NET Ecosystem"]),
        "Go": (["golang"], ["Backend"]),
        "Rust": ([], ["Systems Programming"]),
        "Kotlin": ([], ["Mobile", "JVM"]),
        "Swift": ([], ["Mobile", "Apple Ecosystem"]),
        "Objective-C": (["objective c"], ["Mobile", "Apple Ecosystem"]),
        "Dart": ([], ["Mobile"]),
        "PHP": ([], ["Backend", "Web"]),
        "Ruby": ([], ["Backend"]),
        "Scala": ([], ["JVM", "Big Data"]),
        "R": ([], ["Data Science"]),
        "MATLAB": ([], ["Scientific Computing"]),
        "SQL": (["t-sql", "tsql", "pl/sql", "plsql", "sql queries"], ["Database"]),
        "Bash": (["shell scripting", "shell script", "unix shell scripts", "shell"], ["Scripting"]),
        "PowerShell": (["power shell"], ["Scripting", "Windows"]),
        "Perl": ([], ["Scripting"]),
        "HTML": (["html5", "xhtml"], ["Frontend", "Web"]),
        "CSS": (["css3"], ["Frontend", "Web"]),
        "Verilog": ([], ["Hardware Design"]),
        "VHDL": ([], ["Hardware Design"]),
        "Solidity": ([], ["Blockchain"]),
        "Assembly": (["asm"], ["Systems Programming"]),
        "VBA": ([], ["Scripting", "Office Automation"]),
    },
    "frameworks": {
        "React": (["reactjs", "react js", "react.js"], ["Frontend", "JavaScript Ecosystem"]),
        "React Native": (["react-native"], ["Mobile", "JavaScript Ecosystem"]),
        "Angular": (["angularjs", "angular js", "angular.js"], ["Frontend", "JavaScript Ecosystem"]),
        "Vue.js": (["vue", "vuejs", "vue js"], ["Frontend", "JavaScript Ecosystem"]),
        "Next.js": (["nextjs", "next js"], ["Frontend", "JavaScript Ecosystem"]),
        "Svelte": ([], ["Frontend", "JavaScript Ecosystem"]),
        "Node.js": (["node", "nodejs", "node js"], ["Backend", "JavaScript Ecosystem"]),
        "Express": (["expressjs", "express.js", "express js"], ["Backend", "JavaScript Ecosystem"]),
        "NestJS": (["nest.js", "nest js"], ["Backend", "JavaScript Ecosystem"]),
        "Django": ([], ["Backend", "Python Ecosystem"]),
        "Flask": ([], ["Backend", "Python Ecosystem"]),
        "FastAPI": (["fast api"], ["Backend", "Python Ecosystem"]),
        "Spring": (["spring framework"], ["Backend", "JVM"]),
        "Spring Boot": (["springboot"], ["Backend", "JVM"]),
        "Hibernate": ([], ["Backend", "JVM"]),
        "ASP.NET": (["asp net", "asp.net mvc", "asp.net core"], ["Backend", ".NET Ecosystem"]),
        ".NET": (["dotnet", "dot net", ".net core", "net core", ".net framework"], ["Backend", ".NET Ecosystem"]),
        "Laravel": ([], ["Backend", "Web"]),
        "Ruby on Rails": (["rails", "ror"], ["Backend", "Web"]),
        "Flutter": ([], ["Mobile"]),
        "Bootstrap": ([], ["Frontend", "Web"]),
        "Tailwind CSS": (["tailwind", "tailwindcss"], ["Frontend", "Web"]),
        "jQuery": (["jquery"], ["Frontend", "JavaScript Ecosystem"]),
        "Redux": ([], ["Frontend", "JavaScript Ecosystem"]),
        "GraphQL": ([], ["API"]),
        "REST API": (["rest", "restful", "restful api", "rest apis", "restful apis", "rest api"], ["API"]),
        "LangChain": ([], ["LLM", "Python Ecosystem"]),
        "Hadoop": (["apache hadoop"], ["Big Data"]),
        "Spark": (["apache spark", "pyspark"], ["Big Data"]),
        "Qt": ([], ["Desktop"]),
    },
    "libraries": {
        "NumPy": (["numpy"], ["Data Science", "Python Ecosystem"]),
        "Pandas": (["pandas"], ["Data Science", "Python Ecosystem"]),
        "Matplotlib": ([], ["Data Visualization", "Python Ecosystem"]),
        "Seaborn": ([], ["Data Visualization", "Python Ecosystem"]),
        "Plotly": ([], ["Data Visualization"]),
        "scikit-learn": (["sklearn", "scikit learn", "scikit"], ["Machine Learning", "Python Ecosystem"]),
        "TensorFlow": (["tensor flow", "tf"], ["Deep Learning"]),
        "Keras": ([], ["Deep Learning"]),
        "PyTorch": (["torch", "py torch"], ["Deep Learning"]),
        "Hugging Face Transformers": (["huggingface", "hugging face", "transformers"], ["NLP", "Deep Learning"]),
        "spaCy": (["spacy"], ["NLP", "Python Ecosystem"]),
        "NLTK": ([], ["NLP", "Python Ecosystem"]),
        "OpenCV": (["open cv", "cv2"], ["Computer Vision"]),
        "XGBoost": ([], ["Machine Learning"]),
        "LightGBM": ([], ["Machine Learning"]),
        "SciPy": ([], ["Scientific Computing", "Python Ecosystem"]),
        "D3.js": (["d3", "d3js"], ["Data Visualization", "JavaScript Ecosystem"]),
        "Selenium": ([], ["Testing", "Automation"]),
        "JUnit": ([], ["Testing", "JVM"]),
        "pytest": ([], ["Testing", "Python Ecosystem"]),
        "Jest": ([], ["Testing", "JavaScript Ecosystem"]),
        "AJAX": ([], ["Frontend", "Web"]),
    },
    "databases": {
        "PostgreSQL": (["postgres", "postgre sql", "postgresql", "psql"], ["Database", "Relational Database"]),
        "MySQL": (["my sql"], ["Database", "Relational Database"]),
        "SQLite": ([], ["Database", "Relational Database"]),
        "Microsoft SQL Server": (["sql server", "mssql", "ms sql", "ms sql server", "microsoft sql"], ["Database", "Relational Database"]),
        "Oracle Database": (["oracle", "oracle db", "oracle sql"], ["Database", "Relational Database"]),
        "MongoDB": (["mongo", "mongo db"], ["Database", "NoSQL"]),
        "Redis": ([], ["Database", "NoSQL", "Cache"]),
        "Cassandra": (["apache cassandra"], ["Database", "NoSQL"]),
        "HBase": (["apache hbase"], ["Database", "NoSQL", "Big Data"]),
        "Couchbase": ([], ["Database", "NoSQL"]),
        "DynamoDB": (["dynamo db", "amazon dynamodb"], ["Database", "NoSQL", "AWS"]),
        "Elasticsearch": (["elastic search", "elk"], ["Database", "Search"]),
        "Firebase": (["firestore"], ["Database", "Backend as a Service"]),
        "Supabase": ([], ["Database", "Backend as a Service"]),
        "Neo4j": ([], ["Database", "Graph Database"]),
        "Snowflake": ([], ["Database", "Data Warehouse"]),
        "BigQuery": (["google bigquery"], ["Database", "Data Warehouse", "GCP"]),
        "Microsoft Access": (["ms access"], ["Database"]),
        "FAISS": ([], ["Vector Database"]),
        "Pinecone": ([], ["Vector Database"]),
    },
    "cloud": {
        "AWS": (["amazon web services", "aws cloud", "amazon aws"], ["Cloud", "Infrastructure"]),
        "Azure": (["microsoft azure", "azure cloud"], ["Cloud", "Infrastructure"]),
        "GCP": (["google cloud platform", "google cloud", "gcp cloud"], ["Cloud", "Infrastructure"]),
        "AWS Lambda": (["lambda"], ["Cloud", "Serverless", "AWS"]),
        "Amazon EC2": (["ec2", "aws ec2"], ["Cloud", "Compute", "AWS"]),
        "Amazon S3": (["s3", "aws s3"], ["Cloud", "Storage", "AWS"]),
        "Heroku": ([], ["Cloud", "PaaS"]),
        "Vercel": ([], ["Cloud", "PaaS"]),
        "DigitalOcean": (["digital ocean"], ["Cloud", "Infrastructure"]),
        "Databricks": ([], ["Cloud", "Big Data"]),
        "SharePoint": (["share point", "sharepoint online"], ["Cloud", "Microsoft Ecosystem"]),
        "Salesforce": (["sfdc"], ["Cloud", "CRM"]),
    },
    "devops_infrastructure": {
        "Docker": (["docker compose", "docker-compose"], ["DevOps", "Containers"]),
        "Kubernetes": (["k8s", "kubernetes cluster"], ["DevOps", "Containers", "Orchestration"]),
        "Jenkins": ([], ["DevOps", "CI/CD"]),
        "GitHub Actions": (["github action"], ["DevOps", "CI/CD"]),
        "GitLab CI": (["gitlab ci/cd", "gitlab-ci"], ["DevOps", "CI/CD"]),
        "TeamCity": (["team city"], ["DevOps", "CI/CD"]),
        "CI/CD": (["ci cd", "cicd", "continuous integration"], ["DevOps"]),
        "Terraform": ([], ["DevOps", "Infrastructure as Code"]),
        "Ansible": ([], ["DevOps", "Configuration Management"]),
        "Linux": (["ubuntu", "unix", "red hat", "centos", "debian"], ["Operating System", "Infrastructure"]),
        "Windows Server": ([], ["Operating System", "Infrastructure"]),
        "Nginx": ([], ["Web Server", "Infrastructure"]),
        "Apache HTTP Server": (["apache server", "apache web server"], ["Web Server", "Infrastructure"]),
        "IIS": (["internet information services"], ["Web Server", "Windows"]),
        "Airflow": (["apache airflow"], ["Data Engineering", "Orchestration"]),
        "Kafka": (["apache kafka"], ["Data Engineering", "Messaging"]),
        "RabbitMQ": ([], ["Messaging"]),
        "Prometheus": ([], ["Monitoring"]),
        "Grafana": ([], ["Monitoring"]),
        "TCP/IP": (["tcp ip"], ["Networking"]),
        "VPN": ([], ["Networking", "Security"]),
        "LAN/WAN": (["lan", "wan", "lan wan"], ["Networking"]),
        "Active Directory": ([], ["Networking", "Windows"]),
        "Cisco": (["cisco routers"], ["Networking"]),
        "MLflow": ([], ["MLOps"]),
    },
    "tools": {
        "Git": ([], ["Version Control"]),
        "GitHub": (["git hub"], ["Version Control"]),
        "GitLab": ([], ["Version Control"]),
        "Bitbucket": ([], ["Version Control"]),
        "SVN": (["subversion"], ["Version Control"]),
        "Jira": (["atlassian jira"], ["Project Management"]),
        "Confluence": ([], ["Documentation"]),
        "Postman": ([], ["API", "Testing"]),
        "Microsoft Excel": (["excel", "ms excel", "advanced excel"], ["Office", "Data Analysis"]),
        "Microsoft Office": (["ms office", "office 365", "microsoft 365"], ["Office"]),
        "Power BI": (["powerbi", "power-bi"], ["Business Intelligence", "Data Visualization"]),
        "Tableau": ([], ["Business Intelligence", "Data Visualization"]),
        "Visual Studio Code": (["vscode", "vs code"], ["IDE"]),
        "Visual Studio": ([], ["IDE"]),
        "IntelliJ IDEA": (["intellij"], ["IDE"]),
        "Eclipse": ([], ["IDE"]),
        "Jupyter": (["jupyter notebook", "jupyter notebooks"], ["Data Science", "IDE"]),
        "Figma": ([], ["Design"]),
        "Adobe Photoshop": (["photoshop"], ["Design"]),
        "Adobe Illustrator": (["illustrator"], ["Design"]),
        "Adobe Premiere Pro": (["premiere pro"], ["Video Editing"]),
        "Canva": ([], ["Design"]),
        "AutoCAD": (["auto cad"], ["CAD"]),
        "SolidWorks": (["solid works"], ["CAD"]),
        "LTspice": ([], ["Electronics", "Simulation"]),
        "SAP": ([], ["ERP"]),
        "Wireshark": ([], ["Networking", "Security"]),
        "Arduino": ([], ["Embedded"]),
        "Microsoft PowerPoint": (["powerpoint", "ms powerpoint", "power point"], ["Office"]),
        "Microsoft Word": (["ms word"], ["Office"]),
        "Microsoft Outlook": (["outlook", "ms outlook"], ["Office"]),
        "Microsoft Project": (["ms project"], ["Project Management"]),
        "Microsoft Visio": (["visio", "ms visio"], ["Design", "Documentation"]),
        "Google Analytics": (["ga4"], ["Marketing", "Analytics"]),
        "Google Ads": (["adwords", "google adwords"], ["Marketing"]),
        "Google Workspace": (["g suite", "gsuite", "google docs", "google sheets"], ["Office"]),
        "HubSpot": ([], ["Marketing", "CRM"]),
        "CRM": (["crm systems", "crm software"], ["CRM"]),
        "SEO": (["search engine optimization"], ["Marketing"]),
        "QuickBooks": ([], ["Accounting"]),
        "Tally": (["tally erp"], ["Accounting"]),
        "Team Foundation Server": (["tfs", "azure devops server"], ["Version Control", "Project Management"]),
        "Trello": ([], ["Project Management"]),
        "Asana": ([], ["Project Management"]),
        "Wix": ([], ["Web"]),
        "WordPress": (["wordpress"], ["Web", "CMS"]),
        "Shopify": ([], ["E-commerce"]),
        "VMware": (["vmware vsphere", "vsphere", "esxi"], ["Virtualization", "Infrastructure"]),
        "Avid Media Composer": (["avid", "avid non-linear editing system", "avid media"], ["Video Editing"]),
        "Final Cut Pro": (["final cut"], ["Video Editing"]),
        "DaVinci Resolve": (["davinci"], ["Video Editing"]),
        "Adobe After Effects": (["after effects"], ["Video Editing", "Design"]),
        "Adobe Creative Suite": (["adobe cs5", "adobe cs6", "creative suite", "adobe creative cloud"], ["Design"]),
        "Hootsuite": (["hootsuite media"], ["Social Media"]),
        "Qt Designer": (["qt-designer"], ["Desktop", "Design"]),
        "Ngspice": (["ng spice", "spice"], ["Electronics", "Simulation"]),
        "Magic VLSI": (["magic"], ["Electronics", "VLSI"]),
        "Cadence Virtuoso": (["cadence", "virtuoso"], ["Electronics", "VLSI"]),
        "Xilinx Vivado": (["vivado", "xilinx"], ["Electronics", "FPGA"]),
        "QGIS": ([], ["GIS", "Data Visualization"]),
        "Google Colab": (["colab"], ["Data Science", "IDE"]),
        "Notion": ([], ["Productivity"]),
        "Slack": ([], ["Collaboration"]),
    },
    "other": {
        "Machine Learning": (["ml"], ["Artificial Intelligence"]),
        "Deep Learning": (["dl"], ["Artificial Intelligence"]),
        "Natural Language Processing": (["nlp"], ["Artificial Intelligence"]),
        "Computer Vision": (["cv"], ["Artificial Intelligence"]),
        "Large Language Models": (["llm", "llms"], ["Artificial Intelligence"]),
        "Retrieval-Augmented Generation": (["rag"], ["Artificial Intelligence", "LLM"]),
        "Data Analysis": (["data analytics"], ["Data Science"]),
        "Data Science": (["data sciences"], ["Data Science"]),
        "Microservices": (["micro services", "microservice"], ["Architecture"]),
        "XML": ([], ["Data Format"]),
        "JSON": ([], ["Data Format"]),
        "Agile": (["scrum", "agile methodology"], ["Methodology"]),
        "Data Structures and Algorithms": (["dsa", "data structures & algorithms", "data structures"], ["Computer Science"]),
        "Convolutional Neural Networks": (["cnn", "cnns"], ["Deep Learning"]),
        "Recurrent Neural Networks": (["rnn", "rnns", "lstm"], ["Deep Learning"]),
        "Hidden Markov Models": (["hmm", "hmms"], ["Machine Learning"]),
        "Boosting": (["adaboost", "gradient boosting"], ["Machine Learning"]),
        "CatBoost": ([], ["Machine Learning"]),
        "Signal Processing": (["dsp", "digital signal processing"], ["Electronics"]),
        "VLSI Design": (["vlsi"], ["Electronics", "Hardware Design"]),
        "Embedded Systems": (["microcontrollers", "embedded"], ["Electronics", "Embedded"]),
        "Internet of Things": (["iot"], ["Embedded"]),
        "Word Embeddings": (["word2vec"], ["NLP"]),
    },
    "non_technical": {
        "English": ([], ["Spoken Language"]), "French": ([], ["Spoken Language"]),
        "Arabic": ([], ["Spoken Language"]), "Hindi": ([], ["Spoken Language"]),
        "Spanish": ([], ["Spoken Language"]), "German": ([], ["Spoken Language"]),
        "Russian": ([], ["Spoken Language"]), "Hebrew": ([], ["Spoken Language"]),
        "Dutch": ([], ["Spoken Language"]), "Ukrainian": ([], ["Spoken Language"]),
        "Communication": (["communication skills", "excellent communication"], ["Soft Skill"]),
        "Teamwork": (["team work", "team player"], ["Soft Skill"]),
        "Leadership": (["team leadership"], ["Soft Skill"]),
        "Problem Solving": (["problem-solving"], ["Soft Skill"]),
        "Time Management": ([], ["Soft Skill"]),
        "Critical Thinking": ([], ["Soft Skill"]),
        "Creativity": (["creative thinking"], ["Soft Skill"]),
        "Collaboration": (["collaborative"], ["Soft Skill"]),
        "Adaptability": (["flexibility"], ["Soft Skill"]),
        "Attention to Detail": (["detail oriented", "detail-oriented"], ["Soft Skill"]),
        "Public Speaking": (["presentation skills"], ["Soft Skill"]),
        "Negotiation": ([], ["Soft Skill"]),
        "Project Management": ([], ["Soft Skill"]),
        "Interpersonal Skills": ([], ["Soft Skill"]),
        "Active Listening": ([], ["Soft Skill"]),
        "Empathy": ([], ["Soft Skill"]),
        "Kazakh": ([], ["Spoken Language"]), "Flemish": ([], ["Spoken Language"]),
        "Tamil": ([], ["Spoken Language"]), "Telugu": ([], ["Spoken Language"]),
    },
}

AMBIGUOUS = {"c", "r", "go", "dart", "swift", "rust", "spring", "express", "rest", "node",
             "shell", "excel", "oracle", "lambda", "s3", "ml", "dl", "cv", "ts", "tf", "py", "js",
             "lan", "wan", "rails", "ror", "unix", "scikit", "torch", "transformers", "mongo",
             "eclipse", "illustrator", "sap", "agile", "scrum", "elk", "lambda", "qt", "rag",
             "magic", "avid", "spice", "cnn", "rnn", "hmm", "boosting", "notion", "slack", "embedded",
             "cadence", "colab", "dsp", "data structures", "outlook", "tally", "wix", "asana", "crm", "seo",
             "visio"}

CATEGORIES = [c for c in ONTOLOGY if c != "non_technical"]
SEMANTIC_THRESHOLD = 0.8


def skill_key(value):
    s = value.strip().lower().replace("&", "and")
    s = re.sub(r"(?<=[a-z0-9])[\s._/\-]+(?=[a-z0-9])", "", s)
    return re.sub(r"\s+", " ", s).strip(" .,:;-")


CANONICAL = {}
for _category, _skills in ONTOLOGY.items():
    for _name, (_aliases, _parents) in _skills.items():
        for _form in [_name] + _aliases:
            CANONICAL.setdefault(skill_key(_form), (_name, _category, _parents))

SURFACE_FORMS = sorted({form for skills in ONTOLOGY.values()
                        for name, (aliases, _) in skills.items()
                        for form in [name.lower()] + aliases}, key=len, reverse=True)
VOCAB = [x for x in SURFACE_FORMS if x not in AMBIGUOUS]
AMBIGUOUS_FORMS = {name for skills in ONTOLOGY.values() for name in skills if name.lower() in AMBIGUOUS}

ROLE_ALIASES = {
    "swe": "Software Engineer", "software developer": "Software Engineer",
    "sr software engineer": "Senior Software Engineer",
    "sr. software engineer": "Senior Software Engineer",
    "senior software developer": "Senior Software Engineer",
    "jr software engineer": "Junior Software Engineer",
    "full stack developer": "Full Stack Engineer",
    "fullstack developer": "Full Stack Engineer",
    "full-stack developer": "Full Stack Engineer",
    "frontend developer": "Frontend Engineer",
    "front end developer": "Frontend Engineer",
    "front-end developer": "Frontend Engineer",
    "backend developer": "Backend Engineer",
    "back end developer": "Backend Engineer",
    "back-end developer": "Backend Engineer",
    "devops engineer": "DevOps Engineer",
    "ml engineer": "Machine Learning Engineer",
    "machine learning developer": "Machine Learning Engineer",
    "data scientist": "Data Scientist", "data analyst": "Data Analyst",
    "project manager": "Project Manager", "product manager": "Product Manager",
    "qa engineer": "QA Engineer", "test engineer": "QA Engineer",
    "ui ux designer": "UI/UX Designer", "ui/ux designer": "UI/UX Designer",
}


def lookup_skill(value):
    return CANONICAL.get(skill_key(value))


def normalize_skill(value):
    hit = lookup_skill(value)
    return hit[0] if hit else value.strip()


def classify_roles(raw_roles):
    result, seen = [], set()
    for raw in raw_roles:
        if raw and raw.strip():
            role = ROLE_ALIASES.get(re.sub(r"\s+", " ", raw.strip().lower()), raw.strip())
            if role.lower() not in seen:
                seen.add(role.lower())
                result.append(role)
    return result


def analyze_skills(raw_skills, matcher=None):
    cleaned = [re.sub(r"\s+", " ", r).strip(" \t•-*|,;:.()") for r in raw_skills if r]
    cleaned = [c for c in cleaned if c and len(c.split()) <= 6]

    # Semantic fallback for strings the knowledge base doesn't know.
    unknown = [c for c in cleaned if not lookup_skill(c)]
    semantic = {}
    if matcher is not None and unknown:
        try:
            threshold = getattr(matcher, "threshold", SEMANTIC_THRESHOLD)
            for raw, (name, score) in zip(unknown, matcher.match(unknown)):
                if name and score >= threshold:
                    semantic[raw] = (name, float(score))
        except Exception:
            semantic = {}

    categorized = {name: [] for name in CATEGORIES}
    details = {}
    for raw in cleaned:
        hit = lookup_skill(raw)
        method, confidence = "knowledge_base", 1.0
        if not hit and raw in semantic:
            name, confidence = semantic[raw]
            hit = lookup_skill(name)
            method = "semantic_match"
        if hit:
            name, category, parents = hit
        else:
            name, category, parents, method, confidence = raw, "other", [], "unmatched", 0.5

        key = name.lower()
        if key in details:
            if raw not in details[key]["raw"]:
                details[key]["raw"].append(raw)
            continue
        details[key] = {"skill": name, "category": category, "parents": parents,
                        "raw": [raw], "method": method, "confidence": round(confidence, 3)}
        if category in categorized:
            categorized[category].append(name)
    return categorized, list(details.values())
