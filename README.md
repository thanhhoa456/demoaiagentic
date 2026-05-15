# 🤖 Agentic QA System

**End-to-end AI-powered QA pipeline using AutoGen + NVIDIA LLM + Jira**

```
Jira User Story ──► BusinessAnalysisAgent ──► ManualTestcaseAgent ──► AutomationTestcaseAgent
                                                                              │
                                                                              ▼
                                                               Java TestNG Maven test code
```

---

## 📁 Project Structure

```
agentic-qa-system/
├── orchestrator.py                  # 🎯 Main entry point (AutoGen leader)
├── .env                             # 🔐 API keys & config
├── requirements.txt                 # Python dependencies
│
├── agents/
│   ├── business_analysis_agent.py   # Analyses user stories
│   ├── manual_testcase_agent.py     # Writes manual test cases
│   └── automation_testcase_agent.py # Converts to Java TestNG code
│
├── prompts/                         # ✏️  FILL THESE IN
│   ├── business_analysis.md         # Prompt for BA agent
│   ├── manual_testcase.md           # Prompt for manual QA agent
│   ├── automation_testcase.md       # Prompt for automation agent
│   └── java_testng_maven_example.md # Java project context/conventions
│
├── tools/
│   ├── jira_tool.py                 # Fetches stories from Jira REST API v3
│   └── file_tool.py                 # Saves agent outputs to disk
│
├── output/                          # 📤 Generated artifacts (auto-created)
│   ├── business_analysis/
│   ├── manual_testcases/
│   └── automation_testcases/
│
└── java-testng-maven-example/       # ☕ Java Maven project skeleton
    ├── pom.xml
    └── src/
        ├── main/java/com/qa/
        │   ├── BaseTest.java        # WebDriver setup/teardown
        │   └── BasePage.java        # Page Object base class
        └── test/
            ├── java/com/qa/tests/
            │   └── SampleTest.java  # Placeholder (AI replaces this)
            └── resources/
                └── testng.xml       # TestNG suite config
```

---

## ⚙️ Prerequisites

| Requirement | Version |
|---|---|
| Python | 3.9+ |
| pip | latest |
| Java JDK | 11+ |
| Maven | 3.8+ |
| Chrome Browser | Latest |
| Git | any |

---

## 🚀 Setup & Run (Step by Step)

### Step 1 — Clone / create the project folder

```bash
# If starting fresh:
mkdir agentic-qa-system && cd agentic-qa-system
# (copy all project files here)
```

### Step 2 — Configure your credentials

Edit `.env` with your real values:

```dotenv
API_KEY=nvapi-xxxxxxxxxxxxxxxxxxxxxxxx
MODEL_NAME=nvidia/nemotron-3-nano-omni-30b-a3b-reasoning
BASE_URL=https://integrate.api.nvidia.com/v1

JIRA_URL=https://ivshcmtraining.atlassian.net
JIRA_USER=your-email@fpt.com
JIRA_TOKEN=your_jira_api_token_here

OUTPUT_DIR=./output
```

**Where to get NVIDIA API Key:**  
→ https://build.nvidia.com → sign in → API Keys → Generate

**Where to get Jira API Token:**  
→ https://id.atlassian.com/manage-profile/security/api-tokens → Create API token

### Step 3 — Install Python dependencies

```bash
# Create virtual environment (recommended)
python -m venv venv

# Activate:
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install packages
pip install -r requirements.txt
```

### Step 4 — Fill in your prompt files

Open each file in `prompts/` and add your QA skill instructions:

| File | What to add |
|---|---|
| `prompts/business_analysis.md` | How the BA agent should analyse user stories |
| `prompts/manual_testcase.md` | How to write manual test cases (format, coverage, etc.) |
| `prompts/automation_testcase.md` | How to convert to Java TestNG code |
| `prompts/java_testng_maven_example.md` | Your project conventions, base classes, etc. |

> ⚠️ The agents will not work correctly without these prompts!

### Step 5 — Test Jira connection

```bash
python tools/jira_tool.py SCRUM-100
```

You should see the user story printed in the terminal. If you get a 401 error, check your `JIRA_USER` and `JIRA_TOKEN`.

### Step 6 — Run the pipeline

**Full pipeline (recommended):**
```bash
python orchestrator.py --jira SCRUM-100
```

**Run specific steps only:**
```bash
# Only fetch Jira story (no AI)
python orchestrator.py --jira SCRUM-100 --task fetch

# Fetch + business analysis only
python orchestrator.py --jira SCRUM-100 --task analysis

# Fetch + manual test cases only
python orchestrator.py --jira SCRUM-100 --task manual

# Manual + automation code (no BA analysis)
python orchestrator.py --jira SCRUM-100 --task automation

# Everything
python orchestrator.py --jira SCRUM-100 --task full
```

### Step 7 — Check outputs

After the pipeline runs, check the `output/` folder:

```
output/
├── business_analysis/
│   └── business_analysis_SCRUM-100_20260515_103000.md
├── manual_testcases/
│   └── manual_testcase_SCRUM-100_20260515_103010.md
└── automation_testcases/
    └── automation_testcase_SCRUM-100_20260515_103020.java
```

### Step 8 — Copy generated Java test to Maven project

1. Copy the generated `.java` file from `output/automation_testcases/` to:
   ```
   java-testng-maven-example/src/test/java/com/qa/tests/
   ```

2. Update `src/test/resources/testng.xml` to include the new test class:
   ```xml
   <class name="com.qa.tests.YourGeneratedTest"/>
   ```

3. Run Maven tests:
   ```bash
   cd java-testng-maven-example
   mvn clean test
   ```

---

## 🔧 Troubleshooting

### Error: `401 Unauthorized` from Jira
→ Double-check `JIRA_USER` (must be your email, not username) and `JIRA_TOKEN`.

### Error: `AuthenticationError` from NVIDIA API
→ Make sure `API_KEY` starts with `nvapi-` and has not expired.

### Error: `ModuleNotFoundError: No module named 'autogen'`
→ Run: `pip install pyautogen==0.2.38`

### Agent returns empty or wrong content
→ Your prompt files in `prompts/` may be empty or unclear. Fill them in with detailed instructions.

### Maven: `ChromeDriver` not found
→ The project uses `WebDriverManager` which downloads it automatically. Just make sure you have Chrome installed.

### Maven build fails
→ Check Java version: `java -version` (must be 11+) and Maven: `mvn -version` (3.8+)

---

## 🧩 How Agentic AI Works Here

This system implements the **Perceive → Reason → Act** cycle:

| Phase | What happens |
|---|---|
| **Perceive** | Orchestrator fetches user story from Jira (real data, no assumptions) |
| **Reason** | Each agent reads its skill prompt and analyses the input |
| **Act** | Agent produces structured output (analysis / test cases / code) |
| **Chain** | Output of one agent becomes input for the next |

The **Orchestrator** acts as the AutoGen "group leader" — it decides which agents to invoke based on the `--task` flag, passes context between them, and saves all outputs.

---

## 📝 Agent Roles

| Agent | Input | Output |
|---|---|---|
| `BusinessAnalysisAgent` | Raw Jira user story | Structured analysis, acceptance criteria, risks |
| `ManualTestcaseAgent` | User story + analysis | Manual test cases (positive/negative/edge) |
| `AutomationTestcaseAgent` | Manual test cases | Java TestNG Selenium code |

---

## ❓ Questions?

Fill in your prompt files, run the Jira connection test first, then run the full pipeline.  
The system is designed so you can swap models, agents, or prompts independently.
