#!/usr/bin/env python3
"""Builds the n8n template JSON files in n8n/ from one description per template.

Every template follows the n8n submission guidelines: a yellow overview sticky note
(Who's it for / How it works / Setup steps / Requirements), white step notes, no
credentials or personal ids, and the official Apify node (@apify/n8n-nodes-apify).
"""
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent / "n8n"
APIFY = "@apify/n8n-nodes-apify.apify"

ACTORS = {
    "linkedin-email-finder": ("aaQmB1hxDtRxhCUtX", "LinkedIn Email Finder ✅ New · Profile URL to Email, Bulk (b2bsearch/linkedin-email-finder)"),
    "domain-to-decision-makers": ("Wiwa5fOD7HOfKdilA", "Decision Maker Finder by Domain ✅ New · CEOs, Founders & VPs (b2bsearch/domain-to-decision-makers)"),
    "lookalike-company-finder": ("OTBPcghLrXdZ1FQkx", "Lookalike Company Finder ✅ New · Similar Companies $1.50/1k (b2bsearch/lookalike-company-finder)"),
    "reverse-email-lookup": ("ZDyCwWPNNDsFwnwnM", "Reverse Email Lookup ✅ New · Email to LinkedIn, Name & Company (b2bsearch/reverse-email-lookup)"),
    "company-email-format-finder": ("RseVONATt3sXimyQP", "Company Email Format Finder ✅ New · Real Pattern, $0.02/domain (b2bsearch/company-email-format-finder)"),
    "b2b-leads-finder": ("gZivd9twvcH2kwNQ3", "B2B Leads Finder with Emails ✅ New · Apollo Alternative (b2bsearch/b2b-leads-finder)"),
    "former-employees-finder": ("dntcFC4J43uLk5cvk", "Former Employees Finder ✅ New · Company Alumni by Domain (b2bsearch/former-employees-finder)"),
}

DISCLOSURE = "\n\n### Disclosure\nThe Apify Actor in this template is built by the author of the template. It is pay per result: a miss is a free row."


def sticky(name, content, x, y, w=420, h=300, color=None):
    params = {"width": w, "height": h, "content": content}
    if color:
        params["color"] = color
    return {"parameters": params, "name": name, "type": "n8n-nodes-base.stickyNote", "typeVersion": 1, "position": [x, y]}


def overview(title, who, how, setup, reqs):
    body = f"## {title}\n\n### Who's it for\n{who}\n\n### How it works\n{how}\n\n### Setup steps\n{setup}\n\n### Requirements\n{reqs}{DISCLOSURE}"
    return sticky("Overview", body, -900, -220, 480, 760)


def node(name, type_, version, params, x, y):
    return {"parameters": params, "name": name, "type": type_, "typeVersion": version, "position": [x, y]}


def manual(x=-340, y=140):
    return node("When clicking 'Execute workflow'", "n8n-nodes-base.manualTrigger", 1, {}, x, y)


def sheets_read(name, x, y):
    return node(name, "n8n-nodes-base.googleSheets", 4.7, {
        "documentId": {"__rl": True, "mode": "list", "value": ""},
        "sheetName": {"__rl": True, "mode": "list", "value": ""},
        "options": {},
    }, x, y)


def sheets_append(name, columns, x, y):
    schema = [{"id": c, "displayName": c, "required": False, "defaultMatch": False, "display": True, "type": "string", "canBeUsedToMatch": True} for c in columns]
    return node(name, "n8n-nodes-base.googleSheets", 4.7, {
        "operation": "append",
        "documentId": {"__rl": True, "mode": "list", "value": ""},
        "sheetName": {"__rl": True, "mode": "list", "value": ""},
        "columns": {"mappingMode": "defineBelow", "value": {c: f"={{{{ $json.{c} }}}}" for c in columns}, "matchingColumns": [], "schema": schema},
        "options": {},
    }, x, y)


def aggregate(name, field, out, x, y):
    return node(name, "n8n-nodes-base.aggregate", 1, {
        "fieldsToAggregate": {"fieldToAggregate": [{"fieldToAggregate": field, "renameField": True, "outputFieldName": out}]},
        "options": {},
    }, x, y)


def apify(name, slug, body_expr, x, y):
    actor_id, label = ACTORS[slug]
    return node(name, APIFY, 1, {
        "actorId": {"__rl": True, "mode": "list", "value": actor_id, "cachedResultUrl": f"https://console.apify.com/actors/{actor_id}/input", "cachedResultName": label},
        "timeout": {},
        "operation": "Run actor and get dataset",
        "customBody": body_expr,
        "actorSource": "store",
    }, x, y)


