# Web client e2e tests

Playwright tests that drive the real web client (production build) against
the real server image, one browser context per chat user.

## What it covers

| File                      | Scenario                                        |
|---------------------------|-------------------------------------------------|
| `tests/connect.spec.js`   | nick (Pokemon slug), user list (self first), greeting |
| `tests/chat.spec.js`      | two users, plaintext both ways                  |
| `tests/omit.spec.js`      | omit via toggle button: masked / plaintext / badge, then toggle off |
| `tests/leave.spec.js`     | leaver removed from lists, omit selection pruned|
| `tests/reconnect.spec.js` | server restart: offline (list/nick cleared), recovery, new nick |
| `tests/history.spec.js`   | late joiner sees history masked per recipient   |
| `tests/theme.spec.js`     | theme selector: auto follows OS, choice persists, no storage |
| `tests/layout.spec.js`    | 320/390px: header and page do not overflow, users toggle, long list scrolls in its box |

## Layout

| Path             | Role                                                    |
|------------------|---------------------------------------------------------|
| `run`            | build, start stack, run tests, tear down (always)       |
| `compose.yaml`   | project `paranoia-e2e`: server (18000), web (15173)     |
| `lib/user.js`    | `User` helper, one per browser context                  |
| `lib/stack.js`   | health polling, server restart via Podman API socket   |

The web service is `vite preview` on the production build; it proxies
`/ws` and `/healthz` to the server, as the real app expects. Ports differ
from the root `compose.yaml` (8000) so both can run at once.

## Run locally

Needs rootless Podman and `podman-compose`; nothing else on the host.

```sh
cd client/web/e2e
./run                  # everything; exit status is Playwright's
./run -g omit          # extra arguments go to `playwright test`
KEEP_IMAGE=1 ./run     # keep the built server image between runs
```

`./run` builds `paranoia-e2e-server` (`podman build --format docker`),
builds the web bundle in `node:24-alpine`, starts a temporary rootless
Podman API socket (the reconnect test restarts the server through it),
runs Playwright in `mcr.microsoft.com/playwright:v1.63.0-noble` with host
networking, then removes the stack, socket and image (also on failure).
The Playwright image tag must match `@playwright/test` in `package.json`
(override with `PLAYWRIGHT_IMAGE`). Results: list output plus
`test-results/junit.xml` and traces for failures (gitignored).

## GitLab CI

Any runner with Podman and `podman-compose` (shell executor) can run
`./run`. Sample job:

```yaml
web-e2e:
  stage: test
  script:
    - client/web/e2e/run
  artifacts:
    when: always
    reports:
      junit: client/web/e2e/test-results/junit.xml
    paths:
      - client/web/e2e/test-results/
    expire_in: 1 week
```

## Selectors

Tests use `data-testid` hooks in `client/web/src` (`status`, `nick`,
`timeline`, `message`, `sender`, `text`, `omitted`, `notice`, `user-list`,
`omit-bar`) plus ARIA roles (user-list toggle buttons by nick, `aria-pressed`).
