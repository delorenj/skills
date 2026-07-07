## Model selection procedure

- Open model selector with:
  `/models`

- Select exactly one approved alias:
  - `openrouter/fusion`
  - `openrouter/3-buck-chuck`
  - `openrouter/free-lunch`

## Alias policy

- Use `openrouter/fusion` by default.
- Use `openrouter/3-buck-chuck` for budget-sensitive direct work.
- Use `openrouter/free-lunch` for free, low-risk, or smoke-test work.
- Do not choose direct provider/model routes unless the user explicitly grants an exception.

## Drift check

Run:

```bash
opencode models openrouter --pure
```

Expected output:

```text
openrouter/3-buck-chuck
openrouter/free-lunch
openrouter/fusion
```

If anything else appears, report OpenCode config drift before continuing.
