# b2bsearch workflows

Ready-to-import automations and step-by-step guides that use the [`b2bsearch` Actors on Apify](https://apify.com/b2bsearch) in a real sales or research process: from a trigger to a Slack message, a CRM row or a table an agent writes. Every Actor is pay per result and reads a database of professional profile and company records without scraping or a LinkedIn login.

| Workflow | What it does | n8n | Guide |
|---|---|---|---|
| New hires signal | Every Monday, who joined your target accounts in a buying role and where they came from, to Slack | [new-hires-to-slack.json](n8n/new-hires-to-slack.json) | [articles/new-hires-signal.md](articles/new-hires-signal.md) |
| LinkedIn URLs to work emails | A sheet of LinkedIn profile URLs to emails on record, one Actor run for the whole list | [linkedin-urls-to-work-emails-sheets.json](n8n/linkedin-urls-to-work-emails-sheets.json) | |
| Domains to decision makers | Founders, C-level, VPs and directors for a list of company domains | [company-domains-to-decision-makers-sheets.json](n8n/company-domains-to-decision-makers-sheets.json) | |
| Best customers to lookalike accounts | Seed domains to similar companies to the people at each | [best-customers-to-lookalike-accounts-sheets.json](n8n/best-customers-to-lookalike-accounts-sheets.json) | |
| Sign-up enrichment to HubSpot | Webhook with an email to person, title, company, HubSpot contact | [signup-email-enrichment-hubspot.json](n8n/signup-email-enrichment-hubspot.json) | |
| Email format check | The work email convention of each domain before you guess addresses | [company-email-format-check-sheets.json](n8n/company-email-format-check-sheets.json) | |
| B2B lead list with emails | ICP filters to leads with an email, an Apollo alternative | [b2b-lead-list-with-emails-apollo-alternative-sheets.json](n8n/b2b-lead-list-with-emails-apollo-alternative-sheets.json) | |
| Champion tracking | Who left your customers' companies and where they work now | [former-employees-champion-tracking-sheets.json](n8n/former-employees-champion-tracking-sheets.json) | |

Each guide has a version for Claude Code (a prompt over the Apify MCP server) and a version for n8n.

## Import an n8n workflow

1. In n8n: Workflows → Import from File, pick the JSON.
2. Open the Apify node, add your Apify credential (API token from Apify Console → Settings → Integrations). The node is the official `@apify/n8n-nodes-apify`, available on n8n Cloud and self-hosted.
3. Follow the yellow sticky note in the workflow for the remaining setup.

## Run the same thing from an agent

Agent skills: `npx skills add b2bsearch/skills` ([repository](https://github.com/b2bsearch/skills)). Local MCP server with task-named tools: [b2bsearch/mcp](https://github.com/b2bsearch/mcp).

## Disclosure

The Actors these workflows call are built by the author of this repository. No affiliate or referral parameters are used. Not affiliated with LinkedIn.

## License

MIT
