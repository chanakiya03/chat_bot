---
description: How to add questions and generate new training data
---

Follow these steps to expand the chatbot's training dataset with new natural language questions.

### 1. Add New Questions
Open the following file and add your new questions (one per line):
`d:\projects\college_chat\backend\data\question.txt`

> [!TIP]
> You can add questions at the end of the file or under a specific category. The generator will automatically pick up anything that looks like a question (ends with `?` or is longer than 3 words).

### 2. Run the Data Generator
Run this command from the `backend` directory to generate answers for your new questions and update the training set:

```cmd
cd d:\projects\college_chat\backend
python chatbot\engine\generator.py
```

### 3. Verify with a Fast Mini Test
To quickly check if the bot is answering 10 core questions correctly, run:

```cmd
python mini_test.py
```
> [!NOTE]
> This script writes detailed logs to `mini_test_debug.log` and a summary to `mini_test_results.json`.

### 4. Run the Full Stress Test (1,000+ Questions)
To perform a comprehensive accuracy check across 1,100+ variations, run:

```cmd
python stress_test.py
```

### 5. Review Accuracy Report
Once the stress test completes, you can find the final accuracy percentage and detailed results in:
`d:\projects\college_chat\backend\data\stress_test_report.json`
