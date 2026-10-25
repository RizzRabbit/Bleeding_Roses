<script lang="ts">
	import { BaseSprite, Container, Graphics, Text } from 'pixi-svelte';

	import { artState } from '../game/art.svelte';
	import { getContext } from '../game/context';
	import { reelView } from '../game/reels.svelte';
	import { stateGame } from '../game/stateGame.svelte';
	import SymbolView from './SymbolView.svelte';

	const context = getContext();
	const portrait = $derived(context.stateLayoutDerived.layoutType() === 'portrait');
	const plan = $derived(
		portrait ? artState.frameMeta?.mockup_portrait_1080 : artState.frameMeta?.mockup_1920,
	);
	const windowRect = $derived(artState.frameMeta?.window ?? { x: 141, y: 134, w: 900, h: 720 });
	const cell = 180;

	const symbolX = (reel: number) => windowRect.x + reel * cell + cell / 2;
	const symbolY = (slot: number) => windowRect.y + slot * cell + cell / 2;
</script>

{#if artState.frame && plan}
	<BaseSprite texture={artState.frame} x={plan.frame_pos[0]} y={plan.frame_pos[1]} scale={plan.scale} />
	<Container x={plan.frame_pos[0]} y={plan.frame_pos[1]} scale={plan.scale}>
		<Container>
			<Graphics
				isMask
				draw={(graphics) => {
					graphics.rect(windowRect.x, windowRect.y, windowRect.w, windowRect.h).fill({ color: 0xffffff });
				}}
			/>
		{#if reelView.active}
			{#each reelView.reels as reel, reelIndex (reelIndex)}
				{#each reel.symbols as name, slot (`${reelIndex}-${slot}`)}
					<SymbolView
						{name}
						anim="still"
						token={0}
						reel={reelIndex}
						row={slot}
						x={symbolX(reelIndex)}
						y={windowRect.y + (slot - reel.scroll) * cell + cell / 2}
					/>
				{/each}
			{/each}
		{:else}
			{#each stateGame.cells as reel, reelIndex (reelIndex)}
				{#each reel as symbol, row (`${reelIndex}-${row}-${symbol.token}`)}
					<SymbolView
						name={symbol.name}
						anim={symbol.anim}
						token={symbol.token}
						reel={reelIndex}
						{row}
						x={symbolX(reelIndex)}
						y={symbolY(row)}
						glow={stateGame.glow?.reel === reelIndex && stateGame.glow?.row === row}
					/>
				{/each}
			{/each}
		{/if}
		</Container>
		{#each stateGame.reelMultipliers as multiplier, reelIndex (reelIndex)}
			{#if multiplier > 1}
				<Text
					text={`${multiplier}x`}
					x={symbolX(reelIndex)}
					y={windowRect.y - 18}
					anchor={{ x: 0.5, y: 0.5 }}
					style={{ fill: stateGame.stickyReels.includes(reelIndex) ? 0xc4a574 : 0xf4e7ea, fontSize: 28, fontFamily: 'Cinzel' }}
				/>
			{/if}
		{/each}
		{#if stateGame.globalMult > 1}
			<Text
				text={`${stateGame.globalMult}x`}
				x={windowRect.x + windowRect.w / 2}
				y={windowRect.y + windowRect.h + 28}
				anchor={{ x: 0.5, y: 0.5 }}
				style={{ fill: 0xc4a574, fontSize: 32, fontFamily: 'Cinzel' }}
			/>
		{/if}
	</Container>
{/if}
