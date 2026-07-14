# Report format

Produce one JSON object matching `report-schema.json`.

Each idea result must contain:

- The exact request `id` and `path`.
- One allowed result.
- A concise conclusion that explains what is and is not established.
- Evidence entries with a kind, description, and whether the evidence is direct.
- Every material evidence gap.

Useful evidence kinds include `test`, `command`, `browser`, `runtime`, `source`, `artifact`, `telemetry`, `production`, and `inference`. Use a more precise string when helpful.

Example:

```json
{
  "schema_version": 2,
  "context": "Check the storefront routing changes before shipping",
  "revision": "4e31a67",
  "summary": "One idea is supported and one is inconclusive.",
  "ideas": [
    {
      "id": "storefronts-resolve-by-host",
      "path": "ideas/storefronts-resolve-by-host.md",
      "result": "supported",
      "summary": "Host-specific request tests and route inspection support the claim.",
      "evidence": [
        {
          "kind": "test",
          "description": "Tenant routing integration tests passed.",
          "direct": true,
          "command": "bin/rails test test/integration/tenant_routing_test.rb",
          "exit_code": 0
        }
      ],
      "gaps": []
    }
  ]
}
```

The validator computes gating from the request manifest. The agent does not choose whether an idea is blocking.
