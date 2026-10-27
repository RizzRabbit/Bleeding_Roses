import { createEventEmitter } from 'utils-event-emitter';
import type { EmitterEventHotKey } from 'components-shared';

export type EmitterEvent =
	| EmitterEventHotKey
	| { type: 'bet' }
	| { type: 'autoBet' }
	| { type: 'resumeBet' };

export const { eventEmitter } = createEventEmitter<EmitterEvent>();