def keep_found(name, x, y, extra=None):
    conds = [{"id": "status-found", "leftValue": "={{ $json._status }}", "rightValue": "found", "operator": {"type": "string", "operation": "equals"}}]
    if extra:
        conds.append(extra)
    return node(name, "n8n-nodes-base.filter", 2.2, {
        "conditions": {"options": {"caseSensitive": False, "leftValue": "", "typeValidation": "loose"}, "conditions": conds, "combinator": "and"},
        "options": {},
    }, x, y)


def code(name, js, x, y):
    return node(name, "n8n-nodes-base.code", 2, {"jsCode": js}, x, y)


def chain(names):
    return {a: {"main": [[{"node": b, "type": "main", "index": 0}]]} for a, b in zip(names, names[1:])}


def workflow(name, nodes, connections):
    return {"name": name, "nodes": nodes, "connections": connections, "settings": {"executionOrder": "v1"}, "pinData": {}}


TEMPLATES = {}

# ---------------------------------------------------------------- 1. LinkedIn URLs → emails
TEMPLATES["linkedin-urls-to-work-emails-sheets"] = workflow(
    "Find work emails for LinkedIn profile URLs in Google Sheets with Apify (no cookies, pay per email)",
    [
        overview(
            "Find work emails for LinkedIn profile URLs in Google Sheets",
            "Sales, recruiting and growth teams with a sheet of LinkedIn profile URLs (event attendees, Sales Navigator exports, a CRM list) who need an email address for each person without a LinkedIn login or a browser extension.",
            "1. Reads the `linkedinUrl` column of your Google Sheet.\n2. Collects the URLs into one list and runs **LinkedIn Email Finder** (`b2bsearch/linkedin-email-finder`) on Apify once for the whole list. The Actor reads addresses on record from a database of 800M+ professional profiles; it does not scrape LinkedIn pages.\n3. Keeps the rows where an address was found and appends them to a results sheet: email, email type (work or personal), name, title, company, profile URL.",
            "- Add your Apify credential to the Apify node (API token from Apify Console → Settings → Integrations).\n- Pick the input sheet (column `linkedinUrl`) in **Read profile URLs** and the output sheet in **Append emails**.\n- Optional: set `includePersonalEmails: true` in the Apify node body to also receive personal addresses.",
            "- Apify account (free plan works). $8 per 1,000 profiles with an address found; profiles without an address are free rows. A list of 1,000 URLs finishes in a few minutes.\n- Google Sheets credential.",
        ),
        sticky("Note: read", "## 1. Read the list\nOne row per LinkedIn profile URL. Bare handles (`satyanadella`) work too. Up to 10,000 per run.", -380, -220, color=7),
        sticky("Note: apify", "## 2. One Actor run for the whole list\nThe Aggregate node turns the rows into one `profileUrls` array so the Actor runs once. Every output row carries `_status`: `found` is the paid result, `no_email` and `not_found` are free.", 80, -220, color=7),
        sticky("Note: write", "## 3. Save what was found\n`email` is the best address, `emailType` says work or personal, `workEmails` lists every work address on record.", 540, -220, color=7),
        manual(),
        sheets_read("Read profile URLs", -120, 140),
        aggregate("Collect URLs", "linkedinUrl", "profileUrls", 120, 140),
        apify("LinkedIn Email Finder (Apify)", "linkedin-email-finder", "={{ JSON.stringify({ profileUrls: $json.profileUrls }) }}", 360, 140),
        keep_found("Keep found", 600, 140),
        sheets_append("Append emails", ["email", "emailType", "fullName", "jobTitle", "companyName", "linkedinUrl", "_status"], 840, 140),
    ],
    chain(["When clicking 'Execute workflow'", "Read profile URLs", "Collect URLs", "LinkedIn Email Finder (Apify)", "Keep found", "Append emails"]),
)

