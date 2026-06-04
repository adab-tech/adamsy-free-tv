# GitHub repository secrets

Repository: [adab-tech/adamsy-free-tv](https://github.com/adab-tech/adamsy-free-tv)

## Actions (CI / deploy)

| Secret | Required | Purpose |
|--------|----------|---------|
| `ADAMSY_ADMIN_TOKEN` | Optional | Protects `/admin/refresh` on API and Vercel |
| `VERCEL_TOKEN` | For deploy workflow | Vercel personal token |
| `VERCEL_ORG_ID` | For deploy workflow | From `.vercel/project.json` after `vercel link` |
| `VERCEL_PROJECT_ID` | For deploy workflow | From `.vercel/project.json` |

CI smoke tests do **not** require secrets. The Vercel workflow runs only when `VERCEL_TOKEN` is set.

**Vercel project env (mirror in Vercel dashboard):** `ADAMSY_ADMIN_TOKEN`

```powershell
gh secret set ADAMSY_ADMIN_TOKEN --repo adab-tech/adamsy-free-tv --body "choose-a-long-random-token"
gh secret set VERCEL_TOKEN --repo adab-tech/adamsy-free-tv --body "YOUR_VERCEL_TOKEN"
```
