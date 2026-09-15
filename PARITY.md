# Parity environment

This document describes the tooling built to support **parity testing** — comparing the Money
to Prisoners services against their replacement, built on the organisation's standard tech
stack.

Unlike the `test` environment (whose data we don't control and which we can't reset on
demand), the `parity` environment is fully controlled by these repositories: its database is
wiped and reloaded from a fixed, static set of Django fixtures every day (via a cron job), so
both services are always compared against identical, reproducible data.

This guide gets you from a clean checkout to a passing local Playwright run. It assumes you're
running the whole stack via **Docker Compose from this repository** — that's the default,
recommended way to run everything locally, and what the rest of this document assumes
throughout.

See [`money-to-prisoners-api`'s `PARITY.md`](https://github.com/ministryofjustice/money-to-prisoners-api/blob/main/PARITY.md)
for how the parity fixtures themselves are structured, and how to add more data to them — this
document only covers running/orchestrating the stack as a whole.

## Prerequisites

Clone the full set of Money to Prisoner services as siblings of this one (i.e. all under the
same parent directory, e.g. `~/code/mtp/`).

`money-to-prisoners-common` (this repository) — orchestrates the local Docker Compose stack for
every app (`api`, `cashbook`, `bank-admin`, `noms-ops`, `send-money`, `emails`, `start-page`)
plus a Postgres `db` service. **This is the directory you'll run `docker compose` from** — not
any individual app's own repository, each of which has its own, unrelated `docker-compose.yml`
used only for standalone local development outside Docker Compose.

`hmpps-prisoner-monies-playwright-suite` is the E2E test suite that exercises the running stack.

## 1. Configure environment variables

This repository's `docker-compose.yml` already sets sensible defaults for local dev
(`ENV: local`, `DEBUG: True`, DB connection details, etc.) — no extra config is needed just to
bring the stack up. However, a couple of app features need real secrets to work end-to-end, and
those aren't (and shouldn't be) committed to the repo.

**Where secrets go:** create a `.env` file at the root of this repository (it's already covered
by this repo's `.gitignore`, so it's safe to keep real values in it). Docker Compose
automatically loads this file and loads environment variables for the suite.

**Do not** put these in an app's own `settings/local.py` — this is not used for docker.
Environment variables in `docker-compose.yml` (backed by the `.env` file) are the only
supported way to configure secrets for the Compose stack.

Currently required secrets (values, not names, live in `.env`):

| Variable                            | Service       | Why it's needed                                                                                                                                                                                                                     |
|--------------------------------------|---------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `ZENDESK_API_USERNAME`               | `bank-admin`  | Bank Admin's "Get help" feedback form creates a real Zendesk ticket on submit. Without this (and the two below), the form fails silently and never redirects to `/feedback/success/`, which breaks the Playwright bank-admin get-help spec. |
| `ZENDESK_API_TOKEN`                  | `bank-admin`  | As above.                                                                                                                                                                                                                          |
| `ZENDESK_REQUESTER_ID`               | `bank-admin`  | As above.                                                                                                                                                                                                                          |
| `GOVUK_NOTIFY_CALLBACKS_BEARER_TOKEN`| `emails`      | Authenticates incoming delivery-receipt/inbound-SMS callbacks from GOV.UK Notify (`/notify-callbacks/`). Defaults to `'CHANGE_ME'` if unset, which never matches any bearer token supplied, breaking the Playwright emails-api specs. |
| `GOVUK_PAY_AUTH_TOKEN`               | `send-money`  | Authenticates outgoing requests to the GOV.UK Pay sandbox API when creating a card payment. Without it, the debit-card journey fails at the card details step with "We are experiencing technical problems", breaking the Playwright send-money happy-path spec. |

This repository's `bank-admin`/`emails`/`send-money` services already reference these as
`${VAR_NAME:-}` etc. in their `environment:` blocks, so you only need to supply the values.
Create `money-to-prisoners-common/.env`:

```dotenv
ZENDESK_API_USERNAME=servicedesk@digital.justice.gov.uk
ZENDESK_API_TOKEN=<your-zendesk-api-token>
ZENDESK_REQUESTER_ID=<your-zendesk-requester-id>
GOVUK_NOTIFY_CALLBACKS_BEARER_TOKEN=<your-govuk-notify-callbacks-bearer-token>
GOVUK_PAY_AUTH_TOKEN=<a-govuk-pay-sandbox-auth-token>
```

Ask a teammate or check the team's secrets store for real values if you don't have them.

| Variable                        | Value | Why it's needed                                                                                                                                                                                 |
|----------------------------------|-------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `NOVEMBER_SECOND_CHANGES_LIVE`   | `1`   | Gates whether Bank Admin still shows Access Pay refund file downloads (pre-policy-change behaviour) or the "no refunds needed" message (post-policy-change). `test`/`parity` both set this to `1` (see `config/{test,parity}/env/bank-admin.yml`); without it locally, Bank Admin's downloads page shows refund downloads instead, breaking the Playwright bank-admin downloads-page spec. |

These are read once by Django at process start (`os.environ.get(...)` in each app's
`settings/base.py`), so they can only be changed by recreating the container if changed.

If you add a fixture or feature that needs a new secret in future, follow the same pattern: add
`${VAR_NAME:-}` to the relevant service's `environment:` block in this repository's
`docker-compose.yml` (safe to commit — no real value in it), and document the real value's
variable name (not its value) in the table above.

