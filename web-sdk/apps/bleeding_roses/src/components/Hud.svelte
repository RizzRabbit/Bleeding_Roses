<script lang="ts">
	import { bookEventAmountToCurrencyString, numberToCurrencyString } from 'utils-shared/amount';
	import { stateBet, stateConfig, stateModal, stateSound, stateUrlDerived } from 'state-shared';

	import { canAfford, debitAmount, modeCost, MODE_COST, setPersistent } from '../game/betModes';
	import { DISCLAIMER, HOW_TO_PLAY, PAYTABLE, RULES } from '../game/config';
	import { getContext } from '../game/context';
	import { stageFor } from '../game/layout';
	import { armReplay } from '../game/replay';
	import { reelEngine } from '../game/reels.svelte';
	import { isSocial, modeLabel, t } from '../game/social';
	import { unlockSound } from '../game/sound';
	import { askConfirm, dismissPresentation, stateGame } from '../game/stateGame.svelte';
	import { skipHolds } from '../game/tempo';

	const context = getContext();
	const layoutType = $derived.by(context.stateLayoutDerived.layoutType);
	const frame = $derived.by(context.stateLayoutDerived.mainLayout);
	const stage = $derived(stageFor(layoutType));
	const replay = $derived(stateUrlDerived.replay());
	const idle = $derived.by(context.stateXstateDerived.isIdle);
	const social = $derived(isSocial());
	const jurisdiction = $derived(stateConfig.jurisdiction);

	let replayPlayed = $state(false);
	let shownAmount = $state(0);

	const money = (value: number) => numberToCurrencyString(value);

	const betIndex = () => {
		const levels = stateConfig.betAmountOptions;
		const index = levels.findIndex((level) => Math.abs(level - stateBet.betAmount) < 1e-6);
		return index < 0 ? 0 : index;
	};

	const stepBet = (direction: number) => {
		if (replay) return;
		const levels = stateConfig.betAmountOptions;
		if (!levels.length) return;
		const next = betIndex() + direction;
		if (next < 0 || next >= levels.length) return;
		stateBet.betAmount = levels[next];
		stateBet.wageredBetAmount = levels[next];
	};

	const hurry = () => {
		reelEngine.hurry();
		skipHolds();
		if (stateGame.presentation) dismissPresentation();
	};

	const playReplay = () => {
		if (!idle) {
			hurry();
			return;
		}
		if (!armReplay()) {
			stateModal.modal = { name: 'error', error: { message: t('Replay could not be started.') } };
			return;
		}
		replayPlayed = true;
		context.eventEmitter.broadcast({ type: 'resumeBet' });
	};

	const spin = () => {
		unlockSound();
		if (replay) {
			playReplay();
			return;
		}
		if (!idle) {
			hurry();
			return;
		}
		if (stateGame.panel || stateModal.modal) return;
		if (!stateConfig.betAmountOptions.length) return;
		if (!canAfford()) {
			stateGame.panel = 'funds';
			return;
		}
		context.eventEmitter.broadcast({ type: 'bet' });
	};

	const chooseMode = async (mode: string) => {
		const price = money(stateBet.betAmount * modeCost(mode));
		const accepted = await askConfirm(
			modeLabel(mode),
			t(`This round costs ${price} (${modeCost(mode)}x the base bet).`),
			mode,
		);
		if (!accepted) return;
		if (!canAfford(mode)) {
			stateGame.panel = 'funds';
			return;
		}
		if (mode === 'bloodlust' || mode === 'super_ante_20') setPersistent(mode);
		else stateBet.activeBetModeKey = mode;
		if (mode !== 'bloodlust' && mode !== 'super_ante_20' && mode !== 'base') {
			context.eventEmitter.broadcast({ type: 'bet' });
		}
	};

	const startAuto = (count: number) => {
		if (!context.stateXstateDerived.isIdle()) return;
		if (!canAfford()) {
			stateGame.panel = 'funds';
			return;
		}
		stateGame.panel = null;
		stateBet.autoSpinsCounter = count;
		context.eventEmitter.broadcast({ type: 'autoBet' });
	};

	const toggleSound = () => {
		unlockSound();
		const muted = stateSound.volumeValueMaster <= 0;
		stateSound.volumeValueMaster = muted ? 75 : 0;
		stateSound.volumeValueMusic = stateSound.volumeValueMaster;
		stateSound.volumeValueSoundEffect = stateSound.volumeValueMaster;
	};

	const closePanel = () => {
		if (stateGame.confirm) stateGame.confirm.resolve(false);
		else stateGame.panel = null;
	};

	const replayLabel = () => {
		const base = money(stateBet.betAmount);
		if (stateBet.replayCostMultiplier > 1) {
			const real = money(stateBet.betAmount * stateBet.replayCostMultiplier);
			return t(`BONUS: ${base} · REAL COST: ${real}`);
		}
		return base;
	};

	const modes = Object.keys(MODE_COST);

	$effect(() => {
		const current = stateGame.presentation;
		if (!current) {
			shownAmount = 0;
			return;
		}
		const target = current.amount ?? 0;
		const started = performance.now();
		let frameId = 0;
		const tick = (now: number) => {
			const progress = Math.min(1, (now - started) / Math.max(1, current.duration));
			shownAmount = target * (1 - (1 - progress) ** 2);
			if (progress < 1 && stateGame.presentation === current) frameId = requestAnimationFrame(tick);
			else shownAmount = target;
		};
		frameId = requestAnimationFrame(tick);
		const timer = window.setTimeout(() => {
			if (stateGame.presentation === current) dismissPresentation();
		}, current.duration);
		return () => {
			cancelAnimationFrame(frameId);
			window.clearTimeout(timer);
		};
	});

	context.eventEmitter.subscribeOnMount({
		hotKey: (event) => {
			if (event.key !== 'Space' || event.action !== 'keyDown') return;
			if (stateConfig.jurisdiction.disabledSpacebar) return;
			if (stateGame.panel || stateModal.modal) return;
			if (stateGame.presentation || !context.stateXstateDerived.isIdle()) {
				hurry();
				return;
			}
			spin();
		},
	});
