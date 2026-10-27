import { stateSoundDerived } from 'state-shared';

let context: AudioContext | null = null;

const ctx = () => {
	if (!context) context = new AudioContext();
	if (context.state === 'suspended') void context.resume();
	return context;
};

export const unlockSound = () => {
	try {
		ctx();
	} catch {
		context = null;
	}
};

export const tone = (frequency: number, duration = 0.12, type: OscillatorType = 'sine', gain = 0.03) => {
	const volume = stateSoundDerived.volumeMaster();
	if (volume <= 0) return;
	try {
		const audio = ctx();
		const osc = audio.createOscillator();
		const amp = audio.createGain();
		osc.type = type;
		osc.frequency.value = frequency;
		amp.gain.value = gain * volume;
		osc.connect(amp);
		amp.connect(audio.destination);
		osc.start();
		amp.gain.exponentialRampToValueAtTime(0.0001, audio.currentTime + duration);
		osc.stop(audio.currentTime + duration);
	} catch {
		context = null;
	}
};
