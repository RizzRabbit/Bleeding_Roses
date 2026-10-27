import type { paths } from './schema';
import { fetcher } from 'utils-fetcher';

/** Add https:// only when the launch param has no scheme. */
export const withScheme = (rgsUrl: string) => {
	const trimmed = rgsUrl.trim().replace(/\/+$/, '');
	if (!trimmed) return '';
	if (/^[a-z][a-z0-9+.-]*:\/\//i.test(trimmed)) return trimmed;
	return `https://${trimmed}`;
};

const readBody = async (response: Response) => {
	const text = await response.text();
	if (!text) return {};
	try {
		return JSON.parse(text) as { error?: string; message?: string };
	} catch {
		return { message: text };
	}
};

const parse = async (response: Response) => {
	if (response.status !== 200) {
		const body = await readBody(response);
		throw {
			error: body.error || `HTTP_${response.status}`,
			message: body.message || `Request failed (${response.status}).`,
			status: response.status,
		};
	}
	const text = await response.text();
	if (!text) return {};
	return JSON.parse(text);
};

export const rgsFetcher = {
	post: async function post<
		T extends keyof paths,
		TResponse = paths[T]['post']['responses'][200]['content']['application/json'],
	>(options: {
		url: T;
		rgsUrl: string;
		variables?: paths[T]['post']['requestBody']['content']['application/json'];
	}): Promise<TResponse> {
		const response = await fetcher({
			method: 'POST',
			variables: options.variables,
			endpoint: `${withScheme(options.rgsUrl)}${options.url}`,
		});
		return (await parse(response)) as TResponse;
	},
	get: async function get<
		T extends keyof paths,
		TResponse = paths[T]['get']['responses'][200]['content']['application/json'],
	>(options: { url: T; rgsUrl: string }): Promise<TResponse> {
		const response = await fetcher({
			method: 'GET',
			endpoint: `${withScheme(options.rgsUrl)}${options.url}`,
		});
		return (await parse(response)) as TResponse;
	},
};
