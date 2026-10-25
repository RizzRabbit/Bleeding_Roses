<script lang="ts">
	import { onMount } from 'svelte';
	import { stateBet, stateUrlDerived } from 'state-shared';

	import { getContext } from '../game/context';
	import { rememberReplay } from '../game/replay';

	const context = getContext();

	onMount(() => {
		if (stateUrlDerived.replay()) {
			rememberReplay();
			return;
		}
		if (stateBet.betToResume?.active) {
			if (stateBet.betToResume.mode) stateBet.activeBetModeKey = stateBet.betToResume.mode;
			context.eventEmitter.broadcast({ type: 'resumeBet' });
		}
	});
</script>
