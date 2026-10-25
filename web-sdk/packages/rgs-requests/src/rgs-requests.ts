import { API_AMOUNT_MULTIPLIER } from 'constants-shared/bet';
import { rgsFetcher } from 'rgs-fetcher';

export * from './types';

type AuthenticateOptions = { sessionID: string; rgsUrl: string; language: string };
type BetOptions = {
	sessionID: string;
	currency: string;
	amount: number;
	mode: string;
	rgsUrl: string;
};
type EndRoundOptions = { sessionID: string; rgsUrl: string };
type EndEventOptions = { sessionID: string; eventIndex: number; rgsUrl: string };

export type DevRgsHandler = {
	authenticate: (options: AuthenticateOptions) => Promise<unknown>;
	bet: (options: BetOptions) => Promise<unknown>;
	endRound: (options: EndRoundOptions) => Promise<unknown>;
	endEvent: (options: EndEventOptions) => Promise<unknown>;
};

let devRgs: DevRgsHandler | null = null;

/** Local book replay used when the game is opened without an RGS url. */
export const registerDevRgs = (handler: DevRgsHandler | null) => {
	devRgs = handler;
};

const isDevBuild = () => Boolean((import.meta as { env?: { DEV?: boolean } }).env?.DEV);

const localDev = (rgsUrl: string) => isDevBuild() && !rgsUrl && devRgs;

const requireRgs = (rgsUrl: string) => {
	if (!rgsUrl) {
		throw {
			error: 'Missing rgs_url',
			message: 'This game must be launched with an rgs_url.',
		};
	}
};

export const requestAuthenticate = async (options: AuthenticateOptions) => {
	if (localDev(options.rgsUrl)) return devRgs!.authenticate(options);
	requireRgs(options.rgsUrl);
	const data = await rgsFetcher.post({
		rgsUrl: options.rgsUrl,
		url: '/wallet/authenticate',
		variables: {
			sessionID: options.sessionID,
			language: options.language,
		},
	});

	return data;
};

export const requestEndRound = async (options: EndRoundOptions) => {
	if (localDev(options.rgsUrl)) return devRgs!.endRound(options);
	requireRgs(options.rgsUrl);
	const data = await rgsFetcher.post({
		rgsUrl: options.rgsUrl,
		url: '/wallet/end-round',
		variables: {
			sessionID: options.sessionID,
		},
	});

	return data;
};

export const requestEndEvent = async (options: EndEventOptions) => {
	if (localDev(options.rgsUrl)) return devRgs!.endEvent(options);
	requireRgs(options.rgsUrl);
	const data = await rgsFetcher.post({
		rgsUrl: options.rgsUrl,
		url: '/bet/event',
		variables: {
			sessionID: options.sessionID,
			event: `${options.eventIndex}`,
		},
	});

	return data;
};

export const requestBet = async (options: BetOptions) => {
	if (localDev(options.rgsUrl)) return devRgs!.bet(options);
	requireRgs(options.rgsUrl);
	const data = await rgsFetcher.post({
		rgsUrl: options.rgsUrl,
		url: '/wallet/play',
		variables: {
			mode: options.mode,
			currency: options.currency,
			sessionID: options.sessionID,
			amount: Math.round(options.amount * API_AMOUNT_MULTIPLIER),
		},
	});

	return data;
};

export const requestReplay = async (options: {
	game: string;
	version: string;
	mode: string;
	event: string;
	rgsUrl: string;
}) => {
	requireRgs(options.rgsUrl);
	const data = await rgsFetcher.get({
		rgsUrl: options.rgsUrl,
		// @ts-ignore TODO: update the schema.ts
		url: `/bet/replay/${options.game}/${options.version}/${options.mode}/${options.event}`,
	});

	return data;
}