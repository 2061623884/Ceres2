import { writeFileSync } from 'node:fs';

const originalFetch = globalThis.fetch.bind(globalThis);
const mode = process.env.PI_FETCH_MODE ?? 'observe';
const stats = {
  mode,
  fetch_calls: 0,
  json_string_bodies: 0,
  tool_requests: 0,
  tool_requests_with_response_format: 0,
  response_format_removed: 0,
  tool_choice_required_requests: 0,
  tool_choice_auto_set: 0,
  tool_choice_auto_requests: 0,
  only_top_level_tool_choice_changed: true,
  only_top_level_response_format_removed: true,
  request_body_or_headers_recorded: false,
  credentials_recorded: false,
};
const writeStats = () => {
  const output = process.env.PI_FETCH_DIAGNOSTIC_OUT;
  if (!output) return;
  try {
    writeFileSync(output, `${JSON.stringify(stats, null, 2)}\n`);
  } catch {
    // The observer must not change the provider call outcome.
  }
};
writeStats();

globalThis.fetch = async (input, init) => {
  stats.fetch_calls += 1;
  let nextInit = init;
  const body = init?.body;
  if (typeof body === 'string') {
    stats.json_string_bodies += 1;
    let parsed;
    try {
      parsed = JSON.parse(body);
    } catch {
      writeStats();
      return originalFetch(input, nextInit);
    }
    if (parsed && typeof parsed === 'object' && Array.isArray(parsed.tools)) {
      stats.tool_requests += 1;
      if (parsed.tool_choice === 'required') stats.tool_choice_required_requests += 1;
      if (parsed.tool_choice === 'auto') stats.tool_choice_auto_requests += 1;
      if (mode === 'auto' && parsed.tool_choice === 'required') {
        const changed = { ...parsed, tool_choice: 'auto' };
        stats.tool_choice_auto_set += 1;
        nextInit = { ...init, body: JSON.stringify(changed) };
      }
      if (Object.prototype.hasOwnProperty.call(parsed, 'response_format')) {
        stats.tool_requests_with_response_format += 1;
        if (mode === 'strip') {
          const changed = { ...parsed };
          delete changed.response_format;
          stats.response_format_removed += 1;
          nextInit = { ...init, body: JSON.stringify(changed) };
        }
      }
    }
  }
  writeStats();
  return originalFetch(input, nextInit);
};

process.on('exit', writeStats);
