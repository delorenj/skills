---
name: bloodbank-n8n-event-driven-workflows
description: Use this skill when working on any event driven n8n workflow that subscribes to or publishes 33GOD Bloodbank events. This skill will ensure a standard convention is adhered to across all event-driven workflows, and modularity is maximized for robust and rapid expansion.
version: 1.0.0
---

// n8n Code Node

// 1. Paste the generated JSON Schema here or load it
const schema = {
// ... contents of your bloodbank-event-schema.json ...
};

// You need to add 'ajv' as an external module for your n8n instance
const Ajv = require('ajv');
const ajv = new Ajv();
const validate = ajv.compile(schema);

// Your existing logic to build the envelope
const envelope = createEnvelope('github.pr.review', payload, source);

// 2. Validate the envelope before returning
const isValid = validate(envelope);

if (!isValid) {
// If it fails, throw an error to stop the workflow
// and see what went wrong.
throw new Error("Schema validation failed: " + JSON.stringify(validate.errors));
}

// 3. Return the validated envelope
return [{ json: envelope }];
