## ADDED Requirements

### Requirement: Admin UI is restricted to the configured source allow-list

The system SHALL restrict access to `/admin` and every `/admin/api/*` route to source addresses present in the `ALLOW_ADMIN_FROM` allow-list. The allow-list is derived from the `ALLOW_ADMIN_FROM` environment variable. When `ALLOW_ADMIN_FROM` is blank or unset, the system SHALL default to allowing loopback addresses only (`127.0.0.0/8` and `::1/128`).

The system SHALL evaluate the allow-list against the immediate TCP peer (`request.client.host`) of the incoming request, and SHALL also evaluate the hostname of the `Origin` request header against the same allow-list when the `Origin` header is present. The request SHALL be rejected with HTTP 403 when either check fails. A wildcard allow-list (any network with prefix length 0) SHALL accept any source, whether the peer is an IP or the `Origin` is a hostname, because the operator has explicitly opened `/admin` to every network. The hostname `localhost` SHALL resolve to `127.0.0.1` and `::1` so that `http://localhost:<port>` Origins match a loopback allow-list. IPv4-mapped IPv6 sources (`::ffff:<ipv4>`) SHALL match IPv4 networks, and IPv6 sources with an embedded IPv4 mapping SHALL match the corresponding IPv4 network.

#### Scenario: Loopback request is allowed by default
- **WHEN** `ALLOW_ADMIN_FROM` is blank or unset and a client connects from `127.0.0.1` to `/admin`
- **THEN** the system returns the admin page (HTTP 200) without rejection

#### Scenario: Non-loopback request is rejected by default
- **WHEN** `ALLOW_ADMIN_FROM` is blank or unset and a client connects from `10.0.0.5` to `/admin`
- **THEN** the system returns HTTP 403 with detail "Admin UI is local-only"

#### Scenario: Non-loopback request is allowed when listed
- **WHEN** `ALLOW_ADMIN_FROM=10.0.0.0/24` and a client connects from `10.0.0.5` to `/admin`
- **THEN** the system returns the admin page (HTTP 200) without rejection

#### Scenario: Source outside the listed CIDR is rejected
- **WHEN** `ALLOW_ADMIN_FROM=10.0.0.0/24` and a client connects from `10.1.0.5` to `/admin`
- **THEN** the system returns HTTP 403

#### Scenario: Comma-separated list of entries
- **WHEN** `ALLOW_ADMIN_FROM=127.0.0.1,192.168.1.0/24,::1`
- **THEN** clients from `127.0.0.1`, `192.168.1.10`, and the IPv6 loopback `::1` are all allowed; clients from any other address are rejected

#### Scenario: IPv6 entry matches an IPv6 source
- **WHEN** `ALLOW_ADMIN_FROM=2001:db8::/32` and a client connects from `2001:db8::1` to `/admin`
- **THEN** the system returns the admin page (HTTP 200) without rejection

#### Scenario: Wildcard literal `*` accepts any source
- **WHEN** `ALLOW_ADMIN_FROM=*`
- **THEN** any source address (IPv4 or IPv6) reaches `/admin` and the admin API

#### Scenario: Wildcard CIDR `0.0.0.0/0` accepts any IPv4 source
- **WHEN** `ALLOW_ADMIN_FROM=0.0.0.0/0` and a client connects from `8.8.8.8` to `/admin`
- **THEN** the system returns the admin page (HTTP 200) without rejection

#### Scenario: Origin header is checked against the same allow-list
- **WHEN** `ALLOW_ADMIN_FROM=10.0.0.0/24` and a client connects from `127.0.0.1` but the `Origin` header is `https://evil.example.com`
- **THEN** the system returns HTTP 403 because the `Origin` hostname is not in the allow-list

#### Scenario: Blank Origin header is treated as loopback-allowed under default policy
- **WHEN** `ALLOW_ADMIN_FROM` is blank or unset, the peer is loopback, and the `Origin` header is absent
- **THEN** the system allows the request (no `Origin` is not, by itself, a rejection reason)

#### Scenario: `localhost` Origin matches a loopback allow-list
- **WHEN** `ALLOW_ADMIN_FROM` is blank or unset (loopback default) and the peer is loopback with `Origin: http://localhost:8082`
- **THEN** the system allows the request (`localhost` resolves to `127.0.0.1` / `::1`)

#### Scenario: Wildcard allow-list accepts a non-IP Origin hostname
- **WHEN** `ALLOW_ADMIN_FROM=*` (or `0.0.0.0`) and the `Origin` header is a Tailscale MagicDNS hostname that is not parseable as a literal IP
- **THEN** the system allows the request (a wildcard opens `/admin` to every source, including hostnames)

#### Scenario: IPv4-mapped IPv6 source matches an IPv4 entry
- **WHEN** `ALLOW_ADMIN_FROM=10.0.0.0/24` and the peer is `::ffff:10.0.0.5`
- **THEN** the system allows the request (the IPv4-mapped IPv6 address matches the IPv4 network)

