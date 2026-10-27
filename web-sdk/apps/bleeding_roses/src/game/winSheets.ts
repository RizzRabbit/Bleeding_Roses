import { loadClip, releaseFeature } from './art.svelte';

let loading: Promise<void> | null = null;

/** Heart win sheets stay unloaded until a max-win or heart celebration needs them. */
export const preloadWinSheets = () =>
	(loading ??= loadClip('bleeding_heart', 'win').then(() => undefined));

export const releaseWinSheets = async () => {
	await releaseFeature('win');
	loading = null;
};
