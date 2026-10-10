/** Request fields for the explicitly selected official DeepSeek profile. */
export function officialDeepSeekSampling(
  baseUrl: string,
  samplingParams?: Record<string, unknown>,
): Record<string, unknown> | undefined {
  if (new URL(baseUrl).hostname !== 'api.deepseek.com') return undefined;
  return { ...samplingParams, thinking: { type: 'disabled' } };
}
