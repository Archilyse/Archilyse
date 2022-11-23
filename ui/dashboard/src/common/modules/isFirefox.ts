const currentWindow: any = window;
const isFirefox = () => typeof currentWindow.InstallTrigger !== 'undefined';

export default isFirefox;
