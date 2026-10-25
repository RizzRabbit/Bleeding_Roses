<script lang="ts">
	import { stateModal } from 'state-shared';

	import { t } from '../game/social';

	const message = $derived.by(() => {
		if (stateModal.modal?.name !== 'error') return '';
		const error = stateModal.modal.error as { message?: string; error?: string } | string | undefined;
		if (!error) return t('The game could not reach the server.');
		if (typeof error === 'string') return t(error);
		return t(String(error.message || error.error || 'The game could not reach the server.'));
	});

	const close = () => {
		stateModal.modal = null;
	};
</script>

{#if stateModal.modal?.name === 'error'}
	<div class="shade">
		<div class="card">
			<h2>{t('Something went wrong')}</h2>
			<p>{message}</p>
			<button type="button" onclick={close}>{t('Close')}</button>
		</div>
	</div>
{/if}

<style>
	.shade {
		position: fixed;
		inset: 0;
		z-index: 80;
		display: flex;
		align-items: center;
		justify-content: center;
		background: rgba(0, 0, 0, 0.72);
		pointer-events: auto;
	}
	.card {
		width: min(440px, calc(100vw - 32px));
		padding: 28px 24px;
		background: #14060c;
		color: #f4e7ea;
		border: 1px solid rgba(196, 165, 116, 0.45);
		font-family: Cinzel, serif;
		text-align: center;
	}
	h2 {
		margin: 0 0 12px;
		font-family: 'Cinzel Decorative', Cinzel, serif;
		font-size: 22px;
	}
	p {
		margin: 0 0 18px;
		line-height: 1.45;
		font-size: 15px;
	}
	button {
		font-family: inherit;
		background: #6e1220;
		color: #f4e7ea;
		border: 0;
		padding: 10px 22px;
		cursor: pointer;
		touch-action: manipulation;
	}
</style>
