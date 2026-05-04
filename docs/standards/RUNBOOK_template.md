# RUNBOOK TEMPLATE — Canonical Standard

## 1. Purpose
Operate the <system/environment>.

Covers:
- start
- stop
- validation
- reset
- basic recovery

---

## 2. Preconditions

### Base Runtime
- <e.g. Docker running>
- <e.g. docker compose available>
- <e.g. .env present>

### Optional Runtimes (if applicable)
- <e.g. kubectl working>
- <e.g. cluster available>

---

## 3. Start — Base
```bash
<command>
```

---

## 4. Start — Overlay (Optional)
```bash
<command>
```

Overlays modify the base runtime (e.g. additional services or configuration).

---

## 5. Stop — Base
```bash
<command>
```

---

## 6. Reset — Base
```bash
<command>
```

Optional deeper clean:
```bash
<command>
```

---

## 7. Start — Alternate Runtime (Optional)
```bash
<command>
```

---

## 8. Stop — Alternate Runtime (Optional)
```bash
<command>
```

---

## 9. Verify Successful Start

### Base Runtime
```bash
<status command>
```

### Alternate Runtime (if applicable)
```bash
<status command>
```

Expected:
- All core services running
- No restart loops or failures

---

## 10. Service Endpoints (local)

- <service>: <url>
- <service>: <url>

---

## 11. Logs & Diagnostics

### Base Runtime
```bash
<log command>
```

### Alternate Runtime
```bash
<log command>
```

---

## 12. Common Failure Modes

**<Failure name>**
- Cause: <short>
- Fix: <command or action>

**<Failure name>**
- Cause: <short>
- Fix: <command or action>

(Add only real, observed failures)

---

## 13. Command Reference
```bash
<start command>
<stop command>
<reset command>
<status command>
<log command>
```

---

# Enforcement Rules

1. No explanation (no architecture, no theory)
2. One-line descriptions only
3. Command-first design
4. Failure-driven content
5. No duplication
