// @ts-ignore
import base from 'config-vite';

export default () => {
	const config = base();
	if (config.css) delete config.css.preprocessorOptions;
	return config;
};