The Playwright suite itself also needs some of these values (and its own non-secret config) in
its own `hmpps-prisoner-monies-playwright-suite/.env` — see that repo's `.env.example` for the
full list, which follows the same pattern: safe defaults/URLs committed directly, secret values
left blank with a comment on where to find them.

## 2. Start the local stack

From this repository:

```shell
docker compose up
```

This builds/starts every app service (`api`, `cashbook`, `bank-admin`, `noms-ops`, `send-money`,
`emails`, `start-page`) plus the shared Postgres `db` service, all on a common Docker network so
they can reach each other by service name (e.g. `bank-admin` reaches the API at
`http://api:8000`).

Leave this running in its own terminal; run the remaining steps from a second terminal.

## 3. Load the parity data set

```shell
docker compose exec api ./manage.py load_parity_data
```

This wipes the local database and reloads it from the fixed set of fixtures maintained in
`money-to-prisoners-api` (see that repo's `PARITY.md` for how the fixtures/command work) — the
exact same data used in the real `parity` environment. Your local stack now has the same
reference data (groups, prisons, users, OAuth apps/roles) and example prisoners/credits/
payments/disbursements/transactions as `parity`.

Log in to any app using any of the fixed accounts (every password matches its username, e.g.
`bank-admin` / `bank-admin`, or `admin` / `admin` for Django admin).

Re-run this command at any point to reset your local database back to this same known state —
useful whenever your local data has drifted from what you need for a test.

## 4. Run the Playwright suite

From `hmpps-prisoner-monies-playwright-suite`:

```shell
npm test
```

This runs every project defined in `playwright.config.ts` against the URLs in that repo's own
`.env` (e.g. `URL_BANK_ADMIN=http://localhost:8002`), which match the ports this repository's
compose file publishes. To run just one app's tests:

```shell
npm run test:bank-admin
npm run test:send-money
```

## Troubleshooting

- **`service "api" is not running"` / `no such service: api`** — you're not in
  `money-to-prisoners-common` when running `docker compose`. `cd` there first. Also check you're
  using the Compose **service name** `api`, not the container name `mtp-api` shown in Docker
  Desktop (`docker compose ps -a` lists both).
- **A table looks empty even though `load_parity_data` reported success** — you're likely
  connected to the wrong Postgres instance. Each app's *own* `docker-compose.yml` (unrelated to
  the one in this repo) spins up its own standalone Postgres instance published on host port
  `5432`, purely for running that app outside Docker entirely — this repository's `db` service
  does not publish `5432` to the host at all, so a host-based GUI client pointed at
  `localhost:5432` cannot be looking at the data you just loaded. Verify directly instead:
  ```shell
  docker compose exec api ./manage.py shell -c "from disbursement.models import Disbursement; print(Disbursement.objects.count())"
  ```
- **A Playwright spec fails on something that looks unrelated to any fixture data** (e.g. a page
  shows content that assumes a policy/feature flag is on or off) — check whether the app needs a
  plain (non-secret) environment variable set to match `test`/`parity`, before assuming a
  fixture needs changing. `money-to-prisoners-deploy`'s `config/{test,parity}/env/*.yml` files
  are the source of truth for what real `test`/`parity` set; anything found there that this
  repository's local Compose doesn't already set (see the `x-environment` anchor and the
  `NOVEMBER_SECOND_CHANGES_LIVE` example above) should be added there too, not worked around in a
  fixture or the test itself.

## Deploying a branch to parity before it's merged to `main`

Unlike `test` (which auto-deploys on every merge to `main`, via each app's own `deploy` job in
its `build-test-push.yml`), nothing auto-deploys to `parity` — it's not restricted to `main`
either, so you can (and should) test changes there from a feature branch/draft PR before
merging. This is done entirely from the separate `money-to-prisoners-deploy` repository (see its
`PARITY.md`/`docs/deployment.md` for the full picture); the short version, for any given
`<service>` (e.g. `api`, `bank-admin`, `send-money`):

1. Push your branch and wait for its GitHub Actions build to go green (the same
   `build-test-push.yml` run that would eventually deploy to `test` on `main` also builds and
   pushes an image for any branch — it just doesn't auto-deploy anywhere except `main` → `test`).
   You need the whole run green, not just the initial build job, since the image tag is only
   pointed at a multi-arch manifest once `check`/`test` pass too.
2. From `money-to-prisoners-deploy`, with its virtualenv active and `git-crypt unlock` run:
   ```shell
   ./manage.py app deploy parity <service> <branch>.<short-commit-sha>
   ```
   e.g. `./manage.py app deploy parity api parity-env-setup.55ef31a`. This checks the image
   exists in the registry, then patches both the `app-versions` ConfigMap and the `<service>`
   Deployment's image for the `parity` namespace. Branch names are lower-cased in the built tag,
   so match that if your branch has capitals.
3. Confirm what's configured vs actually running:
   ```shell
   ./manage.py app versions parity
   ```
4. **Wait for the rollout to finish** before running any `manage.py` command against the pod —
   patching the Deployment only starts a rolling update, and with several replicas
   `kubectl exec deploy/<service>` can otherwise land on a pod that's still running the old
   image:
   ```shell
   kubectl -n money-to-prisoners-parity rollout status deployment/<service>
   ```
5. Only then run any app-specific management command (e.g. `api`'s `load_parity_data`, as
   described in its own `PARITY.md`) against the pod.

Once your branch is merged to `main`, consider re-running
`./manage.py app deploy parity <service> main.<sha>` (or `latest`) so `parity` doesn't stay
pinned to a stale feature-branch build indefinitely.