#### Scenario: Admin API routes use the same guard
- **WHEN** `ALLOW_ADMIN_FROM` is blank or unset and a client connects from `10.0.0.5` to `POST /admin/api/config/apply`
- **THEN** the system returns HTTP 403 (the same guard as the page route)

### Requirement: The allow-list is validated at server startup

The system SHALL parse `ALLOW_ADMIN_FROM` into a normalized set of `ipaddress.IPv4Network` / `ipaddress.IPv6Network` objects at `Settings` load time. Malformed entries (unparseable IPs, invalid CIDR widths, unknown wildcard tokens) MUST cause `Settings` construction to raise `ValueError` and prevent the server from starting. Whitespace surrounding entries SHALL be trimmed; empty entries (e.g. `,,`) SHALL be ignored.

#### Scenario: Valid CIDR and address entries are accepted
- **WHEN** `ALLOW_ADMIN_FROM=127.0.0.1, 10.0.0.0/24 , ::1` is loaded
- **THEN** the server starts and the allow-list contains `127.0.0.1/32`, `10.0.0.0/24`, and `::1/128`

#### Scenario: Malformed entry prevents startup
- **WHEN** `ALLOW_ADMIN_FROM=10.0.0.999` is loaded
- **THEN** `Settings` construction raises `ValueError` referencing the offending entry and the server does not start

#### Scenario: Unknown wildcard token is rejected
- **WHEN** `ALLOW_ADMIN_FROM=any` is loaded
- **THEN** `Settings` construction raises `ValueError`

#### Scenario: `*`, `0.0.0.0`, and `::` are accepted as wildcards
- **WHEN** any of `*`, `0.0.0.0`, `::` is present in `ALLOW_ADMIN_FROM`
- **THEN** the allow-list contains `0.0.0.0/0` (and `::/0` for `::`) and the server starts

### Requirement: The allow-list is editable through the Admin UI

The system SHALL register `ALLOW_ADMIN_FROM` in the admin configuration manifest as a `ConfigFieldSpec` so that the value is loadable, validatable, and applicable through the existing admin `/admin/api/config/apply` pipeline, with the same restart-required behavior as `HOST` and `PORT`. The field SHALL be classified with `restart_required=True`.

#### Scenario: ALLOW_ADMIN_FROM appears in the admin config response
- **WHEN** the admin UI calls `GET /admin/api/config`
- **THEN** the response includes a `ALLOW_ADMIN_FROM` field entry with key `ALLOW_ADMIN_FROM` and the current value

#### Scenario: Valid update is applied and persisted
- **WHEN** the admin UI submits `POST /admin/api/config/apply` with `{"ALLOW_ADMIN_FROM": "10.0.0.0/24"}` and the entry is valid
- **THEN** the system writes the value to the managed env file, returns a successful response, and the response includes `restart_required: true` for this field

#### Scenario: Invalid update is rejected
- **WHEN** the admin UI submits `POST /admin/api/config/validate` with `{"ALLOW_ADMIN_FROM": "10.0.0.999"}`
- **THEN** the system returns `valid: false` with a validation error referencing the malformed entry

### Requirement: `HOST` and `PORT` are first-class env-controlled bind settings

The system SHALL declare `host` and `port` on `Settings` with explicit `validation_alias` values `HOST` and `PORT` respectively, and the `server.py` entry point SHALL bind Uvicorn to the resulting values. The `HOST` and `PORT` keys SHALL be documented in `.env.example`.

#### Scenario: Uvicorn binds to the configured host and port
- **WHEN** the server is started with `HOST=127.0.0.1 PORT=9000`
- **THEN** Uvicorn binds to `127.0.0.1:9000` and refuses connections on any other address or port

#### Scenario: `.env.example` documents HOST, PORT, and ALLOW_ADMIN_FROM
- **WHEN** a user inspects `.env.example`
- **THEN** the file contains `HOST`, `PORT`, and `ALLOW_ADMIN_FROM` keys with example values and a security note for the wildcard forms

### Requirement: The effective allow-list is surfaced in admin_status

The system SHALL include the configured `ALLOW_ADMIN_FROM` string and the parsed `allow_admin_from_networks` (as a sorted list of network strings) in the `admin_status` response, so the Admin UI can display the effective allow-list.

#### Scenario: admin_status exposes the allow-list
- **WHEN** `GET /admin/api/status` (or the `admin_status` route) is called with `ALLOW_ADMIN_FROM=10.0.0.0/24`
- **THEN** the response includes `"allow_admin_from": "10.0.0.0/24"` and `"allow_admin_from_networks": ["10.0.0.0/24"]`

#### Scenario: admin_status exposes the loopback default
- **WHEN** `ALLOW_ADMIN_FROM` is blank or unset
- **THEN** the response includes `"allow_admin_from": ""` and `"allow_admin_from_networks"` containing `127.0.0.0/8` and `::1/128`
