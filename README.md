# DiffInsight

---

**DiffInsight** is a lightweight, interactive tool that transforms Git diffs into **clear, structured, and risk-assessed code review reports**. Designed for developers, team leads, and code reviewers, it highlights **what changed, why it changed, and its impact** — all presented in a printer-style interface for a unique and engaging experience.
By simply uploading a `.diff` or `.txt` file generated from two commits, branches, or versions, DiffInsight leverages **LLM-based analysis** to provide practical insights and suggestions for code quality improvement.

---

## 💡 Key Features

* Generates **structured, actionable code review reports** from Git diffs.
* Highlights **risk level**: HIGH, MEDIUM, LOW.
* Separate modes for **Senior Reviewer** and **Junior Developer mentoring**.
* Scrollable, animated, printer-style interface for readability.
* Works with **diffs from commits, branches, files, or tags**.
* Fully self-contained — no IDE plugin required.

---

## 🌟 Why DiffInsight Matters

* **Accelerates code reviews**: Quickly identify critical issues without manually inspecting every line.
* **Improves code quality**: Provides actionable refactoring suggestions.
* **Enhances learning**: Junior developers receive clear explanations and guidance on code changes.
* **Reduces merge risks**: Understand potential impact before merging feature branches.

---

## 🎯 Target Audience

* Software engineers seeking faster, reliable code reviews.
* Team leads wanting **risk-aware insights** before merging code.
* Junior developers or mentees learning **best practices** from diffs.
* Open-source contributors reviewing PRs or branches.

---

## 🛠️ Installation & Setup

1. **Clone the repository**:

```bash
git clone https://github.com/ShreyaVijaykumar/Diff-Insight.git
cd diffinsight
```

2. **Install dependencies** (ensure Python 3.9+):

```bash
pip install -r requirements.txt
```

3. **Start the backend server**:

```bash
uvicorn backend.main:app --reload
```

> Make sure you are in the project root directory `diffinsight` and perform `cd backend` when running the above command.

4. **Open your browser** and navigate to:

```
http://127.0.0.1:8000/
```

5. **Upload a `.diff` or `.txt` file** generated from your Git repository and select the review mode.

---

## 📄 How to Generate a Git Diff File

The Git `diff` command allows you to see differences between commits, branches, or files. You can save this output to a file and upload it to DiffInsight.

### **Common Use Cases**

* **View unstaged changes**:

```bash
git diff
```

* **View staged changes**:

```bash
git diff --staged
```

* **View all changes since last commit**:

```bash
git diff HEAD
```

* **Compare two commits**:

```bash
git diff <commit-id-1> <commit-id-2> > my_diff.txt
```

* **Compare two branches**:

```bash
git diff main feature-branch > branch_diff.txt
```

* **Compare a specific file**:

```bash
git diff <file-path> > file_diff.txt
```

* **Compare tags**:

```bash
git diff v1.0 v1.1 > tag_diff.txt
```

> Replace `<commit-id>`, `<branch>`, `<file-path>`, or `<tag>` with your specific references.
> Save the output using `>` to create a `.txt` file, which can then be uploaded to DiffInsight.

### **Understanding the Output**

* `--- a/file.txt` → Original file.
* `+++ b/file.txt` → Updated file.
* `@@ -m,n +o,p @@` → Chunk header showing line numbers.
* `-` → Line removed.
* `+` → Line added.
* Lines without `+` or `-` → Unchanged context.

For a **graphical comparison**, use:

```bash
git difftool
```

---

## 📈 Impact

* Reduces time spent manually reviewing diffs.
* Increases team efficiency and code quality.
* Educates junior developers through clear explanations.
* Makes code review reports **shareable and visually appealing**.

---

## 🧑‍💻 How It Works

1. Upload a `.diff` file.
2. DiffInsight parses the file and computes a **risk level**.
3. LLM-based analysis generates structured insights.
4. Output is shown in a **scrollable, animated, printer-style report** with LEDs indicating risk.

---

## 👀 Preview

```
DIFFINSIGHT REPORT
------------------
Risk Level : HIGH

TITLE: Refactor login flow
CHANGE_SUMMARY: Simplified authentication logic and fixed edge cases
MODIFIED_FILES: auth.py, login.py
WHAT_CHANGED: Updated login flow, added error handling
WHY_CHANGED: Improve security and readability
RISK_LEVEL: HIGH
IMPACT: High risk on authentication
REVIEWER_NOTES: Ensure unit tests are added
```


