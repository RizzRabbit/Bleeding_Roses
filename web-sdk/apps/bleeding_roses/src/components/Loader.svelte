<script lang="ts">
	type Props = { progress?: number };
	const props: Props = $props();
</script>

<div class="loader">
	<p>Rizzin Games</p>
	<h1>Bleeding Roses</h1>
	<div class="track"><span style="width: {Math.round((props.progress ?? 0) * 100)}%"></span></div>
</div>

<style>
	.loader {
		position: fixed;
		inset: 0;
		z-index: 40;
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		gap: 14px;
		background: #070308;
		color: #f4e7ea;
		font-family: Cinzel, serif;
		pointer-events: auto;
	}
	p {
		margin: 0;
		letter-spacing: 0.42em;
		font-size: 12px;
		color: #c4a574;
	}
	h1 {
		margin: 0;
		font-family: 'Cinzel Decorative', Cinzel, serif;
		font-weight: 700;
		font-size: 42px;
		letter-spacing: 0.08em;
	}
	.track {
		width: min(280px, 60vw);
		height: 2px;
		background: rgba(244, 231, 234, 0.15);
	}
	.track span {
		display: block;
		height: 100%;
		background: #8d1d32;
	}
</style>
