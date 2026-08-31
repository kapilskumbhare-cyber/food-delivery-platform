# Food Delivery Platform

Portfolio project: application code + logic is built out fully here.
DevOps lifecycle (Docker, CI/CD, Kubernetes, AWS, Terraform, monitoring)
is handled separately, by design — see "Split of responsibility" below.

## Architecture (current)

Modular monolith. One Flask app, one MySQL database, cleanly separated
modules so it can later be split into real services (Order and Payment
are the natural first candidates) without a rewrite.

```
Browser (Bootstrap + vanilla JS)
        │
        ▼
   Flask app (this repo)
   ├── /api/auth        → register, login (JWT)
   ├── /api/restaurants → browse, menu CRUD
   ├── /api/orders      → cart → order → status lifecycle
   ├── /api/orders/.../pay → simulated payment
   ├── /api/admin       → users, restaurants, stats
   └── / , /restaurants, /orders, ... → server-rendered pages
        │
        ▼
      MySQL
```

## Roles and what each can do

| Role | Capabilities |
|---|---|
| Customer | register/login, browse & search restaurants, view menu, cart, place order, pay (simulated), track order, cancel unpaid/failed orders |
| Restaurant | register a restaurant profile, manage menu (add/edit/remove), view incoming paid orders, accept/reject, advance status (preparing to ready to delivered) |
| Admin | list/disable users, list/disable restaurants, view system stats (order counts by status) |

## Order lifecycle

```
ORDER PLACED (implicit) -> PAYMENT_PENDING
        |
        v
   PAYMENT_SUCCESS -------> PAYMENT_FAILED
        |                        |
        v                        v
 RESTAURANT_ACCEPTED      (customer cancels)
        |                        |
        v                        v
   PREPARING                CANCELLED
        |
        v
     READY
        |
        v
   DELIVERED
```

`ORDER_REJECTED` is also reachable from `PAYMENT_SUCCESS` if the restaurant declines.
Status transitions are enforced server-side in `app/order/routes.py` (`NEXT_STATUS` map)
so a restaurant cannot skip straight from `PAYMENT_SUCCESS` to `DELIVERED`.

## Payment simulation

`POST /api/orders/<id>/pay` — no real gateway. Succeeds ~90% of the time by
default so you have a genuine failure path to test (cancel then retry flow).
Pass `{"force_result": "FAILED"}` in the body to force a failure for testing.

## Project structure

```
food-delivery-platform/
├── app/
│   ├── __init__.py        # app factory, blueprint registration, /health
│   ├── config.py          # all config from environment variables
│   ├── models.py          # User, Restaurant, MenuItem, Order, OrderItem, Payment
│   ├── decorators.py      # role_required() for role-based access control
│   ├── auth/routes.py     # register, login
│   ├── restaurant/routes.py
│   ├── order/routes.py
│   ├── payment/routes.py
│   ├── admin/routes.py
│   ├── frontend/views.py  # renders the HTML pages
│   ├── templates/         # Jinja2 + Bootstrap pages
│   └── static/            # css/js
├── requirements.txt
├── run.py
└── .env.example
```

## Run it locally

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

cp .env.example .env   # then edit values
# make sure a MySQL instance is reachable at the host/port in .env

python run.py
```

Open `http://localhost:5000`. Register as a restaurant owner in one browser
tab, set up a restaurant and menu at `/my-restaurant`, then register as a
customer in another tab (or incognito) to browse, order, and pay.

### API smoke test (no browser)

```bash
curl -X POST http://localhost:5000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"name":"Kapil","email":"kapil@example.com","password":"test1234","role":"customer"}'

curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"kapil@example.com","password":"test1234"}'
```

## Split of responsibility

- **Application code (this repo)** — built out fully: auth, all three
  roles, full order lifecycle, simulated payment, and a working UI.
- **DevOps lifecycle** — Docker, Docker Compose/networking, CI/CD,
  Kubernetes, AWS, Terraform, monitoring/logging — done separately, by
  design, since that is the actual skill being practiced here.

## Why these choices

- **MySQL** — same as the fitness-tracker-cicd project, so existing
  Docker/CI-CD patterns for the DB container transfer directly.
- **Server-rendered templates + vanilla JS, not React** — no build step,
  no Node toolchain to containerize alongside the API. One Dockerfile,
  one image, one thing to deploy — the app stays a single deployable
  unit until there is a reason to split it.
- **Config via env vars only** — `SECRET_KEY`, `JWT_SECRET_KEY`, and DB
  credentials are the values that become a K8s `Secret`; everything else
  (`DB_HOST`, `DB_NAME`, etc.) is a `ConfigMap` candidate.
- **`/health` endpoint exists from day one** — this is what liveness/readiness
  probes will hit once there is a Deployment manifest.

## Known gaps (intentional, for now)

- No image uploads for restaurants/menu items (text-only).
- No pagination on restaurant/order lists — fine at demo scale, would need
  it at real scale.
- Payment is entirely simulated — no PCI/webhook concerns to deal with.
- Notifications (order confirmed, out for delivery, etc.) are not built —
  optional next module, not required for the DevOps lifecycle goals.
