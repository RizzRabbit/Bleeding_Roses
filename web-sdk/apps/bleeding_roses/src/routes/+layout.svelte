<script lang="ts">
	import { onMount, type Snippet } from 'svelte';
	import Authenticate from 'components-shared/src/components/Authenticate.svelte';
	import { stateModal } from 'state-shared';

	import '@fontsource/cinzel/500.css';
	import '@fontsource/cinzel/700.css';
	import '@fontsource/cinzel-decorative/700.css';

	import ErrorModal from '../components/ErrorModal.svelte';
	import Game from '../components/Game.svelte';
	import Loader from '../components/Loader.svelte';
	import { applyBetModes } from '../game/betModes';
	import { boot } from '../game/boot.svelte';
	import { setContext } from '../game/context';

	type Props = { children: Snippet };

	const props: Props = $props();

	setContext();
	applyBetModes();

	let gate = $state(!import.meta.env.DEV);

	onMount(async () => {
		if (import.meta.env.DEV) {
			const module = await import('../game/devRgs');
			module.installDevBooks();
			gate = true;
		}
		void document.fonts?.load('700 32px Cinzel');
		void document.fonts?.load('700 48px "Cinzel Decorative"');
	});
</script>

{#if gate}
	<Authenticate>
		<Game />
	</Authenticate>
{/if}

{#if stateModal.modal?.name !== 'error' && !boot.ready}
	<Loader progress={boot.progress} />
{/if}

<ErrorModal />

{@render props.children()}
