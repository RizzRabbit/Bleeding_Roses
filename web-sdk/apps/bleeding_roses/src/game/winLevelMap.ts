export const winLevelMap = {
	1: { level: 1, alias: 'zero', type: 'small', text: null, presentDuration: 0 },
	2: { level: 2, alias: 'standard', type: 'small', text: null, presentDuration: 700 },
	3: { level: 3, alias: 'small', type: 'small', text: null, presentDuration: 900 },
	4: { level: 4, alias: 'nice', type: 'medium', text: 'NICE WIN', presentDuration: 1200 },
	5: { level: 5, alias: 'substantial', type: 'medium', text: 'GREAT WIN', presentDuration: 1500 },
	6: { level: 6, alias: 'big', type: 'big', text: 'BIG WIN', presentDuration: 2800 },
	7: { level: 7, alias: 'super', type: 'big', text: 'SUPER WIN', presentDuration: 3400 },
	8: { level: 8, alias: 'mega', type: 'big', text: 'MEGA WIN', presentDuration: 4000 },
	9: { level: 9, alias: 'epic', type: 'big', text: 'EPIC WIN', presentDuration: 4600 },
	10: { level: 10, alias: 'max', type: 'max', text: 'MAX WIN', presentDuration: 6200 },
} as const;

export type WinLevel = keyof typeof winLevelMap;
export type WinLevelData = (typeof winLevelMap)[WinLevel];