# ---------------------------------------------------------------- 2. domains → decision makers
TEMPLATES["company-domains-to-decision-makers-sheets"] = workflow(
    "Find decision makers (CEO, founders, VPs) for a list of company domains and save them to Google Sheets with Apify",
    [
        overview(
            "Find decision makers for a list of company domains",
            "Outbound and ABM teams who have target accounts as website domains and need the people to contact: founders, C-level, VPs and directors, with LinkedIn URLs, without Sales Navigator.",
            "1. Reads the `domain` column of your Google Sheet (acme.com).\n2. Runs **Decision Maker Finder by Domain** (`b2bsearch/domain-to-decision-makers`) on Apify for the whole list: founders and CEOs first, then C-level, VPs and directors, up to a cap per company. Rows come from a database of professional profiles, no scraping.\n3. Appends one row per person to a results sheet: name, title, seniority, company, LinkedIn URL and whether a work email is on record.",
            "- Add your Apify credential to the Apify node.\n- Pick the input sheet (column `domain`) and the output sheet.\n- Optional: change `roles` (founder, cxo, vp, director) and `maxPerCompany` in the Apify node body, or add `titleKeywords` such as [\"marketing\", \"sales\"].",
            "- Apify account. $3.20 per 1,000 people delivered; companies with nobody matching are free rows. 100 domains at 5 people each cost at most $1.60.\n- Google Sheets credential.\n- For email addresses, pass the `linkedinUrl` column to the LinkedIn Email Finder template.",
        ),
        sticky("Note: read", "## 1. Read the domains\nWebsite domains, one per row. Full URLs are reduced to the domain; brand domains resolve to the owning company.", -380, -220, color=7),
        sticky("Note: apify", "## 2. Decision makers per domain\n`roles` picks the seniority levels; `maxPerCompany` caps the spend. Rows are ordered founder and CEO first.", 80, -220, color=7),
        sticky("Note: write", "## 3. Save the people\n`hasWorkEmail` tells you who is reachable before you pay for an address.", 540, -220, color=7),
        manual(),
        sheets_read("Read domains", -120, 140),
        aggregate("Collect domains", "domain", "domains", 120, 140),
        apify("Decision Maker Finder (Apify)", "domain-to-decision-makers", "={{ JSON.stringify({ domains: $json.domains, roles: ['founder', 'cxo', 'vp', 'director'], maxPerCompany: 5 }) }}", 360, 140),
        keep_found("Keep found", 600, 140),
        sheets_append("Append decision makers", ["fullName", "jobTitle", "seniority", "companyName", "companyDomain", "linkedinUrl", "hasWorkEmail", "_status"], 840, 140),
    ],
    chain(["When clicking 'Execute workflow'", "Read domains", "Collect domains", "Decision Maker Finder (Apify)", "Keep found", "Append decision makers"]),
)

# ---------------------------------------------------------------- 3. lookalikes → decision makers
TEMPLATES["best-customers-to-lookalike-accounts-sheets"] = workflow(
    "Expand your best customers into lookalike companies and their decision makers with Apify and Google Sheets",
    [
        overview(
            "Expand your best customers into lookalike accounts",
            "Founders and sales teams who know their ten best customers and want the next hundred: companies in the same industry, country and size band, with the people to contact at each.",
            "1. A Code node holds the seed domains (your best customers).\n2. **Lookalike Company Finder** (`b2bsearch/lookalike-company-finder`) returns similar companies for each seed with an explicit `matchedOn` string (industry, country, size): no black-box score.\n3. The lookalike domains go to **Decision Maker Finder by Domain** for founders, C-level and VPs.\n4. One row per person lands in your Google Sheet with the company it was found at and the seed it came from.",
            "- Add your Apify credential to both Apify nodes.\n- Edit the seed domains in **Seed customers**.\n- Pick the output sheet in **Append accounts and people**.\n- Optional: `maxPerSeed`, `sameCountry`, `sameSize`, `countries` in the first Apify node; `roles` and `maxPerCompany` in the second.",
            "- Apify account. Lookalikes cost $0.0015 per company ($1.50 per 1,000); decision makers $0.0032 per person. Ten seeds at 25 lookalikes and 3 people each: about $0.38 + $1.20.\n- Google Sheets credential.",
        ),
        sticky("Note: seeds", "## 1. Seeds\nTen distinct customer domains work best; two similar seeds can return the same company twice.", -380, -220, color=7),
        sticky("Note: lookalikes", "## 2. Lookalikes\nEvery row says what it matched on. Seeds that resolve to nothing are free rows.", 80, -220, color=7),
        sticky("Note: people", "## 3. People at each lookalike\nThe Filter drops the free seed notes, the Aggregate collects the domains, the second Actor runs once for all of them.", 540, -220, color=7),
        manual(),
        code("Seed customers", "// Your best customers, as website domains (up to 50).\nconst seedDomains = ['linear.app', 'n26.com'];\nreturn [{ json: { seedDomains } }];", -120, 140),
        apify("Lookalike Company Finder (Apify)", "lookalike-company-finder", "={{ JSON.stringify({ seedDomains: $json.seedDomains, maxPerSeed: 25, sameCountry: true, sameSize: true }) }}", 120, 140),
        keep_found("Keep lookalikes", 360, 140),
        aggregate("Collect lookalike domains", "domain", "domains", 600, 140),
        apify("Decision Maker Finder (Apify)", "domain-to-decision-makers", "={{ JSON.stringify({ domains: $json.domains, roles: ['founder', 'cxo', 'vp'], maxPerCompany: 3 }) }}", 840, 140),
        keep_found("Keep people", 1080, 140),
        sheets_append("Append accounts and people", ["companyName", "companyDomain", "fullName", "jobTitle", "seniority", "linkedinUrl", "hasWorkEmail"], 1320, 140),
    ],
    chain(["When clicking 'Execute workflow'", "Seed customers", "Lookalike Company Finder (Apify)", "Keep lookalikes", "Collect lookalike domains", "Decision Maker Finder (Apify)", "Keep people", "Append accounts and people"]),
)

