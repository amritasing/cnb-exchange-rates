# Start Here

This file is for you, not for recruiters. Delete it before you publish the
repository.

---

## What this project is and why this one

A pipeline that collects the Czech National Bank's daily exchange rates,
normalises them, and stores them in a database.

I chose this source for four reasons.

It needs no API key and no registration, so nothing blocks you tonight.

It is Czech, which means a Prague interviewer recognises it immediately. That is
worth more than it sounds — it makes the project memorable in a way that a
generic dataset is not.

It contains a genuine trap. Rates are quoted per 1, per 100 or per 1000 units
depending on the currency, so a naive load gives you a yen rate that is a
hundred times wrong. Spotting and handling that is exactly the kind of judgement
an interviewer is looking for, and you can talk about it.

And it grows naturally into the bigger project. Daily data means incremental
loading is the obvious next step, weekends and holidays mean missing-data
handling, and the whole thing eventually wants orchestration.

---

## Setup, about thirty minutes

### 1. Install Git and set it up

```bash
git --version          # check whether you already have it
```

If not, install it from git-scm.com, then:

```bash
git config --global user.name "Amrita Singh"
git config --global user.email "your@email.com"
```

### 2. Get the project onto your machine

Put the folder somewhere sensible, then:

```bash
cd cnb-exchange-rates
git init
git add .
git commit -m "First version: fetch, parse and store CNB exchange rates"
```

That is your first commit. Git is now tracking the project.

### 3. Create a virtual environment and install dependencies

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate
# macOS or Linux
source .venv/bin/activate

pip install -r requirements.txt
```

### 4. Run it

```bash
python -m src.pipeline
```

You should see log lines showing it fetched, parsed around 30 currencies, and
stored them.

### 5. Run the tests

```bash
pytest -v
```

Eight tests should pass. I verified the logic here, so if a test fails it is
almost certainly a setup problem rather than a bug — tell me the error.

### 6. Put it on GitHub

Create a new **public** repository on GitHub called `cnb-exchange-rates`. Do not
initialise it with a README, since you already have one. Then:

```bash
git remote add origin https://github.com/YOUR-USERNAME/cnb-exchange-rates.git
git branch -M main
git push -u origin main
```

Delete this file first. Then pin the repository on your GitHub profile.

---

## Read the code in this order

Spend an hour on this. You need to be able to explain every line, because the
whole value of the project is being able to discuss it.

1. **`src/parse.py`** — the heart of it. Note the `Amount` normalisation and why
   it matters, and that the header check exists so a layout change fails loudly.
2. **`tests/test_parse.py`** — see how each rule in `parse.py` has a test,
   including the failure cases. Tests on failure paths are what make a project
   look professional.
3. **`src/store.py`** — read the comment on the primary key. Idempotency is the
   single most important concept in this project.
4. **`src/fetch.py`** — short. Note the timeout and `raise_for_status`.
5. **`src/pipeline.py`** — how the pieces join, plus logging and the exit code.

A suggestion rather than a rule: retype `parse.py` yourself from scratch once,
without copying. It takes twenty minutes and it is the difference between
understanding the code and recognising it.

---

## The four things to be able to say about this project

These are what an interviewer will ask. Have real answers.

**What does it do?** Collects the CNB's daily exchange rate fixing, normalises
rates that are quoted per 100 or per 1000 units, and stores them in a database
with a primary key that makes re-runs safe.

**What was the interesting problem?** The `Amount` column. Rates are not quoted
per single unit, so loading the `Rate` column directly gives you a yen rate a
hundred times too large. I kept the raw columns for auditability and added a
normalised per-unit rate.

**How did you make it reliable?** A primary key on date and currency plus
INSERT OR REPLACE, so running it twice updates rather than duplicates. A header
check so a change to the source file layout fails loudly. A row count check so a
truncated file is rejected. A request timeout. A non-zero exit code so a
scheduler knows it failed.

**What would you do next?** Incremental backfill of missing dates, explicit
handling of weekends and public holidays, orchestration with Airflow including
retries and alerts, PostgreSQL instead of SQLite, and a dbt transformation layer
with tests.

---

## Then do this, and it is the real test

Once it runs, break it deliberately. Three ways:

1. In `src/fetch.py`, change `BASE_URL` to a nonsense address. Run it. Watch it
   fail. Read the error.
2. In `src/parse.py`, change the expected header to something wrong. Run it.
3. Save the raw file to disk, delete a field from one row, and parse that.

Fix each one. Then notice how that afternoon felt — whether finding the cause
was absorbing or infuriating. That is the data engineering question we have been
circling for two days, and this is how you answer it.

---

## After this

When this is pushed and you can explain it, tell me and we will build the second
project. That one adds incremental loading, a second data source, and
orchestration — the things that turn a script into a pipeline.

One honest note: this project alone does not make you a data engineering
candidate. It makes you someone with a public, tested, documented piece of work,
which is more than most career changers have, and it is the foundation the next
two build on.
