import { createLayout } from 'utils-layout';

import { mainSizesMap } from './layout';

export const { stateLayout, stateLayoutDerived } = createLayout({
	backgroundRatio: {
		normal: 1920 / 1080,
		portrait: 1080 / 1920,
	},
	mainSizesMap,
});