# ---------------------------------------------------------------- 4. sign-up email → person → HubSpot
TEMPLATES["signup-email-enrichment-hubspot"] = workflow(
    "Enrich new sign-ups by email (name, job title, company, LinkedIn) and create the HubSpot contact with Apify",
    [
        overview(
            "Enrich new sign-ups by email and create the HubSpot contact",
            "Product-led SaaS teams who get sign-ups with only an email address and want to know who the person is, where they work and what they do before routing the lead.",
            "1. A Webhook receives the sign-up (POST with an `email` field) from your app, a form tool or a Zap.\n2. **Reverse Email Lookup** (`b2bsearch/reverse-email-lookup`) turns the address into the person: name, job title, employer, location, LinkedIn URL. Works for personal addresses too (gmail, outlook).\n3. If a person was found, HubSpot gets a contact with the enriched fields; if not, nothing is created and nothing is charged.",
            "- Add your Apify credential to the Apify node.\n- Add your HubSpot credential to **Create HubSpot contact** and map the properties you use.\n- Point your sign-up form at the Webhook URL (production URL after activation).",
            "- Apify account. $3.20 per 1,000 addresses resolved to a person; unknown addresses are free rows. Expect roughly 1 in 5 personal addresses and most work addresses to resolve.\n- HubSpot credential.",
        ),
        sticky("Note: webhook", "## 1. Sign-up arrives\nPOST `{ \"email\": \"jane@example.com\" }`. Add a name field if you have one: a name beside the address raises the hit rate.", -380, -220, color=7),
        sticky("Note: apify", "## 2. Who is this?\n`compact: true` returns a short row: identity, current role, location, the latest positions. Same price as the full record.", 80, -220, color=7),
        sticky("Note: hubspot", "## 3. Create the contact\nOnly rows with `_status: found` reach HubSpot. Map `jobTitle`, `companyName`, `profileUrl` to your properties.", 540, -220, color=7),
        node("Sign-up webhook", "n8n-nodes-base.webhook", 2, {"httpMethod": "POST", "path": "signup-enrich", "options": {}}, -340, 140),
        apify("Reverse Email Lookup (Apify)", "reverse-email-lookup", "={{ JSON.stringify({ emails: [$json.body.email], compact: true }) }}", -100, 140),
        keep_found("Person found?", 140, 140),
        node("Create HubSpot contact", "n8n-nodes-base.hubspot", 2.1, {
            "resource": "contact",
            "operation": "upsert",
            "email": "={{ $json._input.email }}",
            "additionalFields": {"firstName": "={{ $json.firstName }}", "lastName": "={{ $json.lastName }}", "jobTitle": "={{ $json.jobTitle }}", "companyName": "={{ $json.companyName }}", "websiteUrl": "={{ $json.profileUrl }}"},
        }, 380, 140),
    ],
    chain(["Sign-up webhook", "Reverse Email Lookup (Apify)", "Person found?", "Create HubSpot contact"]),
)