</script>

<div
	class="stage"
	style="left:{frame.x - (frame.width * frame.scale) / 2}px;top:{frame.y - (frame.height * frame.scale) / 2}px;width:{frame.width}px;height:{frame.height}px;transform:scale({frame.scale})"
>
	<img class="grain" src="/grain.png" alt="" />

	{#if stateGame.freeSpin}
		<div class="free">{t(stateGame.tierName)} {stateGame.freeSpin.current} / {stateGame.freeSpin.total}</div>
	{/if}

	{#if !replay && !jurisdiction.disabledBuyFeature}
		{#if social}
			<button
				class="text-plaque"
				style="left:{stage.plaques[0].cx}px;top:{stage.plaques[0].cy}px;width:{stage.plaques[0].width}px"
				onclick={() => (stateGame.panel = 'buy')}
			>
				{t('BONUS')}
				<small>{t('3 BONUSES · FROM 100X')}</small>
			</button>
		{:else}
			<button
				class="plaque"
				style="left:{stage.plaques[0].cx}px;top:{stage.plaques[0].cy}px;width:{stage.plaques[0].width}px"
				onclick={() => (stateGame.panel = 'buy')}
			>
				<img src="/assets/scene/ui/plaque_bonus_buy.png" alt={t('Bonus Buy')} />
				<small>{t('3 BONUSES · FROM 100X')}</small>
			</button>
		{/if}
	{/if}

	{#if !replay}
		<button
			class="plaque"
			style="left:{stage.plaques[1].cx}px;top:{stage.plaques[1].cy}px;width:{stage.plaques[1].width}px"
			onclick={() => (stateGame.panel = 'ante')}
		>
			<img src="/assets/scene/ui/plaque_ante.png" alt={t('Ante')} />
			<small>{t('BLOODLUST 3X · SUPER 20X')}</small>
		</button>
	{/if}

	<div class="tools">
		<button type="button" onclick={toggleSound}>{stateSound.volumeValueMaster > 0 ? t('Sound') : t('Muted')}</button>
		<button type="button" onclick={() => (stateGame.panel = 'info')}>{t('Info')}</button>
		<button type="button" onclick={() => (stateGame.panel = 'menu')}>{t('Menu')}</button>
	</div>

	{#if !replay && !jurisdiction.disabledAutoplay}
		<button
			class="side"
			style={stage.kind === 'portrait' ? 'left:24px;top:1760px' : 'left:1520px;top:940px'}
			onclick={() => (stateBet.autoSpinsCounter > 0 ? (stateBet.autoSpinsCounter = 0) : (stateGame.panel = 'auto'))}
		>
			{stateBet.autoSpinsCounter > 0 ? t('Stop') : t('Autoplay')}
		</button>
	{/if}

	{#if !jurisdiction.disabledTurbo}
		<button
			class="side"
			style={stage.kind === 'portrait' ? 'left:900px;top:1760px' : 'left:1700px;top:940px'}
			onclick={() => (stateBet.isTurbo = !stateBet.isTurbo)}
		>
			{stateBet.isTurbo ? t('Turbo on') : t('Turbo')}
		</button>
	{/if}

	<div class="bar" style="left:{stage.bar.x}px;top:{stage.bar.y}px;width:{stage.bar.width}px;height:{stage.bar.height}px">
		<div class="readout">
			<span>{t('Balance')}</span>
			<strong>{money(stateBet.balanceAmount)}</strong>
		</div>
		<button class="spin" type="button" onclick={spin}>
			{#if replay}
				{idle && replayPlayed ? t('Replay again') : t('Play')}
			{:else if !idle}
				{t('Skip')}
			{:else}
				{t('Spin')}
			{/if}
		</button>
		<div class="readout">
			<span>{t('Win')}</span>
			<strong>{bookEventAmountToCurrencyString(stateBet.winBookEventAmount)}</strong>
		</div>
		<div class="bet">
			{#if replay}
				<em>{replayLabel()}</em>
			{:else}
				<button type="button" onclick={() => stepBet(-1)} aria-label={t('Decrease bet')}>−</button>
				<em>{money(stateBet.betAmount)}</em>
				<button type="button" onclick={() => stepBet(1)} aria-label={t('Increase bet')}>+</button>
				{#if modeCost() > 1}
					<small>{modeLabel(stateBet.activeBetModeKey)} {modeCost()}x · {money(debitAmount())}</small>
				{/if}
			{/if}
		</div>
	</div>

	{#if stateGame.presentation}
		<button class="present" type="button" onclick={() => dismissPresentation()}>
			<strong>{stateGame.presentation.title}</strong>
			{#if stateGame.presentation.subtitle}<span>{stateGame.presentation.subtitle}</span>{/if}
			{#if stateGame.presentation.amount != null}
				<b>{bookEventAmountToCurrencyString(shownAmount)}</b>
			{/if}
		</button>
	{/if}

	{#if stateGame.panel === 'buy'}
		<div class="shade">
			<section>
				<h2>{t('Bonus Buy')}</h2>
				{#each [
					['buy_bleeding', '10 free spins. The board bleeds.'],
					['buy_blood_moon', '12 free spins. Reels lock bloody.'],
					['buy_harvest', "15 free spins. A global multiplier grows."],
					['full_bleed', 'One feature round. Every plain rose bleeds.'],
				] as row (row[0])}
					<button type="button" onclick={() => chooseMode(row[0])}>
						{modeLabel(row[0])}
						<small>{row[1] ? t(row[1]) : ''} · {modeCost(row[0])}x · {money(stateBet.betAmount * modeCost(row[0]))}</small>
					</button>
				{/each}
				<button type="button" class="back" onclick={closePanel}>{t('Back')}</button>
			</section>
		</div>
	{/if}

	{#if stateGame.panel === 'ante'}
		<div class="shade">
			<section>
				<h2>{t('Ante')}</h2>
				<button type="button" onclick={() => chooseMode('bloodlust')}>{modeLabel('bloodlust')} · 3x</button>
				<button type="button" onclick={() => chooseMode('super_ante_20')}>{modeLabel('super_ante_20')} · 20x</button>
				<button type="button" onclick={() => { setPersistent('base'); stateGame.panel = null; }}>{t('Base')}</button>
				<button type="button" class="back" onclick={closePanel}>{t('Back')}</button>
			</section>
		</div>
	{/if}

	{#if stateGame.panel === 'auto'}
		<div class="shade">
			<section>
				<h2>{t('Autoplay')}</h2>
				<p>{t('Confirm how many rounds to play.')}</p>
				{#if !canAfford()}<p class="warn">{t('Insufficient funds')}</p>{/if}
				<div class="row">
					{#each [10, 25, 50, 100] as count (count)}
						<button type="button" disabled={!canAfford()} onclick={() => startAuto(count)}>{count}</button>
					{/each}
				</div>
				<button type="button" class="back" onclick={closePanel}>{t('Back')}</button>
			</section>
		</div>
	{/if}

	{#if stateGame.panel === 'confirm' && stateGame.confirm}
		<div class="shade">
			<section>
				<h2>{stateGame.confirm.title}</h2>
				<p>{stateGame.confirm.body}</p>
				{#if !canAfford(stateGame.confirm.mode)}
					<p class="warn">{t('Insufficient funds')}</p>
				{/if}
				<button
					type="button"
					disabled={!canAfford(stateGame.confirm.mode)}
					onclick={() => stateGame.confirm?.resolve(true)}
				>
					{t('Confirm')}
				</button>
				<button type="button" class="back" onclick={() => stateGame.confirm?.resolve(false)}>{t('Back')}</button>
			</section>
		</div>
	{/if}

	{#if stateGame.panel === 'funds'}
		<div class="shade">
			<section>
				<h2>{t('Insufficient funds')}</h2>
				<p>{t('The balance is lower than this bet.')}</p>
				<button type="button" onclick={closePanel}>{t('Back')}</button>
			</section>
		</div>
	{/if}

	{#if stateGame.panel === 'menu'}
		<div class="shade">
			<section>
				<h2>{t('Menu')}</h2>
				<button type="button" onclick={() => (stateGame.panel = 'info')}>{t('Info')}</button>
				<button type="button" onclick={toggleSound}>{stateSound.volumeValueMaster > 0 ? t('Sound') : t('Muted')}</button>
				<button type="button" class="back" onclick={closePanel}>{t('Back')}</button>
			</section>
		</div>
	{/if}

	{#if stateGame.panel === 'info'}
		<div class="shade">
			<section class="rules">
				<div class="tabs">
					<button type="button" onclick={() => (stateGame.infoTab = 'paytable')}>{t('Paytable')}</button>
					<button type="button" onclick={() => (stateGame.infoTab = 'rules')}>{t('Rules')}</button>
					<button type="button" onclick={() => (stateGame.infoTab = 'how')}>{t('How to play')}</button>
				</div>
				{#if stateGame.infoTab === 'paytable'}
					<h2>{t('Paytable')}</h2>
					<p>{t('Wins are multiples of the base bet. The Bleeding Heart is wild. Bloody roses win 3x the plain rose.')}</p>
					{#each PAYTABLE as row (row.symbol)}
						<p>{t(row.label)} · 3 {row.three}x · 4 {row.four}x · 5 {row.five}x</p>
					{/each}
					<p>{t('The Reaper does not form ways. It triggers the feature.')}</p>
				{:else if stateGame.infoTab === 'how'}
					<h2>{t('How to play')}</h2>
					{#each HOW_TO_PLAY as row (row.control)}
						<p><strong>{t(row.control)}</strong> {t(row.text)}</p>
					{/each}
				{:else}
					<h2>{t('Rules')}</h2>
					{#each RULES as rule (rule.title)}
						<h3>{t(rule.title)}</h3>
						<p>{t(rule.body)}</p>
					{/each}
					<h3>{t('Modes')}</h3>
					{#each modes as mode (mode)}
						<p>{modeLabel(mode)} · {modeCost(mode)}x · RTP 96.00% · {t('max win')} 15000x</p>
					{/each}
					<h3>{t('How to play')}</h3>
					{#each HOW_TO_PLAY as row (row.control)}
						<p><strong>{t(row.control)}</strong> {t(row.text)}</p>
					{/each}
					<p class="legal">{DISCLAIMER}</p>
				{/if}
				<button type="button" class="back" onclick={closePanel}>{t('Back')}</button>
			</section>
		</div>
	{/if}
</div>

<style>
	.stage {
		position: fixed;
		z-index: 5;
		transform-origin: top left;
		pointer-events: none;
		font-family: Cinzel, serif;
		color: #f4e7ea;
	}
	.grain {
		position: absolute;
		inset: 0;
		width: 100%;
		height: 100%;
		object-fit: cover;
		opacity: 0.14;
		mix-blend-mode: overlay;
		pointer-events: none;
	}
	button,
	.shade,
	.present {
		pointer-events: auto;
		touch-action: manipulation;
	}
	button {
		font-family: inherit;
		color: inherit;
		background: rgba(12, 4, 8, 0.78);
		border: 1px solid rgba(196, 165, 116, 0.4);
		cursor: pointer;
	}
	button:disabled {
		opacity: 0.35;
		cursor: default;
	}
	.tools {
		position: absolute;
		top: 28px;
		right: 28px;
		display: flex;
		gap: 8px;
		pointer-events: none;
	}
	.tools button,
	.side {
		pointer-events: auto;
		min-width: 92px;
		min-height: 42px;
		padding: 8px 12px;
		font-size: 16px;
	}
	.side {
		position: absolute;
	}
	.plaque,
	.text-plaque {
		position: absolute;
		transform: translate(-50%, -50%);
		background: transparent;
		border: 0;
		padding: 0;
	}
	.plaque img {
		width: 100%;
		height: auto;
		display: block;
	}
	.plaque small,
	.text-plaque small {
		display: block;
		margin-top: 6px;
		font-size: 13px;
		letter-spacing: 0.08em;
		color: #c4a574;
	}
	.text-plaque {
		min-height: 92px;
		background: rgba(12, 4, 8, 0.82);
		border: 1px solid rgba(196, 165, 116, 0.5);
		font-size: 28px;
		letter-spacing: 0.16em;
	}
	.bar {
		position: absolute;
		display: grid;
		grid-template-columns: 1fr auto 1fr;
		grid-template-rows: 1fr auto;
		align-items: center;
		pointer-events: none;
	}
	.readout,
	.bet {
		pointer-events: none;
		text-align: center;
	}
	.readout span,
	.bet small {
		display: block;
		font-size: 14px;
		letter-spacing: 0.14em;
		color: #c4a574;
	}
	.readout strong,
	.bet em {
		font-style: normal;
		font-size: 26px;
	}
	.bet {
		grid-column: 1 / -1;
		display: flex;
		gap: 12px;
		align-items: center;
		justify-content: center;
		pointer-events: auto;
	}
	.bet button {
		width: 42px;
		height: 42px;
		font-size: 24px;
	}
	.spin {
		width: 124px;
		height: 124px;
		border-radius: 50%;
		background: #6e1220;
		font-family: 'Cinzel Decorative', Cinzel, serif;
		font-size: 22px;
		justify-self: center;
	}
	.free {
		position: absolute;
		left: 50%;
		top: 150px;
		transform: translateX(-50%);
		letter-spacing: 0.16em;
		font-size: 18px;
		color: #c4a574;
	}
	.present {
		position: absolute;
		inset: 0;
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		gap: 12px;
		background: rgba(7, 3, 8, 0.45);
		border: 0;
	}
	.present strong {
		font-family: 'Cinzel Decorative', Cinzel, serif;
		font-size: 72px;
		font-weight: 700;
	}
	.present b {
		font-size: 42px;
		font-weight: 500;
	}
	.shade {
		position: absolute;
		inset: 0;
		display: flex;
		align-items: center;
		justify-content: center;
		background: rgba(0, 0, 0, 0.62);
	}
	section {
		width: min(760px, 86%);
		max-height: 86%;
		overflow: auto;
		padding: 28px;
		background: #14060c;
		border: 1px solid rgba(196, 165, 116, 0.4);
		display: flex;
		flex-direction: column;
		gap: 10px;
	}
	h2,
	h3 {
		font-family: 'Cinzel Decorative', Cinzel, serif;
		margin: 0;
	}
	section button small {
		display: block;
		margin-top: 4px;
		color: #c4a574;
		white-space: normal;
		letter-spacing: 0.04em;
	}
	p {
		margin: 0;
		line-height: 1.4;
		font-size: 16px;
	}
	.legal {
		font-size: 13px;
		color: #c4b8b0;
	}
	.warn {
		color: #e7b4b4;
	}
	.row {
		display: flex;
		gap: 8px;
	}
	.tabs {
		display: flex;
		gap: 8px;
	}
	.back {
		margin-top: 8px;
	}
</style>
