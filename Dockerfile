# MechaCut — deterministic data transforms (chart, reshape, validate)
# Railway-ready image: binds 0.0.0.0:$PORT, trusts the platform proxy for
# real client IPs (Cloudflare -> Railway -> uvicorn --proxy-headers).
FROM python:3.13-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY main.py chart.py reshape.py repair.py tables.py edits.py dates.py numfmt.py units.py money.py spell.py identity.py checkers.py context.py mdrender.py htmltext.py check.py extract.py rules.py micro.py eth.py ethabi.py routing.py payments.py intake.py verdict.py redlines.py cache.py geo.py leakkit.py chainkit.py taxid.py addrkit.py timekit.py holidays.py icskit.py amortize.py pdftext.py auditor.py sayings.py rates.py pngkit.py certkit.py urlkit.py reldate.py moneykit.py formatkit.py discountkit.py calckit.py scalekit.py formulakit.py reflectkit.py recurrkit.py shoeskit.py srikit.py tzambkit.py compkit.py weekkit.py bagkit.py damagekit.py crosskit.py displaykit.py lockkit.py anchorkit.py pointskit.py dimkit.py castkit.py bogokit.py unitpricekit.py modelidkit.py poultrykit.py xmlkit.py sqlkit.py ficheskit.py digitkit.py webkit.py qrkit.py annuaire.py routeur.py router_annuaire.json bip39_english.txt SKILL.md SKILL-MINI.md integrity.json ./
COPY data/ ./data/
COPY static/ ./static/
COPY locales/ ./locales/

ENV PYTHONUNBUFFERED=1
EXPOSE 8080
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8080} --proxy-headers --forwarded-allow-ips \"*\""]