# ---------------------------------------------------------------- 5. email format check
TEMPLATES["company-email-format-check-sheets"] = workflow(
    "Check the email format of companies (first.last@, flast@) before guessing work emails, from a domain list in Google Sheets with Apify",
    [
        overview(
            "Check company email formats before you guess work emails",
            "Anyone who builds work email addresses from names: SDRs, recruiters, agencies. Guessing `first.last@` works at some companies and wastes verification credits at others. This workflow tells you which is which.",
            "1. Reads the `domain` column of your Google Sheet.\n2. **Company Email Format Finder** (`b2bsearch/company-email-format-finder`) reads the addresses on record for each company's current staff and reports the pattern most of them follow, how many people confirm it and the agreement. No address leaves the Actor; samples are masked.\n3. Appends one row per domain to a results sheet: pattern, example, confirmations, agreement, other patterns in use, status.",
            "- Add your Apify credential to the Apify node.\n- Pick the input sheet (column `domain`) and the output sheet.\n- Use `agreement` as your bar: build addresses where it is 0.8 or higher; use an email finder on record for the rest.",
            "- Apify account. $0.02 per domain with a confirmed pattern; weak evidence, unknown domains and shared-hosting domains are free. 1,000 domains cost at most $20.\n- Google Sheets credential.",
        ),
        sticky("Note: read", "## 1. Domains\nUp to 5,000 per run; about 1–2 seconds per domain.", -380, -220, color=7),
        sticky("Note: apify", "## 2. Pattern from real addresses\n`confirmations` = distinct employees whose address follows the pattern. 20 at 0.9 agreement is a convention; 3 at 0.5 is a hint.", 80, -220, color=7),
        sticky("Note: write", "## 3. Save the verdict\n`otherPatterns` shows a company with two conventions. `_status` explains every free row.", 540, -220, color=7),
        manual(),
        sheets_read("Read domains", -120, 140),
        aggregate("Collect domains", "domain", "domains", 120, 140),
        apify("Company Email Format Finder (Apify)", "company-email-format-finder", "={{ JSON.stringify({ domains: $json.domains, sampleLimit: 200 }) }}", 360, 140),
        sheets_append("Append formats", ["domain", "pattern", "patternExample", "confirmations", "agreement", "coverage", "otherPatterns", "_status"], 600, 140),
    ],
    chain(["When clicking 'Execute workflow'", "Read domains", "Collect domains", "Company Email Format Finder (Apify)", "Append formats"]),
)

# ---------------------------------------------------------------- 6. ICP → leads with emails
TEMPLATES["b2b-lead-list-with-emails-apollo-alternative-sheets"] = workflow(
    "Build a B2B lead list with emails from job title, country and company size filters (Apollo alternative) into Google Sheets with Apify",
    [
        overview(
            "Build a B2B lead list with emails from ICP filters",
            "Founders and SDRs who want a prospect list by job title, seniority, country, industry and company size, with an email on every row, without an Apollo or Sales Navigator subscription.",
            "1. A Set node holds your filters (edit the values).\n2. **B2B Leads Finder** (`b2bsearch/b2b-leads-finder`) on Apify searches a database of 800M+ professional profiles and returns one row per person who has an email on record: name, title, company, location, LinkedIn URL, email and its type. People without an email are skipped and not charged.\n3. The rows are appended to your Google Sheet, ready for a sequence tool.",
            "- Add your Apify credential to the Apify node.\n- Edit `jobTitles`, `countries`, `industries`, `companySizeMin`, `companySizeMax`, `emailType` and `maxResults` in **ICP filters**.\n- Pick the output sheet. Run again with a different sheet to grow the list; use `excludeDatasets` in the Actor to skip people from earlier runs.",
            "- Apify account. $1.50–$3 per 1,000 leads depending on your Apify plan; 500 leads cost at most $1.50.\n- Google Sheets credential.",
        ),
        sticky("Note: filters", "## 1. Your ICP\nTitle words, two-letter country codes, industry names, employee range. `emailType` = work, personal or any.", -380, -220, color=7),
        sticky("Note: apify", "## 2. Leads with an email\nOne flat row per person. `maxResults` is your spend cap.", 80, -220, color=7),
        sticky("Note: write", "## 3. To the sheet\nColumns match what outreach tools import: name, email, title, company, LinkedIn URL.", 540, -220, color=7),
        manual(),
        node("ICP filters", "n8n-nodes-base.set", 3.4, {
            "assignments": {"assignments": [
                {"id": "jobTitles", "name": "jobTitles", "value": "={{ ['head of marketing', 'vp marketing', 'cmo'] }}", "type": "array"},
                {"id": "countries", "name": "countries", "value": "={{ ['gb'] }}", "type": "array"},
                {"id": "industries", "name": "industries", "value": "={{ ['Software Development'] }}", "type": "array"},
                {"id": "companySizeMin", "name": "companySizeMin", "value": 50, "type": "number"},
                {"id": "companySizeMax", "name": "companySizeMax", "value": 200, "type": "number"},
                {"id": "emailType", "name": "emailType", "value": "work", "type": "string"},
                {"id": "maxResults", "name": "maxResults", "value": 500, "type": "number"},
            ]},
            "options": {},
        }, -120, 140),
        apify("B2B Leads Finder (Apify)", "b2b-leads-finder", "={{ JSON.stringify({ jobTitles: $json.jobTitles, countries: $json.countries, industries: $json.industries, companySizeMin: $json.companySizeMin, companySizeMax: $json.companySizeMax, emailType: $json.emailType, maxResults: $json.maxResults }) }}", 120, 140),
        keep_found("Keep leads", 360, 140),
        sheets_append("Append leads", ["fullName", "email", "emailType", "jobTitle", "companyName", "companyDomain", "location", "linkedinUrl"], 600, 140),
    ],
    chain(["When clicking 'Execute workflow'", "ICP filters", "B2B Leads Finder (Apify)", "Keep leads", "Append leads"]),
)

