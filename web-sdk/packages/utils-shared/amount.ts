import { stateI18n } from 'state-shared';

import { BOOK_AMOUNT_MULTIPLIER } from 'constants-shared/bet';
import { stateBet, stateUrlDerived } from 'state-shared';

const SOCIAL_SUFFIX: Record<string, string> = {
	XGC: 'GC',
	XSC: 'SC',
	XEC: 'SC',
};

const ZERO_DECIMAL = new Set([
	'BIF',
	'CLP',
	'DJF',
	'GNF',
	'JPY',
	'KMF',
	'KRW',
	'MGA',
	'PYG',
	'RWF',
	'UGX',
	'VND',
	'VUV',
	'XAF',
	'XOF',
	'XPF',
]);

const localeForLang = (lang: string) => {
	if (lang === 'br') return 'pt';
	if (lang === 'zz' || !lang) return 'en';
	return lang;
};

const currencyDigits = (currency: string) => {
	if (ZERO_DECIMAL.has(currency)) return 0;
	try {
		const digits = new Intl.NumberFormat('en', {
			style: 'currency',
			currency,
		}).resolvedOptions().maximumFractionDigits;
		return digits ?? 2;
	} catch {
		return 2;
	}
};

/** Keep sub-cent precision (up to 6 decimals) instead of rounding it away. Zero-decimal currencies stay whole. */
const fractionDigits = (value: number, currency: string) => {
	const base = currencyDigits(currency);
	if (base === 0 || !Number.isFinite(value)) return base;
	const abs = Math.abs(value);
	const fixed = abs.toFixed(6);
	const trimmed = fixed.replace(/0+$/, '').replace(/\.$/, '');
	const extra = trimmed.includes('.') ? trimmed.split('.')[1].length : 0;
	return Math.max(base, Math.min(6, extra));
};

export const bookEventAmountToBetAmountMultiplier = (bookEventAmount: number) =>
	bookEventAmount / BOOK_AMOUNT_MULTIPLIER;

export const bookEventAmountToNormalisedAmount = (bookEventAmount: number) => {
	const betAmountMultiplier = bookEventAmountToBetAmountMultiplier(bookEventAmount);
	return stateBet.wageredBetAmount * betAmountMultiplier;
};

export const numberToFloat = (value: number) => Number.parseFloat(`${value}`);

export const numberToCurrencyString = (value: number) => {
	const currency = stateBet.currency || 'USD';
	const lang = localeForLang(stateUrlDerived.lang());
	const digits = fractionDigits(value, currency);
	const suffix = SOCIAL_SUFFIX[currency];
	if (suffix) {
		const formatted = new Intl.NumberFormat(lang, {
			minimumFractionDigits: Math.min(2, digits),
			maximumFractionDigits: Math.max(2, digits),
		}).format(value);
		return `${formatted} ${suffix}`;
	}
	try {
		return new Intl.NumberFormat(lang, {
			style: 'currency',
			currency,
			minimumFractionDigits: currencyDigits(currency),
			maximumFractionDigits: digits,
		}).format(value);
	} catch {
		return `${value.toFixed(digits)} ${currency}`;
	}
};

export const bookEventAmountToCurrencyString = (bookEventAmount: number) => {
	const normalisedAmount = bookEventAmountToNormalisedAmount(bookEventAmount);
	return numberToCurrencyString(normalisedAmount);
};

void stateI18n;
