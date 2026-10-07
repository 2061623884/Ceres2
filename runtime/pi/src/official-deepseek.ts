/** Official api.deepseek.com enables thinking unless the request disables it. */
export function officialDeepSeekSampling(
  baseUrl: string,
  samplingParams?: Record<string, unknown>,
): Record<string, unknown> | undefined {
  if (new URL(baseUrl).hostname !== 'api.deepseek.com') return undefined;
  return { ...samplingParams, thinking: { type: 'disabled' } };
}
