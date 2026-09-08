# Smart Enquiry Assistant — 100 Question Evaluation

Test set: 80 answerable + 20 unanswerable = 100 questions.

Run from the project root:
`python evaluation/evaluate.py`

Your normal local `.env` must contain GEMINI_API_KEY. Never share the `.env` file or API key.

The script reports:
- Overall answer accuracy
- Page retrieval hit rate for answerable questions
- Refusal accuracy for unanswerable questions

Results:
- evaluation/results/results.json
- evaluation/results/results.csv

The automated answer check is keyword-based, so manually review borderline answers before using the percentage in an academic report.
