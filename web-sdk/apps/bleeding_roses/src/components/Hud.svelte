<script lang="ts">
	import { bookEventAmountToCurrencyString, numberToCurrencyString } from 'utils-shared/amount';
	import { stateBet, stateConfig, stateModal, stateSound, stateUrlDerived } from 'state-shared';

	import { canAfford, debitAmount, modeCost, setPersistent } from '../game/betModes';
	import { DISCLAIMER, HOW_TO_PLAY, PAYTABLE, RULES } from '../game/config';
	import { STILL_FILES } from '../game/constants';
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
	let mathModes = $state<{ name: string; cost: number; rtp: number; maxWin: number }[]>([]);

	const money = (value: number) => numberToCurrencyString(value);

	const FEATURES = [
		{ mode: 'buy_bleeding', art: '12_bleeding_heart_wild.png', line: '10 free spins. The board bleeds.' },
		{ mode: 'buy_blood_moon', art: '11_bloody_black_rose.png', line: '12 free spins. Reels lock bloody.' },
		{ mode: 'buy_harvest', art: '13_reaper_scatter.png', line: '15 free spins. A global multiplier grows.' },
		{ mode: 'full_bleed', art: '10_bloody_red_rose.png', line: 'One feature round. Every plain rose bleeds.' },
	] as const;

	const ANTES = [
		{ mode: 'bloodlust', line: 'More Reapers. Each round costs 3x the base bet.' },
		{ mode: 'super_ante_20', line: 'The highest feature rate. Each round costs 20x the base bet.' },
	] as const;

	const fitText = (node: HTMLElement, hint: number | string = 26) => {
		let max = typeof hint === 'number' ? hint : 26;
		const resize = () => {
			const limit = node.clientWidth;
			if (!limit) return;
			let size = max;
			node.style.fontSize = `${size}px`;
			while (size > 9 && node.scrollWidth > limit + 1) {
				size -= 1;
				node.style.fontSize = `${size}px`;
			}
		};
		const observer = new ResizeObserver(resize);
		observer.observe(node);
		resize();
		return {
			update(next: number | string) {
				if (typeof next === 'number') max = next;
				resize();
			},
			destroy() {
				observer.disconnect();
			},
		};
	};

	const rtpText = (rtp: number) => `${(rtp <= 1 ? rtp * 100 : rtp).toFixed(2)}%`;
	const costText = (cost: number) => (Number.isInteger(cost) ? `${cost}` : `${cost}`);

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

	const spinLabel = $derived(
		replay ? (idle && replayPlayed ? t('Replay') : t('Play')) : !idle ? t('Skip') : t('Spin'),
	);

	const toolSide = (place: 'auto' | 'turbo') => {
		if (stage.kind === 'portrait') {
			const left = place === 'auto' ? 28 : 960;
			return `left:${left}px;top:${stage.bar.y + 8}px`;
		}
		const left = stage.bar.x + stage.bar.width + (place === 'auto' ? 36 : 130);
		return `left:${left}px;top:${stage.bar.y + 18}px`;
	};

	$effect(() => {
		let cancelled = false;
		fetch('/assets/math/index.json')
			.then((response) => response.json())
			.then((payload: { modes: typeof mathModes }) => {
				if (!cancelled) mathModes = payload.modes ?? [];
			})
			.catch(() => {
				if (!cancelled) mathModes = [];
			});
		return () => {
			cancelled = true;
		};
	});

	$effect(() => {
		const current = stateGame.presentation;
		if (!current) {
			shownAmount = 0;
			return;
		}
		const target = current.amount ?? 0;
		const origin = current.fromAmount ?? 0;
		const started = performance.now();
		let frameId = 0;
		const tick = (now: number) => {
			const progress = Math.min(1, Math.max(0, (now - started) / Math.max(1, current.duration)));
			const eased = 1 - (1 - progress) ** 2;
			shownAmount = Math.round(origin + (target - origin) * eased);
			if (current.driveMeter) stateBet.winBookEventAmount = shownAmount;
			if (progress < 1 && stateGame.presentation === current) frameId = requestAnimationFrame(tick);
			else {
				shownAmount = target;
				if (current.driveMeter) stateBet.winBookEventAmount = Math.round(target);
			}
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
	data-ui="hud"
	style="left:{frame.x - (frame.width * frame.scale) / 2}px;top:{frame.y - (frame.height * frame.scale) / 2}px;width:{frame.width}px;height:{frame.height}px;transform:scale({frame.scale})"
>
	<img class="grain" src="/grain.png" alt="" />

	{#if stateGame.freeSpin}
		<div class="free">{t(stateGame.tierName)} {stateGame.freeSpin.current} / {stateGame.freeSpin.total}</div>
	{/if}

	{#if !replay && !jurisdiction.disabledBuyFeature}
		<button
			class="plaque"
			data-open="buy"
			style="left:{stage.plaques[0].cx}px;top:{stage.plaques[0].cy}px;width:{stage.plaques[0].width}px"
			onclick={() => (stateGame.panel = 'buy')}
		>
			{#if social}
				<span class="oval">{t('BONUS')}</span>
			{:else}
				<img src="/assets/scene/ui/plaque_bonus_buy.png" alt={t('Bonus Buy')} />
			{/if}
			<small class="fit" use:fitText={12}>{t('4 FEATURES · FROM 100X')}</small>
		</button>
	{/if}

	{#if !replay}
		<button
			class="plaque"
			data-open="ante"
			style="left:{stage.plaques[1].cx}px;top:{stage.plaques[1].cy}px;width:{stage.plaques[1].width}px"
			onclick={() => (stateGame.panel = 'ante')}
		>
			<img src="/assets/scene/ui/plaque_ante.png" alt={t('Ante')} />
			<small class="fit" use:fitText={12}>{t('BLOODLUST 3X · SUPER 20X')}</small>
		</button>
	{/if}

	<div class="tools">
		<div class="tool">
			<button class="iron-btn" class:on={stateSound.volumeValueMaster > 0} type="button" aria-label={t('Sound')} onclick={toggleSound}>
				<svg viewBox="0 0 48 48" aria-hidden="true">
					<path d="M10 18h8l10-8v28L18 30h-8z" />
					{#if stateSound.volumeValueMaster > 0}
						<path d="M34 16c4 3 4 13 0 16M38 12c7 5 7 19 0 24" fill="none" />
					{:else}
						<path d="M32 18l10 12M42 18L32 30" fill="none" />
					{/if}
				</svg>
			</button>
			<span class="fit" use:fitText={13}>{stateSound.volumeValueMaster > 0 ? t('Sound') : t('Muted')}</span>
		</div>
		<div class="tool">
			<button class="iron-btn" type="button" aria-label={t('Info')} onclick={() => (stateGame.panel = 'info')}>
				<svg viewBox="0 0 48 48" aria-hidden="true">
					<circle cx="24" cy="24" r="12" fill="none" />
					<path d="M24 22v10M24 16h.1" fill="none" />
				</svg>
			</button>
			<span class="fit" use:fitText={13}>{t('Info')}</span>
		</div>
		<div class="tool">
			<button class="iron-btn" type="button" aria-label={t('Menu')} data-open="menu" onclick={() => (stateGame.panel = 'menu')}>
				<svg viewBox="0 0 48 48" aria-hidden="true">
					<path d="M12 16h24M12 24h24M12 32h24" fill="none" />
				</svg>
			</button>
			<span class="fit" use:fitText={13}>{t('Menu')}</span>
		</div>
	</div>

	{#if !replay && !jurisdiction.disabledAutoplay}
		<div class="tool side" style={toolSide('auto')}>
			<button
				class="iron-btn"
				class:on={stateBet.autoSpinsCounter > 0}
				type="button"
				aria-label={t('Autoplay')}
				data-open="auto"
				onclick={() => (stateBet.autoSpinsCounter > 0 ? (stateBet.autoSpinsCounter = 0) : (stateGame.panel = 'auto'))}
			>
				<svg viewBox="0 0 48 48" aria-hidden="true">
					<path d="M16 24a8 8 0 1 0 2.4-5.7" fill="none" />
					<path d="M16 14v6h6" fill="none" />
				</svg>
			</button>
			<span class="fit" use:fitText={12}>{stateBet.autoSpinsCounter > 0 ? t('Stop') : t('Autoplay')}</span>
		</div>
	{/if}

	{#if !jurisdiction.disabledTurbo}
		<div class="tool side" style={toolSide('turbo')}>
			<button
				class="iron-btn"
				class:on={stateBet.isTurbo}
				type="button"
				aria-label={t('Turbo')}
				onclick={() => (stateBet.isTurbo = !stateBet.isTurbo)}
			>
				<svg viewBox="0 0 48 48" aria-hidden="true">
					<path d="M26 8L14 26h8l-2 14 14-20h-8z" />
				</svg>
			</button>
			<span class="fit" use:fitText={12}>{stateBet.isTurbo ? t('Turbo on') : t('Turbo')}</span>
		</div>
	{/if}

	<div class="bar" style="left:{stage.bar.x}px;top:{stage.bar.y}px;width:{stage.bar.width}px;height:{stage.bar.height}px">
		<div class="iron">
			<div class="readout">
				<span>{t('Balance')}</span>
				<strong class="fit" use:fitText={money(stateBet.balanceAmount)}>{money(stateBet.balanceAmount)}</strong>
			</div>
			<div class="readout">
				<span>{t('Win')}</span>
				<strong class="fit" use:fitText={bookEventAmountToCurrencyString(stateBet.winBookEventAmount)}>
					{bookEventAmountToCurrencyString(stateBet.winBookEventAmount)}
				</strong>
			</div>
			<div class="spin-slot">
				<button class="spin" type="button" data-spin onclick={spin}>
					<svg viewBox="0 0 64 64" aria-hidden="true">
						<g fill="#7a1824">
							<ellipse cx="32" cy="16" rx="6" ry="10" />
							<ellipse cx="32" cy="16" rx="6" ry="10" transform="rotate(72 32 32)" />
							<ellipse cx="32" cy="16" rx="6" ry="10" transform="rotate(144 32 32)" />
							<ellipse cx="32" cy="16" rx="6" ry="10" transform="rotate(216 32 32)" />
							<ellipse cx="32" cy="16" rx="6" ry="10" transform="rotate(288 32 32)" />
						</g>
						<circle cx="32" cy="32" r="4.5" fill="#4a1018" />
					</svg>
					<span class="spin-label">{spinLabel}</span>
				</button>
			</div>
			<div class="bet">
				<span>{replay ? t('Play') : t('Bet')}</span>
				{#if replay}
					<em class="fit" use:fitText={replayLabel()}>{replayLabel()}</em>
				{:else}
					<div class="stepper">
						<button class="iron-btn tiny" type="button" aria-label={t('Decrease bet')} onclick={() => stepBet(-1)}>−</button>
						<em class="fit" use:fitText={money(stateBet.betAmount)}>{money(stateBet.betAmount)}</em>
						<button class="iron-btn tiny" type="button" aria-label={t('Increase bet')} onclick={() => stepBet(1)}>+</button>
					</div>
					{#if modeCost() > 1}
						<small class="fit" use:fitText={11}>{modeLabel(stateBet.activeBetModeKey)} {modeCost()}x · {money(debitAmount())}</small>
					{/if}
				{/if}
			</div>
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
			<section class="gothic wide">
				<h2>{t('Bonus Buy')}</h2>
				<p class="lede">{t('4 features from 100x. The price is the bet times the cost.')}</p>
				<div class="cards">
					{#each FEATURES as card (card.mode)}
						<article class="card">
							<img src={`/assets/symbols/${card.art}`} alt="" />
							<div>
								<h3>{modeLabel(card.mode)}</h3>
								<p>{t(card.line)}</p>
								<p class="price">{modeCost(card.mode)}x · {money(stateBet.betAmount * modeCost(card.mode))}</p>
							</div>
							<button type="button" data-mode={card.mode} onclick={() => chooseMode(card.mode)}>{t('Buy')}</button>
						</article>
					{/each}
				</div>
				<button type="button" class="back" onclick={closePanel}>{t('Back')}</button>
			</section>
		</div>
	{/if}

	{#if stateGame.panel === 'ante'}
		<div class="shade">
			<section class="gothic">
				<h2>{t('Ante')}</h2>
				<p class="lede">{t('An ante stays on until you return to the base game. Each one asks you to confirm the cost.')}</p>
				<div class="cards ante-cards">
					{#each ANTES as card (card.mode)}
						<article class="card" class:on={stateBet.activeBetModeKey === card.mode}>
							<div>
								<h3>{modeLabel(card.mode)}</h3>
								<p>{t(card.line)}</p>
								<p class="price">{modeCost(card.mode)}x · {money(stateBet.betAmount * modeCost(card.mode))}</p>
							</div>
							<button type="button" data-mode={card.mode} onclick={() => chooseMode(card.mode)}>
								{stateBet.activeBetModeKey === card.mode ? t('On') : t('Turn on')}
							</button>
						</article>
					{/each}
				</div>
				<button type="button" onclick={() => { setPersistent('base'); stateGame.panel = null; }}>{t('Base')}</button>
				<button type="button" class="back" onclick={closePanel}>{t('Back')}</button>
			</section>
		</div>
	{/if}

	{#if stateGame.panel === 'auto'}
		<div class="shade">
			<section class="gothic">
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
			<section class="gothic confirm">
				<h2>{stateGame.confirm.title}</h2>
				<p>{stateGame.confirm.body}</p>
				{#if !canAfford(stateGame.confirm.mode)}
					<p class="warn">{t('Insufficient funds')}</p>
				{/if}
				<button
					type="button"
					data-confirm="yes"
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
			<section class="gothic">
				<h2>{t('Insufficient funds')}</h2>
				<p>{t('The balance is lower than this bet.')}</p>
				<button type="button" onclick={closePanel}>{t('Back')}</button>
			</section>
		</div>
	{/if}

	{#if stateGame.panel === 'menu'}
		<div class="shade">
			<section class="gothic">
				<h2>{t('Menu')}</h2>
				<button type="button" onclick={() => (stateGame.panel = 'info')}>{t('Info')}</button>
				<button type="button" onclick={toggleSound}>{stateSound.volumeValueMaster > 0 ? t('Sound') : t('Muted')}</button>
				<button type="button" class="back" onclick={closePanel}>{t('Back')}</button>
			</section>
		</div>
	{/if}

	{#if stateGame.panel === 'info'}
		<div class="shade">
			<section class="gothic rules">
				<div class="tabs">
					<button type="button" data-tab="paytable" class:on={stateGame.infoTab === 'paytable'} onclick={() => (stateGame.infoTab = 'paytable')}>{t('Paytable')}</button>
					<button type="button" data-tab="rules" class:on={stateGame.infoTab === 'rules'} onclick={() => (stateGame.infoTab = 'rules')}>{t('Rules')}</button>
					<button type="button" data-tab="how" class:on={stateGame.infoTab === 'how'} onclick={() => (stateGame.infoTab = 'how')}>{t('How to play')}</button>
				</div>
				{#if stateGame.infoTab === 'paytable'}
					<h2>{t('Paytable')}</h2>
					<p>{t('Wins are multiples of the base bet. The Bleeding Heart is wild. Bloody roses win 3x the plain rose.')}</p>
					{#each PAYTABLE as row (row.symbol)}
						<div class="pay">
							{#if STILL_FILES[row.symbol]}
								<img src={`/assets/symbols/${STILL_FILES[row.symbol]}`} alt="" />
							{/if}
							<div>
								<strong>{t(row.label)}</strong>
								<span>3 {row.three}x · 4 {row.four}x · 5 {row.five}x</span>
							</div>
						</div>
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
					{#if !mathModes.length}
						<p>{t('The mode list could not be read.')}</p>
					{/if}
					{#each mathModes as mode (mode.name)}
						<p>{modeLabel(mode.name)} · {costText(mode.cost)}x · RTP {rtpText(mode.rtp)} · {t('max win')} {mode.maxWin}x</p>
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
		background: #14080c;
		border: 1px solid rgba(196, 165, 116, 0.45);
		cursor: pointer;
	}
	button:disabled {
		opacity: 0.35;
		cursor: default;
	}
	.fit {
		display: block;
		width: 100%;
		overflow: hidden;
		white-space: nowrap;
		text-align: center;
	}
	.tools {
		position: absolute;
		top: 16px;
		right: 22px;
		display: flex;
		gap: 14px;
		pointer-events: none;
	}
	.tool {
		width: 78px;
		display: flex;
		flex-direction: column;
		align-items: stretch;
		gap: 6px;
		pointer-events: none;
	}
	.tool .iron-btn {
		margin: 0 auto;
	}
	.tool span {
		font-size: 12px;
		letter-spacing: 0.12em;
		text-transform: uppercase;
		color: #c4a574;
		pointer-events: none;
	}
	.side {
		position: absolute;
		pointer-events: none;
	}
	.iron-btn {
		pointer-events: auto;
		width: 58px;
		height: 58px;
		border-radius: 50%;
		padding: 0;
		display: grid;
		place-items: center;
		background:
			radial-gradient(circle at 50% 42%, #3a2428 0%, #14080c 72%);
		border: 2px solid #6a4638;
		box-shadow: inset 0 0 0 1px rgba(196, 165, 116, 0.28);
	}
	.iron-btn.on {
		border-color: #c4a574;
		background: radial-gradient(circle at 50% 42%, #4a1820 0%, #1a080c 72%);
	}
	.iron-btn svg {
		width: 30px;
		height: 30px;
		stroke: #f4e7ea;
		stroke-width: 2.4;
		stroke-linecap: round;
		stroke-linejoin: round;
		fill: #f4e7ea;
	}
	.iron-btn.tiny {
		width: 42px;
		height: 42px;
		font-size: 24px;
		line-height: 1;
		color: #f4e7ea;
	}
	.plaque {
		position: absolute;
		transform: translate(-50%, -50%);
		background: transparent;
		border: 0;
		padding: 0;
		width: 250px;
	}
	.plaque img,
	.oval {
		width: 100%;
		height: auto;
		display: block;
	}
	.oval {
		min-height: 92px;
		display: grid;
		place-items: center;
		border-radius: 999px;
		border: 2px solid #6a4638;
		background: radial-gradient(circle at 50% 40%, #3a1820, #12060c 70%);
		font-family: 'Cinzel Decorative', Cinzel, serif;
		letter-spacing: 0.14em;
		font-size: 22px;
	}
	.plaque small {
		margin-top: 6px;
		font-size: 12px;
		letter-spacing: 0.08em;
		color: #c4a574;
	}
	.bar {
		position: absolute;
		pointer-events: none;
	}
	.iron {
		position: absolute;
		left: 0;
		right: 0;
		top: 28px;
		height: 108px;
		display: grid;
		grid-template-columns: 1.15fr 0.9fr 126px 1.35fr;
		gap: 10px;
		align-items: center;
		padding: 0 16px;
		background: linear-gradient(180deg, #241418 0%, #10060a 100%);
		border: 2px solid #5c3a32;
		border-radius: 22px;
		box-shadow: inset 0 0 0 1px rgba(196, 165, 116, 0.3), inset 0 0 0 7px rgba(62, 14, 20, 0.72);
	}
	.iron::before,
	.iron::after {
		content: '';
		position: absolute;
		top: 50%;
		width: 16px;
		height: 16px;
		margin-top: -8px;
		border-radius: 50%;
		background: radial-gradient(circle at 40% 40%, #a12834, #4a0c14 72%);
	}
	.iron::before { left: -9px; }
	.iron::after { right: -9px; }
	.readout,
	.bet {
		min-width: 0;
		height: 74px;
		padding: 8px 8px 6px;
		text-align: center;
		background: rgba(6, 2, 4, 0.62);
		border: 1px solid rgba(196, 165, 116, 0.38);
		border-radius: 12px;
	}
	.readout span,
	.bet span,
	.bet small {
		display: block;
		font-size: 12px;
		letter-spacing: 0.16em;
		text-transform: uppercase;
		color: #c4a574;
	}
	.readout strong,
	.bet em {
		font-style: normal;
		font-size: 24px;
		font-weight: 500;
		color: #f4e7ea;
	}
	.bet {
		pointer-events: auto;
	}
	.stepper {
		display: grid;
		grid-template-columns: 42px 1fr 42px;
		gap: 6px;
		align-items: center;
	}
	.spin-slot {
		position: relative;
		height: 100%;
		pointer-events: none;
	}
	.spin {
		pointer-events: auto;
		position: absolute;
		left: 50%;
		top: -18px;
		width: 126px;
		height: 126px;
		transform: translateX(-50%);
		border-radius: 50%;
		border: 3px solid #c4a574;
		background: radial-gradient(circle at 50% 42%, #7a1824 0%, #3a0a10 68%, #1a0608 100%);
		box-shadow: inset 0 0 0 5px rgba(92, 16, 24, 0.85);
		display: flex;
		flex-direction: column;
		align-items: stretch;
		justify-content: center;
		gap: 0;
		padding: 14px 18px 12px;
	}
	.spin svg {
		width: 46px;
		height: 40px;
		margin: 0 auto;
	}
	.spin-label {
		display: block;
		width: auto;
		margin-top: 1px;
		font-family: 'Cinzel Decorative', Cinzel, serif;
		font-size: 11px;
		line-height: 1;
		letter-spacing: 0.04em;
		text-transform: uppercase;
		text-align: center;
	}
	.free {
		position: absolute;
		left: 50%;
		top: 148px;
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
		background: rgba(7, 3, 8, 0.55);
		border: 0;
	}
	.present strong {
		font-family: 'Cinzel Decorative', Cinzel, serif;
		font-size: 72px;
		font-weight: 700;
		letter-spacing: 0.14em;
	}
	.present span,
	.present b {
		font-family: Cinzel, serif;
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
		background: rgba(0, 0, 0, 0.68);
	}
	.gothic {
		width: min(760px, 90%);
		max-height: 88%;
		overflow: auto;
		padding: 28px 26px;
		background:
			linear-gradient(180deg, rgba(90, 24, 32, 0.18), transparent 80px),
			#12060c;
		border: 1px solid rgba(196, 165, 116, 0.5);
		box-shadow: inset 0 0 0 1px rgba(90, 16, 24, 0.8);
		display: flex;
		flex-direction: column;
		gap: 12px;
	}
	.gothic.wide {
		width: min(980px, 94%);
	}
	h2,
	h3 {
		font-family: 'Cinzel Decorative', Cinzel, serif;
		font-weight: 700;
		letter-spacing: 0.06em;
		color: #f4e7ea;
		margin: 0;
	}
	h2 {
		font-size: 32px;
		text-align: center;
	}
	h3 {
		font-size: 20px;
	}
	p {
		margin: 0;
		line-height: 1.45;
		font-size: 16px;
		color: #f4e7ea;
	}
	.lede,
	.legal {
		color: #c4b8b0;
	}
	.legal {
		font-size: 13px;
	}
	.warn {
		color: #e7b4b4;
	}
	.cards {
		display: grid;
		grid-template-columns: 1fr 1fr;
		gap: 12px;
	}
	.card {
		display: grid;
		grid-template-columns: 84px 1fr;
		gap: 10px;
		align-items: center;
		padding: 12px;
		background: rgba(8, 2, 6, 0.72);
		border: 1px solid rgba(196, 165, 116, 0.32);
	}
	.card.on {
		border-color: #9a3040;
	}
	.card img {
		width: 84px;
		height: 84px;
		object-fit: contain;
	}
	.card h3 {
		font-size: 18px;
	}
	.card p {
		font-size: 14px;
		color: #d9ccc4;
	}
	.price {
		color: #c4a574 !important;
		letter-spacing: 0.04em;
	}
	.card button,
	.gothic > button {
		min-height: 46px;
		padding: 8px 12px;
		font-size: 16px;
		letter-spacing: 0.08em;
		text-transform: uppercase;
	}
	.card button {
		grid-column: 1 / -1;
	}
	.ante-cards .card {
		grid-template-columns: 1fr;
	}
	.row,
	.tabs {
		display: flex;
		gap: 8px;
		flex-wrap: wrap;
	}
	.tabs button,
	.row button {
		min-height: 44px;
		min-width: 72px;
		padding: 8px 12px;
	}
	.tabs button.on {
		border-color: #c4a574;
		color: #c4a574;
	}
	.pay {
		display: grid;
		grid-template-columns: 72px minmax(0, 1fr);
		gap: 18px;
		align-items: center;
		padding: 8px 0;
		border-bottom: 1px solid rgba(154, 48, 64, 0.35);
	}
	.pay img {
		width: 64px;
		height: 64px;
		object-fit: contain;
		justify-self: center;
	}
	.pay strong,
	.pay span {
		display: block;
	}
	.pay span {
		color: #c4a574;
		font-size: 14px;
	}
	.back {
		margin-top: 4px;
	}
	.confirm {
		width: min(560px, 88%);
		text-align: center;
	}
	.confirm p {
		font-size: 20px;
	}
</style>
