<script lang="ts">
	import { onMount, type Snippet } from 'svelte';

	import { requestAuthenticate, requestReplay } from 'rgs-requests';
	import { stateUrlDerived, stateBet, stateConfig, stateModal, stateUi } from 'state-shared';
	import { API_AMOUNT_MULTIPLIER } from 'constants-shared/bet';

	type Props = { children: Snippet };

	const props: Props = $props();

	let authenticated = $state(false);

	const authenticate = async () => {
		try {
			const authenticateData = await requestAuthenticate({
				rgsUrl: stateUrlDerived.rgsUrl(),
				sessionID: stateUrlDerived.sessionID(),
				language: stateUrlDerived.lang(),
			});

			// error
			if (authenticateData?.error) throw authenticateData;

			// balance
			if (authenticateData?.balance) {
				// Example of authenticateData.balance
				// {
				// 		"amount": 10000000000000000,
				// 		"currency": "USD"
				// },
				stateBet.currency = authenticateData.balance.currency;
				stateBet.balanceAmount = authenticateData.balance.amount / API_AMOUNT_MULTIPLIER;
			}

			// config
			if (authenticateData?.config) {
				const config = authenticateData.config;
				stateConfig.jurisdiction = config?.jurisdiction;
				const minBet = (config.minBet || 0) / API_AMOUNT_MULTIPLIER;
				const maxBet = (config.maxBet || 0) / API_AMOUNT_MULTIPLIER;
				stateConfig.minBet = minBet;
				stateConfig.maxBet = maxBet;
				stateConfig.stepBet = (config.stepBet || 0) / API_AMOUNT_MULTIPLIER;
				const levels = (config.betLevels || [])
					.map((level: number) => level / API_AMOUNT_MULTIPLIER)
					.filter((level: number) => level >= minBet && (maxBet <= 0 || level <= maxBet));
				stateConfig.betAmountOptions = levels;
				stateConfig.betMenuOptions = levels;
				if (!authenticateData.round?.amount && config.defaultBetLevel) {
					const defaultBet = config.defaultBetLevel / API_AMOUNT_MULTIPLIER;
					stateBet.betAmount = defaultBet;
					stateBet.wageredBetAmount = defaultBet;
				}
			}

			// round
			if (authenticateData?.round) {
				// Example of authenticateData.round 
				// {
				// 	"betID": 62277967,
				// 	"amount": 1000000,
				// 	"payout": 33400000,
				// 	"payoutMultiplier": 33.4,
				// 	"active": true,
				// 	"state": [...],
				// 	"mode": "BONUS",
				// 	"event": null
				// }

				if(authenticateData.round?.state) {
					// @ts-ignore
					stateBet.betToResume =  authenticateData.round;
				}

				if(authenticateData.round?.amount) {
					const betAmountValue =
						authenticateData.round.amount > 0
							? authenticateData.round.amount / API_AMOUNT_MULTIPLIER
							: 0;
					stateBet.betAmount = betAmountValue;
					stateBet.wageredBetAmount = betAmountValue;
				}

				if (authenticateData.round?.mode) {
					stateBet.activeBetModeKey = authenticateData.round.mode;
				};
			}
		} catch (error) {
			stateModal.modal = { name: 'error', error };
		}
	};

	const handleReplay = async () => {
		const fromUrl = stateUrlDerived.currency();
		if (fromUrl) stateBet.currency = fromUrl;
		const betAmountValue = stateUrlDerived.amount() / API_AMOUNT_MULTIPLIER;
		stateBet.betAmount = Number.isFinite(betAmountValue) ? betAmountValue : 0;
		stateBet.wageredBetAmount = stateBet.betAmount;
		if (stateUrlDerived.mode()) stateBet.activeBetModeKey = stateUrlDerived.mode();
		try {
			const data = await requestReplay({
				rgsUrl: stateUrlDerived.rgsUrl(),
				game: stateUrlDerived.game(),
				mode: stateUrlDerived.mode(),
				version: stateUrlDerived.version(),
				event: stateUrlDerived.event(),
			});
			const costMultiplier = Number(data?.costMultiplier) || 1;
			stateBet.replayCostMultiplier = costMultiplier;
			// @ts-ignore replay payload is the round body
			stateBet.betToResume = {
				...data,
				event: '0',
				active: true,
				mode: stateUrlDerived.mode(),
				costMultiplier,
			};
		} catch (error) {
			stateBet.betToResume = null;
			stateModal.modal = { name: 'error', error };
		}
	};

	onMount(async () => {
		if(stateUrlDerived.replay()) {
			stateUi.config.mode = 'replay';
			await handleReplay();
		} else {
			stateUi.config.mode = 'default';
			await authenticate();
		};

		authenticated = true;
	});
</script>

{#if authenticated}
	{@render props.children()}
{/if}