# ---------------------------------------------------------------- 7. former employees → where they went
TEMPLATES["former-employees-champion-tracking-sheets"] = workflow(
    "Track who left your customers' companies and where they work now (champion tracking) with Apify and Google Sheets",
    [
        overview(
            "Track who left your customers and where they work now",
            "Customer success and sales teams: a champion who leaves is a churn risk at the old account and a warm lead at the new one. This workflow lists both, by company domain.",
            "1. Reads the `domain` column of your Google Sheet (customer websites).\n2. **Former Employees Finder** (`b2bsearch/former-employees-finder`) returns people who left those companies after a given year, with their current title, current company and its domain.\n3. Appends one row per person to a results sheet, so you can filter by seniority and reach out at the new employer.",
            "- Add your Apify credential to the Apify node.\n- Pick the input sheet (column `domain`) and the output sheet.\n- Optional: change `leftAfterYear`, add `titleKeywords` or `seniority` in the Apify node body.",
            "- Apify account. $0.10 per page of up to 50 people; `previewOnly: true` counts for free first.\n- Google Sheets credential.\n- For the email at the new company, pass `linkedinUrl` to the LinkedIn Email Finder template.",
        ),
        sticky("Note: read", "## 1. Customer domains\nOne per row. Brand domains resolve to the owner.", -380, -220, color=7),
        sticky("Note: apify", "## 2. Who left, and where to\n`currentCompanyDomain` is the new account; `formerCompany` is the one they left.", 80, -220, color=7),
        sticky("Note: write", "## 3. Save the moves\nSort by `currentCompany` to spot several alumni landing at the same place.", 540, -220, color=7),
        manual(),
        sheets_read("Read customer domains", -120, 140),
        aggregate("Collect domains", "domain", "companyDomains", 120, 140),
        apify("Former Employees Finder (Apify)", "former-employees-finder", "={{ JSON.stringify({ companyDomains: $json.companyDomains, leftAfterYear: 2025, maxResults: 200 }) }}", 360, 140),
        keep_found("Keep found", 600, 140),
        sheets_append("Append moves", ["fullName", "formerCompany", "currentTitle", "currentCompany", "currentCompanyDomain", "linkedinUrl", "hasWorkEmail"], 840, 140),
    ],
    chain(["When clicking 'Execute workflow'", "Read customer domains", "Collect domains", "Former Employees Finder (Apify)", "Keep found", "Append moves"]),
)


if __name__ == "__main__":
    ROOT.mkdir(exist_ok=True)
    for slug, wf in TEMPLATES.items():
        names = {n["name"] for n in wf["nodes"]}
        for src, c in wf["connections"].items():
            assert src in names, src
            for out in c["main"]:
                for t in out:
                    assert t["node"] in names, t["node"]
        (ROOT / f"{slug}.json").write_text(json.dumps(wf, indent=2, ensure_ascii=False) + "\n")
        print(slug, len(wf["nodes"]), "nodes")
